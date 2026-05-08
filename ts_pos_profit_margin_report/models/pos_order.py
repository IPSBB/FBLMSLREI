from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'


class PosSession(models.Model):
    _inherit = 'pos.session'

