# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import api, fields, models
class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    wk_margin = fields.Float(compute='wk_product_margin', string="Line Margin" ,store=True)
    purchase_price = fields.Float(string='Cost')

    def _wk_compute_margin(self, pos_order, product_id):
        from_curr = self.env.user.company_id.currency_id
        to_curr = pos_order.pricelist_id.currency_id
        purchase_price = self.total_cost or product_id.standard_price
        ctx = self.env.context.copy()
        ctx['date'] = pos_order.date_order
        price = from_curr.with_context(ctx)._convert(purchase_price, to_curr, round=False)
        return price

    @api.model
    def _get_purchase_price(self, pricelist, product, product_uom, date):
        frm_cur = self.env.company.currency_id
        to_cur = pricelist.currency_id
        purchase_price = product.standard_price
        if product_uom != product.uom_id:
            purchase_price = product.uom_id._compute_price(purchase_price, product_uom)
        price = frm_cur._convert(
            purchase_price, to_cur,
            self.order_id.company_id or self.env.company,
            date or fields.Date.today(), round=False)
        return {'purchase_price': price}

    @api.onchange('product_id', 'product_uom')
    def product_id_change_margin(self):
        if not self.order_id.pricelist_id or not self.product_id or not self.product_uom:
            return
        self.purchase_price = self._wk_compute_margin(self.order_id, self.product_id, self.product_uom)

    def create(self, vals):
        result=super(PosOrderLine, self).create(vals)
        for order in vals:
            if 'purchase_price' not in vals:
                pos_order = self.env['pos.order'].browse(order['order_id'])
                product_id = self.env['product.product'].browse(order['product_id'])
                order['purchase_price'] = self._wk_compute_margin(pos_order, product_id)
        return result

    @api.depends('product_id', 'purchase_price', 'qty', 'price_unit', 'price_subtotal','total_cost')
    def wk_product_margin(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.total_cost
            margin = line.price_subtotal - price
            line.wk_margin = currency.round(margin) if currency else margin

class SaleOrder(models.Model):
    _inherit = "pos.order"

    wk_margin = fields.Float(compute='wk_product_margin', help="It gives profitability by calculating the difference between the Unit Price and the cost.", store=True)

    @api.depends('lines.wk_margin')
    def wk_product_margin(self):
        for order in self:
            order.wk_margin = sum(order.lines.mapped('wk_margin'))
