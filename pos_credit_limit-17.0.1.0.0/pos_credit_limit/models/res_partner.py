# -*- coding: utf-8 -*-
###############################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fouzan M (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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


class ResPartner(models.Model):
    """Overriding partner for setting credit and debit included in POS"""
    _inherit = 'res.partner'

    blocking_credit_limit = fields.Float(
        company_dependent=True, copy=False, readonly=False, store= True,
        groups='account.group_account_invoice,account.group_account_readonly',
        help="Cannot make sales once the selected customer is crossed blocking "
             "amount. Set it to 0 to disable the feature")
    partner_block_credit = fields.Boolean(
        groups='account.group_account_invoice,account.group_account_readonly',
        string="Partner Blocking Limit",
        help="option to select custom block credit limit",
        compute='_compute_partner_block_credit', store= True,
        inverse='_inverse_partner_block_credit')

    @api.depends_context('company')
    def _compute_partner_block_credit(self):
        """ Set custom partner credit limit option based on default blocking
        limit and partner credit limit """
        for partner in self:
            company_limit = self.env['ir.property']._get(
                'blocking_credit_limit', 'res.partner')
            partner.partner_block_credit = partner.blocking_credit_limit != \
                                           company_limit

    def _inverse_partner_block_credit(self):
        """ Get custom partner credit limit value """
        for partner in self:
            if not partner.partner_block_credit:
                partner.blocking_credit_limit = self.env['ir.property']._get(
                    'blocking_credit_limit', 'res.partner')

    @api.model
    def _commercial_fields(self):
        """ Overrides base method to include 'blocking_credit_limit'. and it
        returns extended list of commercial fields."""
        return super()._commercial_fields() + \
            ['blocking_credit_limit']

    @api.constrains('blocking_credit_limit', 'credit_limit')
    def validation_blocking_limit(self):
        """to validate blocking credit limit"""
        for partner in self:
            if partner.credit_limit > partner.blocking_credit_limit != 0:
                raise ValidationError(
                    _("Blocking Credit Limit must be greater than Credit Limit "
                      "or set Blocking Credit Limit as 0"))

    @api.depends_context('force_company', 'pos_order_ids.state')
    def _credit_debit_get(self):
        """
        This function helps to calculate the total credit of customer
        including pos payments.
        ----------------------------------------
        @param self: object pointer
        """
        super()._credit_debit_get()
        pos_order = self.pos_order_ids.filtered(
            lambda x: x.partner_id and x.company_id == self.env.company and
                      x.partner_id.use_partner_credit_limit or
                      x.partner_id.partner_block_credit
        )
        for order in pos_order:
            credit_payment = order.payment_ids.filtered_domain(
                [('payment_method_id.journal_id', '=', '')])
            for amount in credit_payment:
                order.partner_id.credit += amount.amount
