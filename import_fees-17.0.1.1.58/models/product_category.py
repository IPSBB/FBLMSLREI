from odoo import api, fields, models, _

#Override the product category model to add the harmonized code field and the allowed harmonized code ids field
class ProductCategory(models.Model):
    _inherit = "product.category"

    harmonized_code_id = fields.Many2one('import_fees.harmonized_code', string='Harmonized Code', company_dependent=True,
                                            domain="[('id', 'in', allowed_harmonized_code_ids)]")
    allowed_harmonized_code_ids = fields.Many2many('import_fees.harmonized_code', 
                                                   compute='_compute_allowed_harmonized_code_ids', 
                                                   store=False)


    @api.depends_context('company')
    def _compute_allowed_harmonized_code_ids(self):
        HarmonizedCode = self.env['import_fees.harmonized_code']
        for category in self:
            category.allowed_harmonized_code_ids = HarmonizedCode.get_harmonized_codes_for_company(self.env.company.id)

    @api.constrains('harmonized_code_id')
    def _check_harmonized_code_company(self):
        for record in self:
            if record.harmonized_code_id and (self.env.company):
                allowed_codes = self.env['import_fees.harmonized_code'].sudo().get_harmonized_codes_for_company(self.env.company.id)
                if record.harmonized_code_id not in allowed_codes:
                    raise ValidationError(_("The selected Harmonized Code is not allowed for the company %s.", self.env.company.name))                      


    def search_harmonized_code_id(self):
        self.ensure_one()
        if self.harmonized_code_id:
            res = self.harmonized_code_id
        elif self.parent_id:
            res = self.parent_id.search_harmonized_code_id()
        else:
            res = self.env["import_fees.harmonized_code"]
        return res

