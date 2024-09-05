# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class pos_order(models.Model):
    _inherit = "pos.order"

    pw_signature = fields.Binary(string="Signature")

    def _order_fields(self, ui_order):
        res = super(pos_order, self)._order_fields(ui_order)
        res.update({
            'pw_signature': ui_order.get('pw_signature')[1] if ui_order.get('pw_signature') else False,
        })
        return res
