# -*- coding: utf-8 -*-

from odoo.addons.stock_landed_costs.tests.common import TestStockLandedCostsCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo import fields
from datetime import datetime, timedelta
import time
import logging

@tagged('post_install', '-at_install')
class ImportFeesTestLandedCostsNoCustomsBill(TestStockLandedCostsCommon):

    def setUp(self):
        super(ImportFeesTestLandedCostsNoCustomsBill, self).setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        
        # Enable EUR currency
        self.env.ref('base.EUR').active = True
        
        # Create product category with real-time inventory valuation
        self.categ = self.env['product.category'].create({
            'name': 'Test Category',
            'property_cost_method': 'average',
            'property_valuation': 'real_time',
        })
        
        # Create a product with landed cost enabled
        self.landed_cost_product = self.env['product.product'].create({
            'name': 'Shipping Cost',
            'type': 'service',
            'categ_id': self.categ.id,
            'landed_cost_ok': True,
            'split_method_landed_cost': 'equal',
        })
        
        # Create a regular product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',  # Changed from 'product' to 'consu' (consumable)
            'categ_id': self.categ.id,
            'standard_price': 100.0,
        })
        
        # Create a vendor
        self.vendor = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })
        
        # Create purchase order
        self.po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
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
        self.invoice = self.env['account.move'].browse(action['res_id'])
        
        # Post the invoice
        self.invoice.invoice_date = fields.Date.today()
        self.invoice.action_post()

    def test_calculate_customs_duties_no_customs_bill(self):
        """Test that clicking on calculate customs duties adds a cost line even when there is no customs bill."""
        # Create a landed cost
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, self.po.picking_ids[0].id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'vendor_bill_ids': [(4, self.invoice.id)],
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        # Calculate customs fees
        landed_cost.calc_customs_fees()

        # Check that a cost line has been added for customs duties
        customs_cost_line = landed_cost.cost_lines.filtered(
            lambda l: l.product_id == self.env.ref('import_fees.customs'))
        self.assertTrue(customs_cost_line, "No cost line has been added for customs duties")
