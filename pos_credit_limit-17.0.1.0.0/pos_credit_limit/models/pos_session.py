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


class PosSession(models.Model):
    """Loading custom fields in PoS Session model"""
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        """
        This function loads the parameters of res.partner in the session.
        ----------------------------------------
        @param self: object pointer
        @return result: params of res.partner model
        """
        result = super(PosSession, self)._loader_params_res_partner()
        append_fields = ['blocking_credit_limit', 'credit', 'credit_limit',
                         'show_credit_limit', 'parent_id',
                         'use_partner_credit_limit', 'partner_block_credit']
        result['search_params']['fields'].extend(append_fields)
        return result
