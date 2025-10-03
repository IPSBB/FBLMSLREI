from odoo import api, fields, models, _ 

# Overriding the product template to add the Harmonized Code field, the allowed Harmonized Codes 
# for the company and the split method for landed cost
class ProductTemplate(models.Model):
    _inherit = "product.template"
    harmonized_code_id = fields.Many2one('import_fees.harmonized_code', string='Harmonized Code', 
                                         domain="[('id', 'in', allowed_harmonized_code_ids)]", company_dependent=True)
    allowed_harmonized_code_ids = fields.Many2many('import_fees.harmonized_code', 
                                                   compute='_compute_allowed_harmonized_code_ids', 
                                                   store=False)
    split_method_landed_cost = fields.Selection(selection_add=[('by_hscode', 'By HS Code'), ],
                                                ondelete={'by_hscode': "cascade"},
                                                string="Default Split Method",
                                                help="Default Split Method when used for Landed Cost"
                                                )

    @api.depends_context('company')
    def _compute_allowed_harmonized_code_ids(self):
        HarmonizedCode = self.env['import_fees.harmonized_code']
        for product in self:
            product.allowed_harmonized_code_ids = HarmonizedCode.get_harmonized_codes_for_company(self.env.company.id if self.env.company else False)

    @api.constrains('harmonized_code_id', 'company_id')
    def _check_harmonized_code_company(self):
        for record in self:
            if record.harmonized_code_id and (record.company_id):
                allowed_codes = self.env['import_fees.harmonized_code'].sudo().get_harmonized_codes_for_company(record.company_id.id)
                if record.harmonized_code_id not in allowed_codes:
                    raise ValidationError(_("The selected Harmonized Code is not allowed for the company %s.", record.company_id.name))                      

    @api.depends('categ_id')
    def _compute_harmonized_code_id(self):
        for record in self:
            record.harmonized_code_id = record.search_harmonized_code_id()

    def search_harmonized_code_id(self):
        res = self.env["import_fees.harmonized_code"]
        if self:
            self.ensure_one()
            if self.harmonized_code_id:
                res = self.harmonized_code_id
            elif self.categ_id:
                res = self.categ_id.search_harmonized_code_id()
        return res
