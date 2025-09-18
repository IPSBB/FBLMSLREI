# -*- coding: utf-8 -*-
from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pw_restrict_pm = fields.Boolean(string="Restrict Payment Methods")
    pw_payment_method_ids = fields.Many2many('pos.payment.method', 'pos_payment_method_rel_config', 'pm_id', 'config_id', string='Default Payment Method')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pw_restrict_pm = fields.Boolean(related='pos_config_id.pw_restrict_pm', readonly=False)
    pw_payment_method_ids = fields.Many2many(related='pos_config_id.pw_payment_method_ids', readonly=False)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        result = super(PosSession, self)._loader_params_res_partner()
        result['search_params']['fields'].append('pw_pos_payment_ids')
        return result
