# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger
from odoo import fields


@tagged('post_install', '-at_install')
class TestCustomsBillsInvoice(TransactionCase):
    """Test that customs bills can be properly invoiced after receipt"""

    @classmethod
    def setUpClass(cls):
        super(TestCustomsBillsInvoice, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Get the service products
        cls.customs_product = cls.env.ref('import_fees.customs')
        cls.clearance_product = cls.env.ref('import_fees.clearance')
        cls.freight_product = cls.env.ref('import_fees.freight')
        
        # Create the customs broker partner
        cls.customs_broker = cls.env['res.partner'].create({
            'name': 'International Customs Brokers',
            'country_id': cls.env.ref('base.us').id,
            'city': 'New York',
            'street': '456 Trade Avenue',
            'zip': '10001',
            'phone': '+1 212-555-4321',
            'email': 'info@intlcustoms.com',
            'website': 'www.intlcustoms.com',
            'company_type': 'company',
            'supplier_rank': 1,
        })
        
        # Create a test purchase order for customs services
        cls.po = cls.env['purchase.order'].create({
            'name': 'TEST-PO-CUSTOMS',
            'partner_id': cls.customs_broker.id,
            'user_id': cls.env.ref('base.user_admin').id,
            'state': 'draft',
            'company_id': cls.env.ref('base.main_company').id,
            'currency_id': cls.env.ref('base.USD').id,
            'origin': 'TEST-PO',
            'order_line': [
                (0, 0, {
                    'name': 'Customs duties - Test Import',
                    'product_id': cls.customs_product.id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': 500.00,
                }),
                (0, 0, {
                    'name': 'Clearance - Test Import',
                    'product_id': cls.clearance_product.id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': 150.00,
                }),
                (0, 0, {
                    'name': 'Freight - Test Import',
                    'product_id': cls.freight_product.id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': 300.00,
                }),
            ]
        })

    @mute_logger('odoo.models.unlink')
    def test_customs_bill_invoice_creation(self):
        """Test that customs bills can be invoiced after receipt"""
        # Confirm the purchase order
        self.po.button_confirm()
        self.assertEqual(self.po.state, 'purchase', "Purchase order should be in 'purchase' state")
        
        # For service products, we need to manually mark them as received
        for line in self.po.order_line:
            line.qty_received = line.product_qty
        
        # Check if all products are marked as received
        received_qty = sum(line.qty_received for line in self.po.order_line)
        self.assertEqual(received_qty, 3, "All 3 service products should be marked as received")
        
        # Now try to create invoice - should succeed
        self.po.action_create_invoice()
        
        # Find the invoice associated with this purchase order
        invoice = self.env['account.move'].search([
            ('invoice_origin', '=', self.po.name),
            ('move_type', '=', 'in_invoice')
        ], limit=1)
        
        self.assertTrue(invoice, "Invoice should be created successfully")
        
        # Check invoice details
        self.assertEqual(float(invoice.amount_total), 950.00, "Invoice total should be 950.00")
        self.assertEqual(len(invoice.invoice_line_ids), 3, "Invoice should have 3 lines")
        
        # Set the invoice date (required for posting)
        invoice.invoice_date = fields.Date.today()
        
        # Post the invoice
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted', "Invoice should be in 'posted' state")
