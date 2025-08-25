# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPriceHistory(models.Model):
    _name = 'product.price.history'
    _description = 'Product Price History'

    product_tmpl_id = fields.Many2one('product.template')
    product_id = fields.Many2one('product.product')
    price = fields.Float("Price")
    currency_id = fields.Many2one('res.currency', string="Currency")
    create_date_x = fields.Char("Date Changed")

    def clear_history(self, domain):
        records = self.search(domain)
        limit = 100
        if len(records) > limit:
            old_records = records.sorted(lambda x: x.id, reverse=True)[limit:]
            old_records.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductPriceHistory, self).create(vals_list)
        for history in res:
            d = history.create_date.strftime("%d-%b-%Y")
            same_day_histories = ((history.product_id or history.product_tmpl_id).price_history_ids.filtered(lambda h:h.create_date.date() == history.create_date.date()))
            if len(same_day_histories) > 1:
                d = history.create_date.strftime("%d-%b-%Y") + f"({len(same_day_histories)})"
            history.write({'create_date_x': d})
        return res


# Test Data
# from datetime import datetime, timedelta
# for day_count in range(1, 101):
#     current_date = datetime(2024, 2, 1, 15, 5, 17) + timedelta(days=day_count)
#     formatted_date = current_date.strftime('%Y-%m-%d %H:%M:%S')
#     import random
#     print(f"""
#     INSERT INTO product_price_history (product_tmpl_id, price, currency_id, create_date_x) VALUES (43, {random.randint(50, 75)}, 1, '{formatted_date}');
#     """.strip())
