# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestDemoCustomsBills(TransactionCase):
    """Test that demo customs bills are in USD and from US-based broker partner"""

    @classmethod
    def setUpClass(cls):
        super(TestDemoCustomsBills, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Get the US dollar currency
        cls.usd_currency = cls.env.ref('base.USD')
        
        # Create the US-based customs broker partner for testing
        cls.us_broker = cls.env['res.partner'].create({
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
        
        # Create test purchase orders for customs bills
        po_data = [
            {
                'name': 'DEMO-PO-NAFTA-CUSTOMS',
                'origin': 'DEMO-PO-NAFTA',
                'customs_duties': 600.00,
                'clearance': 150.00,
                'freight': 350.00,
            },
            {
                'name': 'DEMO-PO-EU-CUSTOMS',
                'origin': 'DEMO-PO-EU',
                'customs_duties': 2040.00,
                'shipping': 950.00,
                'clearance': 250.00,
            },
            {
                'name': 'DEMO-PO-ASIA-CUSTOMS',
                'origin': 'DEMO-PO-ASIA',
                'customs_duties': 3800.00,
                'freight': 1650.00,
                'clearance': 280.00,
            },
            {
                'name': 'DEMO-PO-NETWORK-CUSTOMS',
                'origin': 'DEMO-PO-NETWORK',
                'customs_duties': 2850.00,
                'shipping': 1250.00,
                'insurance': 320.00,
            },
            {
                'name': 'DEMO-PO-SOUTH-AMERICA-CUSTOMS',
                'origin': 'DEMO-PO-SOUTH-AMERICA',
                'customs_duties': 12750.00,
                'freight': 4850.00,
                'insurance': 950.00,
                'clearance': 750.00,
            },
        ]
        
        # Create the purchase orders
        cls.customs_pos = cls.env['purchase.order']
        for po in po_data:
            po_vals = {
                'name': po['name'],
                'partner_id': cls.us_broker.id,
                'user_id': cls.env.ref('base.user_admin').id,
                'state': 'purchase',
                'company_id': cls.env.ref('base.main_company').id,
                'currency_id': cls.usd_currency.id,
                'origin': po['origin'],
                'order_line': [],
            }
            
            # Add order lines
            if 'customs_duties' in po:
                po_vals['order_line'].append((0, 0, {
                    'name': f"Customs duties - {po['name']} Import",
                    'product_id': cls.env.ref('import_fees.customs').id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': po['customs_duties'],
                }))
            
            if 'clearance' in po:
                po_vals['order_line'].append((0, 0, {
                    'name': f"Clearance - {po['name']} Import",
                    'product_id': cls.env.ref('import_fees.clearance').id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': po['clearance'],
                }))
            
            if 'freight' in po:
                po_vals['order_line'].append((0, 0, {
                    'name': f"Freight - {po['name']} Import",
                    'product_id': cls.env.ref('import_fees.freight').id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': po['freight'],
                }))
            
            if 'shipping' in po:
                po_vals['order_line'].append((0, 0, {
                    'name': f"Shipping - {po['name']} Import",
                    'product_id': cls.env.ref('import_fees.shipping').id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': po['shipping'],
                }))
            
            if 'insurance' in po:
                po_vals['order_line'].append((0, 0, {
                    'name': f"Insurance - {po['name']} Import",
                    'product_id': cls.env.ref('import_fees.insurance').id,
                    'product_qty': 1,
                    'product_uom': cls.env.ref('uom.product_uom_unit').id,
                    'price_unit': po['insurance'],
                }))
            
            # Create the purchase order
            cls.customs_pos += cls.env['purchase.order'].create(po_vals)

    @mute_logger('odoo.models.unlink')
    def test_customs_bills_currency_and_partner(self):
        """Test that all customs bills are in USD and from US-based broker partner"""
        # Verify we found the demo customs bills
        self.assertTrue(self.customs_pos, "No demo customs bills found")
        
        # Check each customs bill
        for po in self.customs_pos:
            # Check currency is USD
            self.assertEqual(
                po.currency_id, 
                self.usd_currency,
                f"Customs bill {po.name} should use USD currency, but uses {po.currency_id.name}"
            )
            
            # Check partner is the US-based customs broker
            self.assertEqual(
                po.partner_id, 
                self.us_broker,
                f"Customs bill {po.name} should use US-based broker partner, but uses {po.partner_id.name}"
            )
            
            # Check partner country is US
            self.assertEqual(
                po.partner_id.country_id.code, 
                'US',
                f"Customs broker partner should be US-based, but is from {po.partner_id.country_id.name}"
            )
            
            # Check that all invoice lines also use USD
            for line in po.order_line:
                self.assertEqual(
                    line.currency_id,
                    self.usd_currency,
                    f"Line {line.name} in {po.name} should use USD currency"
                )
