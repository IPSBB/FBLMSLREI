# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_history_ids = fields.One2many("product.price.history", "product_tmpl_id")

    def action_view_price_history(self):

        record = self.env[self._context['active_model']].browse(self._context['active_id'])
        if record._name  == "product.template":
            domain = [('product_tmpl_id', '=', record.id)]
        elif record._name  == "product.product":
            domain = [('product_id', '=', record.id)]
        else:
            raise NotImplementedError

        return {
            'name': 'Price Changes',
            'type': 'ir.actions.act_window',
            'res_model': 'product.price.history',
            'view_mode': 'graph,tree',
            'domain': domain,
        }

    def update_price(self, data):
        history_obj = self.env['product.price.history']
        vals = {'price': data['price'], 'currency_id': data['currency_id']}

        domain = [('id', '=', -1)]
        if data['model'] == "product.template":
            vals['product_tmpl_id'] = data['id']
            domain = [('product_tmpl_id', '=', data['id'])]

        if data['model'] == "product.product":
            vals['product_id'] = data['id']
            domain = [('product_id', '=', data['id'])]

        history_obj.sudo().clear_history(domain)
        last_history = (lambda h: "NULL" if not h else h[-1])(history_obj.search(domain).sorted(lambda x: x.id))
        if not isinstance(last_history, str) and last_history.price == data['price']:
            return

        history_obj.create(vals)

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'list_price' in vals:
            self.update_price({'model': 'product.template', 'id': self.id, 'price': vals['list_price'], 'currency_id': self.currency_id.id})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductTemplate, self).create(vals_list)
        for product in res:
            self.update_price({'model': 'product.template', 'id': product.id, 'price': product.list_price, 'currency_id': product.currency_id.id})
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    price_history_ids = fields.One2many("product.price.history", "product_id")

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'list_price' in vals:
            if type(self.id) != int:
                return res
            self.env['product.template'].update_price({'model': 'product.product', 'id': self.id, 'price': vals['list_price'], 'currency_id': self.currency_id.id})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductProduct, self).create(vals_list)
        for product in res:
            self.env['product.template'].update_price({'model': 'product.product', 'id': product.id, 'price': product.list_price, 'currency_id': product.currency_id.id})
        return res
