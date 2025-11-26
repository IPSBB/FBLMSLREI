from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
    
class HarmonizedCode(models.Model):
    _name = 'import_fees.harmonized_code'
    _description = 'Harmonized System Code'
    _order = 'name asc'
    
    name = fields.Char('HS Code', required=True)
    description = fields.Char('Description', help="Description of the Harmonized System Code")
    company_ids = fields.Many2many('res.company', string='Companies')
    hs_codes_per_region_ids = fields.One2many(
        comodel_name="import_fees.harmonized_code_per_region"
        , inverse_name="harmonized_code_id"
        , string="HS Codes Per Country"
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super(HarmonizedCode, self).create(vals_list)
        for record in records:
            record._create_default_region_record()
        return records
    
    def _create_default_region_record(self):
        """Create a default HS code per region record with 'Default' region."""
        # Find or create the Default region
        default_region = self.env.ref('import_fees.region_default')
        
        # Check if a default region record already exists for this HS code
        existing_record = self.env['import_fees.harmonized_code_per_region'].search([
            ('harmonized_code_id', '=', self.id),
            ('region_id', '=', default_region.id)
        ], limit=1)
        
        if not existing_record:
            # Create the default region record with appropriate values
            self.env['import_fees.harmonized_code_per_region'].create({
                'harmonized_code_id': self.id,
                'region_id': default_region.id,
                'com_value': 0.0,
                'exm_value': 0.0,
                'cid_rate': 0.0,
                'surcharge_rate': 0.0,
                'pal_rate': 0.0,
                'eic_rate': 0.0,
                'cess_levy_rate': 0.0,
                'excise_duty_rate': 0.0,
                'ridl_rate': 0.0,
                'srl_rate': 0.0,
                'sscl_rate': 0.0,
                'vat_rate': 0.15,
            })
    product_category_count = fields.Integer(compute="_compute_product_category_count")
    product_template_count = fields.Integer(compute="_compute_product_template_count")
    
    def get_harmonized_codes_by_region(self, region_id):
        return self.hs_codes_per_region_ids.filtered(lambda hc: hc.region_id == region_id)
    
    product_category_ids = fields.One2many(
        comodel_name="product.category",
        inverse_name="harmonized_code_id",
        string="Product Categories",
        readonly=True,
    )
    product_template_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="harmonized_code_id",
        string="Products",
        readonly=True,
    )


    @api.model
    def get_harmonized_codes_for_company(self, company_id):
        result = self.search([
            '|', ('company_ids', '=', False),
            ('company_ids', 'in', [company_id])
        ])
        return result

    @api.constrains('name', 'company_ids')
    def _check_unique_name(self):
        for record in self:
            domain = [('name', '=', record.name)]
            if record.company_ids:
                domain += [('company_ids', 'in', record.company_ids.ids)]
            else:
                domain += [('company_ids', '=', False)]
            
            if record.id:
                domain += [('id', '!=', record.id)]
            
            if self.search_count(domain) > 0:
                raise ValidationError(
                    "The HS Code name must be unique for the selected companies "
                    "or globally if no company is selected."
                )



    @api.model
    def _default_company_id(self):
        return False

    @api.depends("product_category_ids")
    def _compute_product_category_count(self):
        for code in self:
            code.product_category_count = len(code.product_category_ids)

    @api.depends("product_template_ids")
    def _compute_product_template_count(self):
        for code in self:
            code.product_template_count = len(code.product_template_ids)

    @api.model
    def find_or_create(self, hs_code):
        harmonized_code = self.search([('name', '=', hs_code)], limit=1)
        if not harmonized_code:
            harmonized_code = self.create({'name': hs_code})
        return harmonized_code


class Region(models.Model):
    _name = 'import_fees.region'
    _description = 'Region'
    
    name = fields.Char('Name', required=True)
    country_ids = fields.Many2many('res.country', string='Countries')



