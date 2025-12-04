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
from odoo import models
from odoo.tools import float_is_zero


class PosMakePayment(models.TransientModel):
    """Overriding partner for setting credit and debit included in POS"""
    _inherit = 'pos.make.payment'

    def check(self):
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        @param self: object pointer.
        """
        self.ensure_one()
        order = self.env['pos.order'].browse(self.env.context.get('active_id',
                                                                  False))
        currency = order.currency_id
        init_data = self.read()[0]
        if not float_is_zero(init_data['amount'],
                             precision_rounding=currency.rounding):
            if order.partner_id:
                order.partner_id.credit -= order._get_rounded_amount(
                    init_data['amount'])
            order.add_payment({
                'pos_order_id': order.id,
                'amount': order._get_rounded_amount(init_data['amount']),
                'name': init_data['payment_name'],
                'payment_method_id': init_data['payment_method_id'][0],
            })
        if order._is_pos_order_paid():
            order.action_pos_order_paid()
            order._create_order_picking()
            order._compute_total_cost_in_real_time()
            return {'type': 'ir.actions.act_window_close'}
        return self.launch_payment()
