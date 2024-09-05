# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pw_enable_signature = fields.Boolean(string="Allow Signature")
    pw_print_signature = fields.Boolean(string="Print Signature")

    @api.onchange('pw_enable_signature')
    def _onchange_pw_enable_signature(self):
        if not self.pw_enable_signature:
            self.pw_print_signature = False


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pw_enable_signature = fields.Boolean(related='pos_config_id.pw_enable_signature', readonly=False)
    pw_print_signature = fields.Boolean(related='pos_config_id.pw_print_signature', readonly=False)

    @api.onchange('pw_enable_signature')
    def _onchange_pw_enable_signature(self):
        if not self.pw_enable_signature:
            self.pw_print_signature = False
