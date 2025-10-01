from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ReceivedProductLine(models.Model):
    _name = 'import_fees.received.product.line'
    _description = 'Received Product Line'
    # ==== Business fields ====
    landed_costs_id = fields.Many2one('stock.landed.cost', 'Landed Cost')
    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True)
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill', compute='_compute_vendor_bill_id', store=True)
    quantity = fields.Float(string='Quantity',
                            default=1.0, digits=(14, 4))
    price_unit = fields.Monetary(string='Unit Price', store=True, readonly=True,
                                 currency_field='currency_id')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
                                  currency_field='currency_id')
    local_price_total = fields.Monetary(string='Local Currency Total', store=True, readonly=True,
                                        currency_field='local_currency_id')
    currency_id = fields.Many2one('res.currency', string='Vendor Currency', required=True)
    currency_rate = fields.Float('Currency Rate', related='currency_id.rate', readonly=True)
    local_currency_id = fields.Many2one(related='landed_costs_id.currency_id', string='Local Currency', readonly=True,
                                        store=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', readonly=True)
    hs_code_id = fields.Many2one('import_fees.harmonized_code_per_region', string="HS Code", store=True, readonly=True,
                                 compute='_compute_hscode')
    is_domestic = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International')
    ], string="Origin", store=True, readonly=True, compute='_compute_is_domestic',
       help="Indicates if the vendor is from the same country as the company")
    vendor_country_id = fields.Many2one('res.country', string="Vendor Country", store=True, readonly=True, 
                                       compute='_compute_vendor_country')
    
    @api.depends('move_id')
    def _compute_vendor_bill_id(self):
        for line in self:
            if line.move_id and line.move_id.purchase_line_id:
                # Get the purchase order
                purchase_order = line.move_id.purchase_line_id.order_id
                # Get the vendor bills associated with this purchase order
                vendor_bills = purchase_order.invoice_ids.filtered(lambda x: x.move_type == 'in_invoice')
                if vendor_bills:
                    line.vendor_bill_id = vendor_bills[0]
                else:
                    line.vendor_bill_id = False
            else:
                line.vendor_bill_id = False
                                       
    @api.depends('move_id')
    def _compute_vendor_country(self):
        for elm in self:
            vendor_country = False
            if elm.move_id and elm.move_id.purchase_line_id and elm.move_id.purchase_line_id.order_id.partner_id.country_id:
                vendor_country = elm.move_id.purchase_line_id.order_id.partner_id.country_id
            elm.vendor_country_id = vendor_country
    
    @api.depends('vendor_country_id')
    def _compute_is_domestic(self):
        for elm in self:
            company_country = elm.env.company.country_id
            if elm.vendor_country_id and company_country == elm.vendor_country_id:
                elm.is_domestic = 'domestic'
            else:
                elm.is_domestic = 'international'

    @api.depends('product_id', 'move_id','vendor_country_id')
    def _compute_hscode(self):
        _logger = logging.getLogger(__name__)
        for elm in self:
            global_hs_code_id = elm.product_id.search_harmonized_code_id()
            _logger.info(f"Product: {elm.product_id.name}, Global HS code: {global_hs_code_id and global_hs_code_id.name or 'None'}")
            
            if global_hs_code_id and elm.is_domestic == 'international':
                default_hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].search([
                    ('harmonized_code_id', '=', global_hs_code_id.id),
                    ('region_id', '=', self.env.ref('import_fees.region_default').id)
                ], limit=1)          
                vendor_country = elm.vendor_country_id     
                # If vendor has a country and it's the same as the company country, set hs_code_id to False
                # This ensures no customs duties are applied for domestic vendors
                if vendor_country:
                    # Default to the default region
                    default_region = self.env.ref('import_fees.region_default')
                    region_to_use = default_region
                    
                    # Find all regions that include the vendor's country
                    regions_with_country = self.env['import_fees.region'].search([
                        ('country_ids', 'in', vendor_country.id)
                    ], limit=1)
                    if not regions_with_country:
                        regions_with_country = default_region
                        
                    # Find the harmonized_code_per_region record for this hs_code and the selected region
                    hs_code_per_region = self.env['import_fees.harmonized_code_per_region'].search([
                        ('harmonized_code_id', '=', global_hs_code_id.id),
                        ('region_id', '=', regions_with_country.id)
                    ], limit=1)
                    
                    _logger.info(f"Searching for HS code per region with harmonized_code_id={global_hs_code_id.id}, region_id={region_to_use.id}")
                    _logger.info(f"Found HS code per region: {hs_code_per_region and hs_code_per_region.name or 'None'}")
                    
                    if hs_code_per_region:
                        elm.hs_code_id = hs_code_per_region
                        _logger.info(f"Set HS code to {hs_code_per_region.name}")
                if not elm.hs_code_id:
                    elm.hs_code_id = default_hs_code_per_region
                    _logger.info(f"No vendor country found, setting to default region HS code")
            else:
                elm.hs_code_id = False
                _logger.info(f"No HS code to be applied")
