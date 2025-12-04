# -*- coding: utf-8 -*-
###############################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fouzan M(Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """ Inheriting res.config.settings to add default blocking credit limit """
    _inherit = 'res.config.settings'

    default_blocking_credit_limit = fields.Monetary(
        string="Default Blocking Credit Limit", readonly=False,
        inverse='_inverse_default_blocking_credit_limit',
        default_model='res.partner',
        compute='_compute_default_blocking_credit_limit',
        help="Cannot make sales once the selected customer is crossed blocking "
        "amount"
    )

    @api.depends('company_id')
    def _compute_default_blocking_credit_limit(self):
        """ Get default value for blocking limit in settings """
        for setting in self:
            setting.default_blocking_credit_limit = self.env['ir.property']. \
                _get('blocking_credit_limit', 'res.partner')

    def _inverse_default_blocking_credit_limit(self):
        """ Set default value for blocking limit """
        for setting in self:
            self.env['ir.property']._set_default(
                'blocking_credit_limit', 'res.partner',
                setting.default_blocking_credit_limit, self.company_id.id)

    @api.constrains('default_blocking_credit_limit')
    def validation_default_blocking_credit_limit(self):
        """ Validate default blocking credit limit and credit limit amount """
        if self.default_blocking_credit_limit < \
                self.account_default_credit_limit and \
                self.default_blocking_credit_limit != 0:
            raise ValidationError(
                _("Default Blocking Credit Limit must be greater than Default "
                  "Credit Limit"))
