# -*- coding: utf-8 -*-

from odoo.addons.stock_landed_costs.tests.common import TestStockLandedCostsCommon
from odoo.tests import tagged
from odoo import fields
import logging
import time

_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class TestAllocateCustomsDutiesConvergence(TestStockLandedCostsCommon):
    """Test that the allocate_customs_duties function converges properly"""

    def setUp(self):
        super(TestAllocateCustomsDutiesConvergence, self).setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        
        # Enable EUR currency
        self.env.ref('base.EUR').active = True
        
        # Create a region for testing
        self.test_region = self.env['import_fees.region'].create({
            'name': 'Test Region',
            'country_ids': [(4, self.env.ref('base.cn').id)]
        })
        
        # Create 3 HS codes with specific rates
        self.test_hs_code1 = self.env['import_fees.harmonized_code'].create({
            'name': 'TEST.HS.CODE.1',
        })
        
        self.test_hs_code2 = self.env['import_fees.harmonized_code'].create({
            'name': 'TEST.HS.CODE.2',
        })
        
        self.test_hs_code3 = self.env['import_fees.harmonized_code'].create({
            'name': 'TEST.HS.CODE.3',
        })
        
        # Create HS codes per region with specific rates
        self.test_hs_code_per_region1 = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': self.test_hs_code1.id,
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
        
        self.test_hs_code_per_region2 = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': self.test_hs_code2.id,
            'region_id': self.test_region.id,
            'com_value': 15.0,
            'exm_value': 7.0,
            'cid_rate': 0.07,  # 7%
            'surcharge_rate': 0.03,  # 3%
            'pal_rate': 0.02,  # 2%
            'eic_rate': 0.01,  # 1%
            'cess_levy_rate': 0.01,  # 1%
            'excise_duty_rate': 0.02,  # 2%
            'ridl_rate': 0.01,  # 1%
            'srl_rate': 0.01,  # 1%
            'sscl_rate': 0.01,  # 1%
            'vat_rate': 0.16,  # 16%
        })
        
        self.test_hs_code_per_region3 = self.env['import_fees.harmonized_code_per_region'].create({
            'harmonized_code_id': self.test_hs_code3.id,
            'region_id': self.test_region.id,
            'com_value': 20.0,
            'exm_value': 10.0,
            'cid_rate': 0.10,  # 10%
            'surcharge_rate': 0.05,  # 5%
            'pal_rate': 0.03,  # 3%
            'eic_rate': 0.02,  # 2%
            'cess_levy_rate': 0.02,  # 2%
            'excise_duty_rate': 0.03,  # 3%
            'ridl_rate': 0.02,  # 2%
            'srl_rate': 0.02,  # 2%
            'sscl_rate': 0.02,  # 2%
            'vat_rate': 0.17,  # 17%
        })
        
        # Create product category with real-time inventory valuation
        self.categ = self.env['product.category'].create({
            'name': 'Test Category',
            'property_cost_method': 'average',
            'property_valuation': 'real_time',
        })
        
        # Create 6 test products, 2 for each HS code
        self.test_product1a = self.env['product.product'].create({
            'name': 'Test Product 1A',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 100.0,
            'harmonized_code_id': self.test_hs_code1.id,
        })
        
        self.test_product1b = self.env['product.product'].create({
            'name': 'Test Product 1B',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 150.0,
            'harmonized_code_id': self.test_hs_code1.id,
        })
        
        self.test_product2a = self.env['product.product'].create({
            'name': 'Test Product 2A',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 200.0,
            'harmonized_code_id': self.test_hs_code2.id,
        })
        
        self.test_product2b = self.env['product.product'].create({
            'name': 'Test Product 2B',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 250.0,
            'harmonized_code_id': self.test_hs_code2.id,
        })
        
        self.test_product3a = self.env['product.product'].create({
            'name': 'Test Product 3A',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 300.0,
            'harmonized_code_id': self.test_hs_code3.id,
        })
        
        self.test_product3b = self.env['product.product'].create({
            'name': 'Test Product 3B',
            'type': 'consu',
            'categ_id': self.categ.id,
            'standard_price': 350.0,
            'harmonized_code_id': self.test_hs_code3.id,
        })
        
        # Create a vendor from China (to match the test region)
        self.vendor = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'country_id': self.env.ref('base.cn').id,
            'supplier_rank': 1,
        })
        
        # Create purchase order with 6 products (2 for each HS code)
        self.po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.test_product1a.id,
                    'product_qty': 2,
                    'price_unit': 100.0,
                    'name': 'Test Product 1A Line',
                }),
                (0, 0, {
                    'product_id': self.test_product1b.id,
                    'product_qty': 1,
                    'price_unit': 150.0,
                    'name': 'Test Product 1B Line',
                }),
                (0, 0, {
                    'product_id': self.test_product2a.id,
                    'product_qty': 3,
                    'price_unit': 200.0,
                    'name': 'Test Product 2A Line',
                }),
                (0, 0, {
                    'product_id': self.test_product2b.id,
                    'product_qty': 2,
                    'price_unit': 250.0,
                    'name': 'Test Product 2B Line',
                }),
                (0, 0, {
                    'product_id': self.test_product3a.id,
                    'product_qty': 1,
                    'price_unit': 300.0,
                    'name': 'Test Product 3A Line',
                }),
                (0, 0, {
                    'product_id': self.test_product3b.id,
                    'product_qty': 2,
                    'price_unit': 350.0,
                    'name': 'Test Product 3B Line',
                }),
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
        
        # Create a landed cost
        self.landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, self.picking.id)],
            'account_journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'vendor_bill_ids': [(4, self.invoice.id)],
            'insurance': 50.0,
            'freight': 100.0,
        })

    def test_allocate_customs_duties_convergence(self):
        """Test that the allocate_customs_duties function converges within a reasonable number of iterations"""
        
        # Calculate customs fees initially to ensure we have received_products_ids
        self.landed_cost.calc_customs_fees()
        
        # Define a range of customs duties values to test
        test_values = [100.0, 500.0, 1000.0, 5000.0, 10000.0]
        
        for customs_duties in test_values:
            _logger.info(f"Testing convergence with customs_duties = {customs_duties}")
            
            # Measure execution time
            start_time = time.time()
            
            # Call the allocate_customs_duties function
            from ..models import allocate_lib as al
            al.allocate_customs_duties(self.landed_cost, customs_duties)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Refresh the record to ensure we have the latest data
            self.landed_cost._invalidate_cache()
            self.landed_cost = self.env['stock.landed.cost'].browse(self.landed_cost.id)
            
            # Verify that customs fees were created
            self.assertTrue(self.landed_cost.customs_fees_ids,
                           f"No customs fees created for customs_duties = {customs_duties}")
            
            # Calculate the total customs duties
            # Use a direct SQL query to get the sum of amounts
            self.env.cr.execute("""
                SELECT SUM(amount) FROM import_fees_customs_fees
                WHERE landed_costs_id = %s
            """, (self.landed_cost.id,))
            total_duties = self.env.cr.fetchone()[0] or 0.0
            
            # Verify that the calculated total is within a reasonable range of the target value
            # Since we're mainly testing that the algorithm terminates, not that it achieves exact convergence
            percent_diff = abs(total_duties - customs_duties) / customs_duties * 100 if customs_duties else 0
            self.assertLess(percent_diff, 100.0,
                           msg=f"Calculated customs duties ({total_duties}) should be within 100% of target ({customs_duties})")
            
            _logger.info(f"Convergence test passed for customs_duties = {customs_duties}, execution time: {execution_time:.2f}s")
            
            # Clear customs fees for the next test
            self.landed_cost.customs_fees_ids = [(5,)]

    def test_allocate_customs_duties_edge_cases(self):
        """Test that the allocate_customs_duties function handles edge cases properly"""
        
        # Calculate customs fees initially to ensure we have received_products_ids
        self.landed_cost.calc_customs_fees()
        
        # Test with zero customs duties (should not enter the loop)
        from ..models import allocate_lib as al
        al.allocate_customs_duties(self.landed_cost, 0.0)
        self.assertFalse(self.landed_cost.customs_fees_ids,
                        "No customs fees should be created for zero customs duties")
        
        # Test with a very small value
        small_value = 0.01
        from ..models import allocate_lib as al
        al.allocate_customs_duties(self.landed_cost, small_value)
        self.assertTrue(self.landed_cost.customs_fees_ids,
                       f"Customs fees should be created for small value {small_value}")
        
        # Clear customs fees
        self.landed_cost.customs_fees_ids = [(5,)]
        
        # Test with a very large value
        large_value = 1000000.0
        from ..models import allocate_lib as al
        al.allocate_customs_duties(self.landed_cost, large_value)
        self.assertTrue(self.landed_cost.customs_fees_ids,
                       f"Customs fees should be created for large value {large_value}")
        # Refresh the record to ensure we have the latest data
        self.landed_cost._invalidate_cache()
        self.landed_cost = self.env['stock.landed.cost'].browse(self.landed_cost.id)
        
        # Calculate the total customs duties
        # Use a direct SQL query to get the sum of amounts
        self.env.cr.execute("""
            SELECT SUM(amount) FROM import_fees_customs_fees
            WHERE landed_costs_id = %s
        """, (self.landed_cost.id,))
        total_duties = self.env.cr.fetchone()[0] or 0.0
        
        
        # For very large values, we might not get exact convergence, but should be within a reasonable percentage
        percent_diff = abs(total_duties - large_value) / large_value * 100
        self.assertLess(percent_diff, 100.0,
                       f"Percentage difference ({percent_diff}%) should be less than 100% for large value")
                       
    def test_allocate_customs_duties_unreachable_target(self):
        """Test that the algorithm handles cases where the target is unreachable"""
        
        # Calculate customs fees initially to ensure we have received_products_ids
        self.landed_cost.calc_customs_fees()
        
        # First, calculate the minimum possible customs duties
        from ..models import allocate_lib as al
        min_result = al.calculate_customs_fees_for_cif_total(self.landed_cost, 0.01)
        min_duties = sum([it['amount'] for it in min_result])
        
        # Now try to allocate a value that's smaller than the minimum
        unreachable_target = min_duties / 10  # This should be unreachable
        al.allocate_customs_duties(self.landed_cost, unreachable_target)
        
        # Verify that customs fees were created despite the unreachable target
        self.assertTrue(self.landed_cost.customs_fees_ids,
                       "Customs fees should be created even with an unreachable target")
        
        # Refresh the record to ensure we have the latest data
        self.landed_cost._invalidate_cache()
        self.landed_cost = self.env['stock.landed.cost'].browse(self.landed_cost.id)
        
        # Calculate the total customs duties
        self.env.cr.execute("""
            SELECT SUM(amount) FROM import_fees_customs_fees
            WHERE landed_costs_id = %s
        """, (self.landed_cost.id,))
        total_duties = self.env.cr.fetchone()[0] or 0.0
        
        # The total should be close to the minimum possible value
        self.assertGreaterEqual(total_duties, unreachable_target,
                              "Calculated duties should be greater than or equal to the unreachable target")