class HarmonizedCodePerRegion(models.Model):
    _name = 'import_fees.harmonized_code_per_region'
    _description = 'Harmonized System Code Per Region'
    _sort = 'name asc'
    
    name = fields.Char('Name', compute='_compute_name', store=True)
    region_id = fields.Many2one('import_fees.region', string='Region', required=True)
    harmonized_code_id = fields.Many2one('import_fees.harmonized_code', string='HS Code', required=True)
    com_value = fields.Float('COM', required=True, default=0.0, help="Cost of Manufacture (fixed amount per hs code)")
    exm_value = fields.Float('EXM', required=True, default=0.0, help="Export Market Value (fixed amount per hs code)")
    cid_rate = fields.Float('CID', required=True, default=0.0, help="Customs Import Duty Rate")
    surcharge_rate = fields.Float('Surcharge', required=True, default=0.0, help="Surcharge Rate")
    pal_rate = fields.Float('PAL', required=True, default=0.0, help="Port Authority Levy Rate")
    eic_rate = fields.Float('EIC', required=True, default=0.0, help="Export Inspection Charge Rate")
    cess_levy_rate = fields.Float('Cess Levy', required=True, default=0.0, help="Cess Levy Rate")
    excise_duty_rate = fields.Float('Excise Duty', required=True, default=0.0, help="Excise Duty Rate")
    ridl_rate = fields.Float('RIDL', required=True, default=0.0, help="Road Infrastructure Development Levy Rate")
    srl_rate = fields.Float('SRL', required=True, default=0.0, help="Sugar Re-planting Levy Rate")
    sscl_rate = fields.Float('SSCL', required=True, default=0.0, help="Special Sales Tax on Cigarettes and Liquor Rate")
    vat_rate = fields.Float('VAT', required=True, default=0.15, help="Value Added Tax Rate")
    is_com_visible = fields.Boolean('COM Visible', compute='_compute_com_visible', store=False)
    is_exm_visible = fields.Boolean('EXM Visible', compute='_compute_exm_visible', store=False)
    is_cid_visible = fields.Boolean('CID Visible', compute='_compute_cid_visible', store=False)
    is_surcharge_visible = fields.Boolean('Surcharge Visible', compute='_compute_surcharge_visible', store=False)
    is_pal_visible = fields.Boolean('PAL Visible', compute='_compute_pal_visible', store=False)
    is_eic_visible = fields.Boolean('EIC Visible', compute='_compute_eic_visible', store=False)
    is_cess_levy_visible = fields.Boolean('Cess Levy Visible', compute='_compute_cess_levy_visible', store=False)
    is_excise_duty_visible = fields.Boolean('Excise Duty Visible', compute='_compute_excise_duty_visible', store=False)
    is_ridl_visible = fields.Boolean('RIDL Visible', compute='_compute_ridl_visible', store=False)
    is_srl_visible = fields.Boolean('SRL Visible', compute='_compute_srl_visible', store=False)
    is_sscl_visible = fields.Boolean('SSCL Visible', compute='_compute_sscl_visible', store=False)
    is_vat_visible = fields.Boolean('VAT Visible', compute='_compute_vat_visible', store=False)

    @api.depends('harmonized_code_id', 'region_id.name')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.harmonized_code_id.name} / {record.region_id.name}"
        
    def _compute_com_visible(self):
        for code in self:
            code.is_com_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.com_visible', False)

    def _compute_exm_visible(self):
        for code in self:
            code.is_exm_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.exm_visible', False)

    def _compute_cid_visible(self):
        for code in self:
            code.is_cid_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.cid_visible', False)

    def _compute_surcharge_visible(self):
        for code in self:
            code.is_surcharge_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.surcharge_visible', False)

    def _compute_pal_visible(self):
        for code in self:
            code.is_pal_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.pal_visible', False)

    def _compute_eic_visible(self):
        for code in self:
            code.is_eic_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.eic_visible', False)

    def _compute_cess_levy_visible(self):
        for code in self:
            code.is_cess_levy_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.cess_levy_visible', False)

    def _compute_excise_duty_visible(self):
        for code in self:
            code.is_excise_duty_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.excise_duty_visible', False)

    def _compute_ridl_visible(self):
        for code in self:
            code.is_ridl_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.ridl_visible', False)

    def _compute_srl_visible(self):
        for code in self:
            code.is_srl_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.srl_visible', False)

    def _compute_sscl_visible(self):
        for code in self:
            code.is_sscl_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.sscl_visible', False)

    def _compute_vat_visible(self):
        for code in self:
            code.is_vat_visible = self.env['ir.config_parameter'].sudo().get_param('import_fees.vat_visible', False)
