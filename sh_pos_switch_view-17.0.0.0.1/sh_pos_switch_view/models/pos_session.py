# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_product(self):
        res = super()._loader_params_product_product()
        if res.get('search_params'):
            if res.get('search_params').get('fields'):
                res.get('search_params').get('fields').extend(['type','qty_available','virtual_available'])
        return res
