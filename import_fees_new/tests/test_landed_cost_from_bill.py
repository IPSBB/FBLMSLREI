# -*- coding: utf-8 -*-
from odoo.addons.stock_landed_costs.tests.common import TestStockLandedCostsCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from odoo import fields
from datetime import datetime, timedelta
import time
import logging
from odoo import fields

@tagged('post_install', '-at_install')
class TestLandedCostFromBill(TestStockLandedCostsCommon):
    """
    This test specifically reproduces the bug where creating landed costs from a vendor bill
    results in a ValueError: "Invalid field 'origin_vendor_bill_id' on model 'stock.landed.cost.lines'"
    """

    def setUp(self):
        super(TestLandedCostFromBill, self).setUp()
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
        
        # Add landed cost product to the invoice
        self.invoice.write({
            'invoice_line_ids': [(0, 0, {
                'product_id': self.landed_cost_product.id,
                'name': 'Shipping Cost',
                'quantity': 1,
                'price_unit': 50.0,
                'is_landed_costs_line': True,
            })]
        })
        
        # Post the invoice
        self.invoice.invoice_date = fields.Date.today()
        self.invoice.action_post()

    def test_create_landed_costs_from_bill(self):
        """Test creating landed costs from vendor bill with the button_create_landed_costs method."""
        # This should create a landed cost record from the vendor bill
        result = self.invoice.button_create_landed_costs()
        
        # If the bug is fixed, we should be able to get the landed cost record
        landed_cost_id = result.get('res_id')
        self.assertTrue(landed_cost_id, "Landed cost should be created")
        
        landed_cost = self.env['stock.landed.cost'].browse(landed_cost_id)
        self.assertEqual(landed_cost.vendor_bill_ids[0].id, self.invoice.id, 
                         "Landed cost should reference the original vendor bill")
        
