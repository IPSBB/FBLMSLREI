from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

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


