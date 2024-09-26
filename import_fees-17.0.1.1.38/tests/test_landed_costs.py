# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from datetime import datetime
import time


@tagged('post_install', '-at_install')
class TestLandedCosts(TransactionCase):

    def setUp(self):
        super(TestLandedCosts, self).setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self.env.company.country_id = self.env.ref('base.lk')
        self.env.company.currency_id = self.env.ref('base.LKR')

        self.product_data = [
            ('5320-24T-8XE', 4, 1163.82, '8517.62.90'),
            ('5320-24P-8XE', 4, 1565.09, '8517.62.90'),
            ('5320-48T-8XE', 4, 1484.12, '8517.62.90'),
            ('5320-24T-8XE', 3, 1141.00, '8517.62.90'),
            ('5420F-16MW-32P-4XE', 2, 4126.98, '8517.62.90'),
            ('AP510C-WR', 20, 455.50, '8517.62.10'),
            ('XN-ACPWR', 1, 645.40, '8504.40.90'),
            ('<UNKNOWN>', 2, 53.10, '8504.40.90'),
        ]

        self.products = {}
        for name, qty, price, hs_code in self.product_data:
            product = self.env['product.product'].create({
                'name': name,
                'type': 'product',
                'categ_id': self.env.ref('product.product_category_all').id,
                'standard_price': price,
            })
            harmonized_code = self.env['import_fees.harmonized_code'].create({
                'name': hs_code,
                'code': hs_code,
            })
            product.write({'harmonized_code_id': harmonized_code.id})
            self.products[name] = {'product': product, 'qty': qty, 'price': price}

        self.vendor = self.env['res.partner'].create({
            'name': 'EXTREME',
            'supplier_rank': 1,
        })

        self.po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.products[name]['product'].id,
                    'product_qty': self.products[name]['qty'],
                    'price_unit': self.products[name]['price'],
                }) for name in self.products
            ],
            'currency_id': self.env.ref('base.USD').id,
        })

        self.env['res.currency.rate'].create({
            'name': '2024-09-23',
            'rate': 1.0 / 313.15,
            'currency_id': self.env.ref('base.USD').id,
            'company_id': self.env.company.id,
        })

    def test_landed_cost_creation(self):
        self.po.button_confirm()
        picking = self.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking.button_validate()

        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees_and_open()

        self.assertAlmostEqual(landed_cost.declared_value, 38459.14, 2, "Incorrect declared value")
        self.assertAlmostEqual(landed_cost.customs_value, 1583256.99, 2, "Incorrect total duty")
        self.assertAlmostEqual(landed_cost.customs_vat_value, 2666597.00, 2, "Incorrect customs VAT")
        self.assertAlmostEqual(landed_cost.total_customs_value, 4249853.99, 2, "Incorrect total customs value")

        customs_duties = landed_cost.customs_fees_ids
        expected_duties = [
            {'hs_code': '8504.40.90', 'rate': 910.24, 'value': 751.60, 'amount': 6841.33, 'cif_value': 751.60, 'com_value': 83.33, 'exm_value': 100.00, 'pal_value': 0.00, 'sscl_value': 6658.00, 'vat_value': 47934.00},
            {'hs_code': '8517.62.10', 'rate': 4189.29, 'value': 9110.00, 'amount': 381644.33, 'cif_value': 9110.00, 'com_value': 83.33, 'exm_value': 100.00, 'pal_value': 293431.00, 'sscl_value': 88030.00, 'vat_value': 633810.00},
            {'hs_code': '8517.62.90', 'rate': 4177.88, 'value': 28597.54, 'amount': 1194771.33, 'cif_value': 28597.54, 'com_value': 83.33, 'exm_value': 100.00, 'pal_value': 918914.00, 'sscl_value': 275674.00, 'vat_value': 1984853.00},
        ]

        for duty, expected in zip(customs_duties, expected_duties):
            for field, value in expected.items():
                self.assertAlmostEqual(duty[field], value, 2, f"Incorrect {field} for HS Code {duty.harmonized_code_id.code}")

        landed_cost.compute_landed_cost()
        landed_cost.button_validate()

        expected_costs = {
            'Bank Charges': 126153.86,
            'Clearance': 27553.50,
            'Freight': 190260.58,
            'Customs duties': 1583256.99,
        }

        for cost_line in landed_cost.cost_lines:
            self.assertAlmostEqual(cost_line.price_unit, expected_costs[cost_line.product_id.name], 2,
                                   f"Incorrect cost for {cost_line.product_id.name}")

        for valuation in landed_cost.valuation_adjustment_lines:
            product = valuation.product_id
            total_valuation = sum(line.additional_landed_cost for line in landed_cost.valuation_adjustment_lines if line.product_id == product)
            cost_line_total = sum(line.price_unit for line in landed_cost.cost_lines if line.product_id == product)
            self.assertAlmostEqual(total_valuation, cost_line_total, 2,
                                   f"Mismatch between valuation and cost line for product {product.name}")

    def test_hs_code_application(self):
        for product_data in self.product_data:
            product_name, _, _, expected_hs_code = product_data
            product = self.products[product_name]['product']
            self.assertEqual(product.harmonized_code_id.code, expected_hs_code,
                             f"Incorrect HS Code for product {product_name}")

    def test_custom_split_method(self):
        self.po.button_confirm()
        picking = self.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking.button_validate()

        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees_and_open()
        
        # Set split method to 'by_hscode' for customs duties
        customs_cost_line = landed_cost.cost_lines.filtered(lambda l: l.product_id == self.env.ref('import_fees.customs'))
        customs_cost_line.write({'split_method': 'by_hscode'})

        landed_cost.compute_landed_cost()

        # Check if costs are distributed correctly based on HS codes
        hs_code_costs = {}
        for valuation in landed_cost.valuation_adjustment_lines:
            if valuation.cost_line_id == customs_cost_line:
                hs_code = valuation.product_id.harmonized_code_id.code
                hs_code_costs[hs_code] = hs_code_costs.get(hs_code, 0) + valuation.additional_landed_cost

        # Assert that products with the same HS code have similar cost distributions
        for hs_code, total_cost in hs_code_costs.items():
            products = self.env['product.product'].search([('harmonized_code_id.code', '=', hs_code)])
            for product in products:
                product_cost = sum(line.additional_landed_cost for line in landed_cost.valuation_adjustment_lines 
                                   if line.product_id == product and line.cost_line_id == customs_cost_line)
                self.assertAlmostEqual(product_cost / total_cost, 1 / len(products), 2,
                                       f"Incorrect cost distribution for product {product.name} with HS code {hs_code}")

    def test_recalculate_wizard(self):
        self.po.button_confirm()
        picking = self.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking.button_validate()

        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees_and_open()
        
        initial_customs_value = landed_cost.customs_value
        
        # Modify a value to trigger recalculation
        landed_cost.freight = 200000.00
        
        wizard = self.env['import_fees.recalculate.wizard'].create({
            'landed_cost_id': landed_cost.id,
        })
        wizard.action_recalculate()
        
        self.assertNotEqual(initial_customs_value, landed_cost.customs_value, 
                            "Customs value should change after recalculation")

    def test_create_landed_bill(self):
        self.po.button_confirm()
        picking = self.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking.button_validate()

        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees_and_open()
        landed_cost.compute_landed_cost()
        landed_cost.button_validate()

        # Create landed cost bill
        result = landed_cost.button_create_landed_bill()
        
        self.assertEqual(result['type'], 'ir.actions.act_window', "Should return an action to open the created bill")
        self.assertEqual(result['res_model'], 'account.move', "Should create an account move")
        
        bill = self.env['account.move'].browse(result['res_id'])
        self.assertTrue(bill, "Landed cost bill should be created")
        self.assertEqual(bill.move_type, 'in_invoice', "Created bill should be a vendor bill")
        self.assertEqual(bill.invoice_origin, landed_cost.name, "Bill should reference the landed cost")

    def test_error_handling(self):
        # Test creating landed cost without picking
        with self.assertRaises(UserError):
            self.env['stock.landed.cost'].create({
                'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                'bank': 126153.86,
                'clearance': 27553.50,
                'freight': 190260.58,
            }).calc_customs_fees_and_open()

        # Test negative values
        self.po.button_confirm()
        picking = self.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking.button_validate()

        with self.assertRaises(ValidationError):
            self.env['stock.landed.cost'].create({
                'picking_ids': [(4, picking.id)],
                'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                'bank': -126153.86,
                'clearance': 27553.50,
                'freight': 190260.58,
            })

    def test_currency_conversion(self):
        self.po.button_confirm()
        picking = self.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking.button_validate()

        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees_and_open()

        # Check if the currency conversion is correct
        total_usd = sum(line.price_unit * line.product_qty for line in self.po.order_line)
        expected_lkr = total_usd * 313.15  # Using the exchange rate we set up

        self.assertAlmostEqual(landed_cost.amount_local_currency, expected_lkr, 2,
                               "Incorrect currency conversion from USD to LKR")

    # Add more test methods as needed

if __name__ == '__main__':
    from odoo.tests.common import tagged
    from odoo.tests import runner
    runner.run_tests(['test_landed_costs'])
