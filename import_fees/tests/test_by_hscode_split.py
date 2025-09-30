# -*- coding: utf-8 -*-

from odoo.addons.stock_landed_costs.tests.common import TestStockLandedCostsCommon
from odoo.tests import tagged
from odoo import fields
import logging

_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class TestByHscodeSplit(TestStockLandedCostsCommon):
    """Test customs duties valuation when using by_hscode split method"""

    def setUp(self):
        super(TestByHscodeSplit, self).setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        
        # Enable EUR currency
        self.env.ref('base.EUR').active = True
        
        # Create a region for testing
        self.test_region = self.env['import_fees.region'].create({
            'name': 'Test Region',
            'country_ids': [(4, self.env.ref('base.cn').id)]
        })
        
        # Create HS code with specific rates
        self.test_hs_code = self.env['import_fees.harmonized_code'].create({
            'name': 'TEST.HS.CODE',
        })
        
        # Create HS code per region with specific rates
        self.test_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': self.test_hs_code.id,
            'region_id': self.test_region.id,
            'com_value': 10.0,
            'exm_value': 5.0,
            'cid_rate': 0.05,  # 5%
            'surcharge_rate': 0.02,  # 2%
            'pal_rate': 0.01,  # 1%
            'eic_rate': 0.0,
            'cess_levy_rate': 0.0,
            'excise_duty_rate': 0.0,
            'ridl_rate': 0.0,
            'srl_rate': 0.0,
            'sscl_rate': 0.0,
            'vat_rate': 0.15,  # 15%
        })
        
        # Create product category with real-time inventory valuation
        self.categ = self.env['product.category'].create({
            'name': 'Test Category',
            'property_cost_method': 'average',
            'property_valuation': 'real_time',
        })
        
        # Create a test product with the test HS code
        self.test_product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 100.0,
            'harmonized_code_id': self.test_hs_code.id,
        })
        
        # Create a vendor from China (to match the test region)
        self.vendor = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'country_id': self.env.ref('base.cn').id,
            'supplier_rank': 1,
        })
        
        # Create purchase order
        self.po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.test_product.id,
                    'product_qty': 5,
                    'price_unit': 100.0,
                    'name': 'Test Product Line',
                })
            ],
            'currency_id': self.env.ref('base.EUR').id,
        })
        self.po.button_confirm()
        
        # Receive the products
        self.picking = self.po.picking_ids[0]
        self.picking.action_confirm()
        self.picking.action_assign()
        for move_line in self.picking.move_line_ids:
            move_line.quantity = move_line.quantity_product_uom
        self.picking.button_validate()
        
        # Create vendor bill
        action = self.po.action_create_invoice()
        self.invoice = self.env['account.move'].browse(int(action['res_id']))
        
        # Post the invoice
        self.invoice.invoice_date = fields.Date.today()
        self.invoice.action_post()

    def test_by_hscode_split_valuation(self):
        """Test that customs duties are properly allocated when using by_hscode split method"""
        
        # Create a landed cost
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, self.picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'vendor_bill_ids': [(4, self.invoice.id)],
            'insurance': 50.0,
            'freight': 100.0,
        })
        
        # Calculate customs fees
        landed_cost.calc_customs_fees()
        
        # Verify customs fees were calculated
        customs_fees = landed_cost.customs_fees_ids.filtered(
            lambda f: f.harmonized_code_id.harmonized_code_id == self.test_hs_code
        )
        self.assertTrue(customs_fees, "No customs fees found for test product")
        self.assertGreater(customs_fees.amount, 0, "Customs fees amount should be greater than zero")
        
        # Compute landed cost
        landed_cost.compute_landed_cost()
        
        # Find the customs cost line
        customs_product = self.env.ref('import_fees.customs')
        customs_cost_line = landed_cost.cost_lines.filtered(
            lambda l: l.product_id.id == customs_product.id and "(Calculated)" in l.name
        )
        self.assertTrue(customs_cost_line, "No customs cost line found")
        self.assertEqual(customs_cost_line.split_method, 'by_hscode', "Customs cost line split method should be 'by_hscode'")
        
        # Find the valuation adjustment lines for the test product
        valuation_lines = landed_cost.valuation_adjustment_lines.filtered(
            lambda l: l.product_id == self.test_product and l.cost_line_id == customs_cost_line
        )
        self.assertTrue(valuation_lines, "No valuation adjustment lines found for test product")
        
        # Verify that the additional landed cost is greater than zero
        for line in valuation_lines:
            self.assertGreater(line.additional_landed_cost, 0, 
                              "Additional landed cost should be greater than zero for by_hscode split method")
        
        # We don't need to validate the landed cost for this test
        # The important part is that the valuation lines have the correct values
