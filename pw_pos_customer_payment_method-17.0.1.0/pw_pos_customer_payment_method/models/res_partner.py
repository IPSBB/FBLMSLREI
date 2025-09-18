# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pw_pos_payment_ids = fields.Many2many('pos.payment.method', string="POS Payment Method")
