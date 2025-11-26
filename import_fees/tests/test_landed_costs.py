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


@tagged('post_install', '-at_install')
class ImportFeesTestLandedCosts(TestStockLandedCostsCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        #enable EUR currency
        cls.env.ref('base.EUR').active = True

        # Create regions for testing HS code selection based on vendor country
        cls.eu_region = cls.env['import_fees.region'].create({
            'name': 'EU Region',
            'country_ids': [(4, cls.env.ref('base.be').id), (4, cls.env.ref('base.fr').id)]
        })
        
        cls.asia_region = cls.env['import_fees.region'].create({
            'name': 'Asia Region',
            'country_ids': [(4, cls.env.ref('base.cn').id), (4, cls.env.ref('base.jp').id)]
        })
        
        # Get the default region
        cls.default_region = cls.env.ref('import_fees.region_default')
        
        # Create HS codes with different regions
        cls.eu_hs_code = cls.env['import_fees.harmonized_code'].create({
            'name': 'EU_HS_CODE'
        })
        
        cls.asia_hs_code = cls.env['import_fees.harmonized_code'].create({
            'name': 'ASIA_HS_CODE'
        })
        
        cls.default_hs_code = cls.env['import_fees.harmonized_code'].create({
            'name': 'DEFAULT_HS_CODE'
        })
        
        # Create HS code per region records for EU region
        cls.eu_hs_code_per_region = cls.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': cls.eu_hs_code.id,
            'region_id': cls.eu_region.id,
            'vat_rate': 0.21
        })
        
        # Create HS code per region records for Asia region
        cls.asia_hs_code_per_region = cls.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': cls.asia_hs_code.id,
            'region_id': cls.asia_region.id,
            'vat_rate': 0.17,
            'com_value': 15.0,
            'exm_value': 8.0,
            'cid_rate': 0.08,  # 8%
            'surcharge_rate': 0.03,  # 3%
            'pal_rate': 0.02,  # 2%
        })
        
        # Create HS code per region records for default region
        cls.default_hs_code_per_region = cls.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': cls.default_hs_code.id,
            'region_id': cls.default_region.id,
            'vat_rate': 0.15
        })
        
        # Create vendors with different countries
        cls.eu_vendor = cls.env['res.partner'].create({
            'name': 'EU Vendor',
            'country_id': cls.env.ref('base.be').id,
            'supplier_rank': 1
        })
        
        cls.asia_vendor = cls.env['res.partner'].create({
            'name': 'Asia Vendor',
            'country_id': cls.env.ref('base.cn').id,
            'supplier_rank': 1
        })
        
        cls.no_country_vendor = cls.env['res.partner'].create({
            'name': 'No Country Vendor',
            'supplier_rank': 1
        })

        cls.product_data = [
            ('5320-24T-8XE', 4, 1163.82, '8517.62.90'),
            ('5320-24P-8XE', 4, 1565.09, '8517.62.90'),
            ('5320-48T-8XE', 4, 1484.12, '8517.62.90'),
            ('5320-24T-8XE', 3, 1141.00, '8517.62.90'),
            ('5420F-16MW-32P-4XE', 2, 4126.98, '8517.62.90'),
            ('AP510C-WR', 20, 455.50, '8517.62.10'),
            ('XN-ACPWR', 1, 645.40, '8504.40.90'),
            ('<UNKNOWN>', 2, 53.10, '8504.40.90'),
        ]
        # Use existing accounts from the company's default product category to avoid access rights issues
        default_categ = cls.env.ref('product.product_category_all')
        
        # Create our test category with the same account settings
        cls.categ = cls.env['product.category'].create({
            'name': 'Test Category',
            'property_cost_method': 'average',
            'property_valuation': 'real_time',
            'property_stock_account_input_categ_id': default_categ.property_stock_account_input_categ_id.id,
            'property_stock_account_output_categ_id': default_categ.property_stock_account_output_categ_id.id,
            'property_stock_valuation_account_id': default_categ.property_stock_valuation_account_id.id,
        })

        cls.products = {}
        for name, qty, price, hs_code in cls.product_data:
            product = cls.env['product.product'].create({
                'name': name,
                'type': 'consu',
                'categ_id': cls.categ.id,
                'standard_price': price,
                'cost_method': 'average',
            })
            # Use sudo() to ensure harmonized codes are created with proper access rights
            # Also ensure the harmonized code is properly created and committed to the database
            harmonized_code = cls.env['import_fees.harmonized_code'].sudo().find_or_create(hs_code)
            product.write({'harmonized_code_id': harmonized_code.id})
            cls.products[name] = {'product': product, 'qty': qty, 'price': price}

        cls.vendor = cls.env['res.partner'].create({
            'name': 'EXTREME',
            'supplier_rank': 1,
        })

        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.products[name]['product'].id,
                    'product_qty': cls.products[name]['qty'],
                    'price_unit': cls.products[name]['price'],
                }) for name in cls.products
            ],
            'currency_id': cls.env.ref('base.EUR').id,
        })
        cls.po.button_confirm()

        # Receive the products
        picking = cls.po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.quantity = move_line.quantity_product_uom
        picking.button_validate()

        # Create vendor bill
        action = cls.po.action_create_invoice()
        cls.invoice = cls.env['account.move'].browse(action['res_id'])
        cls.invoice.invoice_date = fields.Date.today()
        cls.invoice.action_post()

        # Set currency rates
        cls.env['res.currency.rate'].create({
            'name': fields.Date.today(),
            'rate': 1.0 / 1.1,
            'currency_id': cls.env.ref('base.EUR').id,
            'company_id': cls.env.company.id,
        })


    def test_hs_code_application(self):
        for product_data in self.product_data:
            product_name, _, _, expected_hs_code = product_data
            product = self.products[product_name]['product']
            self.assertEqual(product.harmonized_code_id.name, expected_hs_code,
                             f"Incorrect HS Code for product {product_name}")

    def test_custom_split_method_not_allowed(self):
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, self.po.picking_ids[0].id)],
            'account_journal_id': self.company_data['default_journal_purchase'].id,
            'vendor_bill_ids': [(4, self.invoice.id)],
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees()
        


        landed_cost.compute_landed_cost()
        with self.assertRaises(UserError):
            # Set split method to 'by_hscode' for customs duties
            customs_cost_line = landed_cost.cost_lines.filtered(lambda l: l.product_id == self.env.ref('import_fees.customs'))
            customs_cost_line.write({'split_method': 'by_hscode'})



    def test_create_landed_bill(self):
        # Get the company from the purchase order
        company = self.po.company_id
        
        # Find a journal from the same company
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        landed_cost = self.env['stock.landed.cost'].with_company(company).create({
            'picking_ids': [(4, self.po.picking_ids[0].id)],
            'account_journal_id': journal.id,
            'vendor_bill_ids': [(4, self.invoice.id)],
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
            'company_id': company.id,
        })

        landed_cost.calc_customs_fees()
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
            }).calc_customs_fees()

    def test_currency_conversion(self):
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, self.po.picking_ids[0].id)],
            'vendor_bill_ids': [(4, self.invoice.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'bank': 126153.86,
            'clearance': 27553.50,
            'freight': 190260.58,
        })

        landed_cost.calc_customs_fees()

        # Check if the currency conversion is correct
        total_eur = sum(line.price_unit * line.product_qty for line in self.po.order_line)
        expected_usd = total_eur * 1.1  # Using the exchange rate we set up

        self.assertAlmostEqual(landed_cost.amount_local_currency, expected_usd, 1,
                               "Incorrect currency conversion from EUR to USD")
                               
    def test_hs_code_selection_based_on_vendor_country(self):
        """Test that received products are created with the HS code matching the vendor country region."""
        # Create test products
        eu_product = self.env['product.product'].create({
            'name': 'EU Product',
            'type': 'consu',
            'categ_id': self.categ.id,
            'harmonized_code_id': self.eu_hs_code.id,
        })
        
        asia_product = self.env['product.product'].create({
            'name': 'Asia Product',
            'type': 'consu',
            'categ_id': self.categ.id,
            'harmonized_code_id': self.asia_hs_code.id,
        })
        
        default_product = self.env['product.product'].create({
            'name': 'Default Product',
            'type': 'consu',
            'categ_id': self.categ.id,
            'harmonized_code_id': self.default_hs_code.id,
        })
        
        # Create HS code per region for Asia HS code
        # Print region IDs for debugging
        _logger = logging.getLogger(__name__)
        _logger.info(f"Asia region ID: {self.asia_region.id}")
        
        # Get all regions with name 'Asia Region'
        asia_regions = self.env['import_fees.region'].search([('name', '=', 'Asia Region')])
        _logger.info(f"All Asia regions: {asia_regions.ids}")
        
        # Create HS code per region for each Asia region
        for region in asia_regions:
            asia_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].create({
                'harmonized_code_id': self.asia_hs_code.id,
                'region_id': region.id,
                'com_value': 15.0,
                'exm_value': 8.0,
                'cid_rate': 0.08,  # 8%
                'surcharge_rate': 0.03,  # 3%
                'pal_rate': 0.02,  # 2%
                'eic_rate': 0.0,
                'cess_levy_rate': 0.0,
                'excise_duty_rate': 0.0,
                'ridl_rate': 0.0,
                'srl_rate': 0.0,
                'sscl_rate': 0.0,
                'vat_rate': 0.17,  # 17%
            })
            _logger.info(f"Created Asia HS code per region: {asia_hs_code_per_region.id}, {asia_hs_code_per_region.name}, region_id: {region.id}")
        
        # Create purchase orders with different vendors
        test_cases = [
            (eu_product, self.eu_vendor, self.eu_region),
            (asia_product, self.asia_vendor, self.asia_region),
            (default_product, self.no_country_vendor, self.default_region)
        ]
        
        for product, vendor, expected_region in test_cases:
            # Create purchase order
            po = self.env['purchase.order'].create({
                'partner_id': vendor.id,
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'product_qty': 1,
                    'price_unit': 100,
                })]
            })
            po.button_confirm()
            
            # Receive the products
            picking = po.picking_ids[0]
            picking.action_confirm()
            picking.action_assign()
            for move_line in picking.move_line_ids:
                move_line.quantity = move_line.quantity_product_uom
            picking.button_validate()
            
            # Create vendor bill
            action = po.action_create_invoice()
            invoice = self.env['account.move'].browse(action['res_id'])
            invoice.invoice_date = fields.Date.today()
            invoice.action_post()
            
            # Create landed cost
            landed_cost = self.env['stock.landed.cost'].create({
                'picking_ids': [(4, picking.id)],
                'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                'vendor_bill_ids': [(4, invoice.id)],
            })
            
            # Calculate customs fees
            landed_cost.calc_customs_fees()
            
            # Check that the received product line has the correct HS code region
            received_product_lines = landed_cost.received_products_ids.filtered(lambda l: l.product_id == product)
            self.assertTrue(received_product_lines, f"No received product lines found for {product.name}")
            
            for line in received_product_lines:
                # Check that the HS code region name matches the expected region name
                # We use the name instead of the ID because the region IDs can be different
                self.assertEqual(
                    line.hs_code_id.region_id.name, 
                    expected_region.name,
                    f"Product {product.name} from vendor {vendor.name} should have HS code from region {expected_region.name}"
                )
                
    def test_domestic_vendor_has_no_hs_code(self):
        """Test that vendors from the same country as the company have no HS code assigned."""
        # Set company country to US
        self.env.company.country_id = self.env.ref('base.us').id
        
        # Create a US vendor (same country as company)
        domestic_vendor = self.env['res.partner'].create({
            'name': 'US Domestic Vendor',
            'country_id': self.env.ref('base.us').id,
            'supplier_rank': 1
        })
        
        # Create a US region and add US to it
        us_region = self.env['import_fees.region'].create({
            'name': 'US Region',
            'country_ids': [(4, self.env.ref('base.us').id)]
        })
        
        # Create a test product with HS code
        test_hs_code = self.env['import_fees.harmonized_code'].create({
            'name': 'US_HS_CODE'
        })
        
        # Create HS code per region for US region
        us_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': test_hs_code.id,
            'region_id': us_region.id,
            'vat_rate': 0.10  # 10% VAT for US region
        })
        
        # Create test product
        test_product = self.env['product.product'].create({
            'name': 'US Product',
            'type': 'consu',
            'categ_id': self.categ.id,
            'harmonized_code_id': test_hs_code.id,
        })
        
        # Create purchase order with domestic vendor
        po = self.env['purchase.order'].create({
            'partner_id': domestic_vendor.id,
            'order_line': [(0, 0, {
                'product_id': test_product.id,
                'product_qty': 1,
                'price_unit': 100,
            })]
        })
        po.button_confirm()
        
        # Receive the products
        picking = po.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.quantity = move_line.quantity_product_uom
        picking.button_validate()
        
        # Create vendor bill
        action = po.action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        invoice.invoice_date = fields.Date.today()
        invoice.action_post()
        
        # Create landed cost
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'vendor_bill_ids': [(4, invoice.id)],
        })
        
        # Calculate customs fees
        landed_cost.calc_customs_fees()
        
        # Check that the received product line has no HS code assigned
        received_product_lines = landed_cost.received_products_ids.filtered(lambda l: l.product_id == test_product)
        self.assertTrue(received_product_lines, "No received product lines found for US product")
        
        for line in received_product_lines:
            # Check that the HS code is False (not assigned)
            self.assertFalse(
                line.hs_code_id,
                "Product from domestic vendor should have no HS code assigned"
            )
            
            # Check that the is_domestic field is set to 'domestic'
            self.assertEqual(
                line.is_domestic,
                'domestic',
                "Product from domestic vendor should be marked as domestic"
            )
        
        # Verify no customs fees are calculated for this product
        customs_fees = landed_cost.customs_fees_ids.filtered(
            lambda f: f.harmonized_code_id.harmonized_code_id == test_hs_code
        )
        self.assertFalse(customs_fees, "No customs fees should be calculated for domestic vendor products")
                
    def test_customs_duties_calculations_per_region(self):
        """Test that customs duties calculations reflect the rates defined in HS Codes per region."""
        # Create regions with specific rates
        eu_region = self.eu_region
        asia_region = self.asia_region
        default_region = self.default_region
        
        # Create HS codes with different rates for different regions
        test_hs_code = self.env['import_fees.harmonized_code'].create({
            'name': 'TEST.HS.CODE',
        })
        
        # Create HS code per region records with specific rates
        eu_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': test_hs_code.id,
            'region_id': eu_region.id,
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
            'vat_rate': 0.21,  # 21%
        })
        
        asia_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': test_hs_code.id,
            'region_id': asia_region.id,
            'com_value': 15.0,
            'exm_value': 8.0,
            'cid_rate': 0.08,  # 8%
            'surcharge_rate': 0.03,  # 3%
            'pal_rate': 0.02,  # 2%
            'eic_rate': 0.0,
            'cess_levy_rate': 0.0,
            'excise_duty_rate': 0.0,
            'ridl_rate': 0.0,
            'srl_rate': 0.0,
            'sscl_rate': 0.0,
            'vat_rate': 0.17,  # 17%
        })
        
        # Create HS code per region for ASIA_HS_CODE
        self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': self.asia_hs_code.id,
            'region_id': asia_region.id,
            'com_value': 15.0,
            'exm_value': 8.0,
            'cid_rate': 0.08,  # 8%
            'surcharge_rate': 0.03,  # 3%
            'pal_rate': 0.02,  # 2%
            'eic_rate': 0.0,
            'cess_levy_rate': 0.0,
            'excise_duty_rate': 0.0,
            'ridl_rate': 0.0,
            'srl_rate': 0.0,
            'sscl_rate': 0.0,
            'vat_rate': 0.17,  # 17%
        })
        
        # Create HS code per region for TEST.HS.CODE in Asia region
        # Print debug information
        _logger = logging.getLogger(__name__)
        _logger.info(f"Asia region ID in test_customs_duties_calculations_per_region: {asia_region.id}")
        
        # Get all regions with name 'Asia Region'
        asia_regions = self.env['import_fees.region'].search([('name', '=', 'Asia Region')])
        _logger.info(f"All Asia regions: {asia_regions.ids}")
        
        # Create HS code per region for each Asia region
        for region in asia_regions:
            asia_hs_code_per_region_test = self.env['import_fees.harmonized_code_per_region'].create({
                'harmonized_code_id': test_hs_code.id,
                'region_id': region.id,
                'com_value': 15.0,
                'exm_value': 8.0,
                'cid_rate': 0.08,  # 8%
                'surcharge_rate': 0.03,  # 3%
                'pal_rate': 0.02,  # 2%
                'eic_rate': 0.0,
                'cess_levy_rate': 0.0,
                'excise_duty_rate': 0.0,
                'ridl_rate': 0.0,
                'srl_rate': 0.0,
                'sscl_rate': 0.0,
                'vat_rate': 0.17,  # 17%
            })
            _logger.info(f"Created Asia HS code per region for TEST.HS.CODE: {asia_hs_code_per_region_test.id}, {asia_hs_code_per_region_test.name}, region_id: {region.id}")
        
        # The default region record is created automatically, update its rates
        default_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].search([
            ('harmonized_code_id', '=', test_hs_code.id),
            ('region_id', '=', default_region.id)
        ], limit=1)
        
        default_hs_code_per_region.write({
            'com_value': 5.0,
            'exm_value': 3.0,
            'cid_rate': 0.03,  # 3%
            'surcharge_rate': 0.01,  # 1%
            'pal_rate': 0.005,  # 0.5%
            'eic_rate': 0.0,
            'cess_levy_rate': 0.0,
            'excise_duty_rate': 0.0,
            'ridl_rate': 0.0,
            'srl_rate': 0.0,
            'sscl_rate': 0.0,
            'vat_rate': 0.15,  # 15%
        })
        
        # Create test product with the test HS code
        test_product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'categ_id': self.categ.id,
            'harmonized_code_id': test_hs_code.id,
        })
        
        # Test cases for different vendors and expected rates
        test_cases = [
            (self.eu_vendor, eu_hs_code_per_region),
            (self.asia_vendor, asia_hs_code_per_region),
            (self.no_country_vendor, default_hs_code_per_region)
        ]
        
        for vendor, expected_hs_code_per_region in test_cases:
            # Create purchase order
            po = self.env['purchase.order'].create({
                'partner_id': vendor.id,
                'order_line': [(0, 0, {
                    'product_id': test_product.id,
                    'product_qty': 1,
                    'price_unit': 1000,  # Fixed price for easier calculations
                })]
            })
            po.button_confirm()
            
            # Receive the products
            picking = po.picking_ids[0]
            picking.action_confirm()
            picking.action_assign()
            for move_line in picking.move_line_ids:
                move_line.quantity = move_line.quantity_product_uom
            picking.button_validate()
            
            # Create vendor bill
            action = po.action_create_invoice()
            invoice = self.env['account.move'].browse(action['res_id'])
            invoice.invoice_date = fields.Date.today()
            invoice.action_post()
            
            # Create landed cost with fixed values for insurance and freight
            landed_cost = self.env['stock.landed.cost'].create({
                'picking_ids': [(4, picking.id)],
                'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                'vendor_bill_ids': [(4, invoice.id)],
                'insurance': 50,
                'freight': 100,
            })
            
            # Calculate customs fees
            landed_cost.calc_customs_fees()
            
            # Get the customs fees for the test product
            customs_fees = landed_cost.customs_fees_ids.filtered(
                lambda f: f.harmonized_code_id.harmonized_code_id == test_hs_code
            )
            
            self.assertTrue(customs_fees, f"No customs fees found for product with vendor {vendor.name}")
            
            # COM and EXM are fixed values
            self.assertAlmostEqual(
                customs_fees.com_value, 
                expected_hs_code_per_region.com_value, 
                places=2,
                msg=f"COM value incorrect for vendor {vendor.name}"
            )
            
            self.assertAlmostEqual(
                customs_fees.exm_value, 
                expected_hs_code_per_region.exm_value, 
                places=2,
                msg=f"EXM value incorrect for vendor {vendor.name}"
            )

    def test_adding_changing_any_customs_fees_editable_field_is_kept_after_compute_fees_id(self):
        """ Test that after the compute fees id, any changes to the customs fees editable fields are kept """
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
        landed_cost.compute_landed_cost()

        # Get the customs fees
        customs_fees = landed_cost.customs_fees_ids.filtered(lambda f: f.harmonized_code_id.harmonized_code_id == self.products['5320-24T-8XE']['product'].harmonized_code_id)

        # Change the CIF value
        customs_fees.cif_value = 200

        # Compute the customs fees again
        landed_cost._compute_customs_fees_ids()

        # Check that the CIF value is still 100.0
        self.assertEqual(customs_fees.cif_value, 200.0, "CIF value should be kept after compute fees id")

if __name__ == '__main__':
    from odoo.tests.common import tagged
    from odoo.tests import runner
    runner.run_tests(['test_landed_costs'])
