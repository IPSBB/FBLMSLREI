from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    harmonized_code_id = fields.Many2one('import_fees.harmonized_code', compute='_compute_harmonized_code_id', store=True, readonly=False)
    split_method_landed_cost = fields.Selection(selection_add=[('by_hscode', 'By HS Code'), ],
                                                ondelete={'by_hscode': "cascade"},
                                                string="Default Split Method",
                                                help="Default Split Method when used for Landed Cost"
                                                )
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

class ProductProduct(models.Model):
    _inherit = "product.product"

    def search_harmonized_code_id(self):
        res = self.env["import_fees.harmonized_code"]
        if self:
            self.ensure_one()
            if self.harmonized_code_id:
                res = self.harmonized_code_id
            elif self.categ_id:
                res = self.categ_id.search_harmonized_code_id()
        return res


class ProductCategory(models.Model):
    _inherit = "product.category"
    harmonized_code_id = fields.Many2one('import_fees.harmonized_code')

    def search_harmonized_code_id(self):
        self.ensure_one()
        if self.harmonized_code_id:
            res = self.harmonized_code_id
        elif self.parent_id:
            res = self.parent_id.search_harmonized_code_id()
        else:
            res = self.env["import_fees.harmonized_code"]
        return res

