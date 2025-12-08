from odoo import api, fields, models


class ReportPosMarginSellingProducts(models.AbstractModel):
    _name = 'report.egy_pos_margin_reports.report_margin_selling_products'
    _description = "Report for POS Products Margin"

    def get_margin_products_details(self, type=False, pos_session_id=False, start_date=False, end_date=False):
        if type == 'session':
            order_ids = self.env["pos.order"].search([
                ('session_id', '=', pos_session_id),
                ('state', 'in', ['paid', 'done', 'invoiced'])
            ])
        else:
            order_ids = self.env["pos.order"].search([
                ('date_order', '>=', start_date),
                ('date_order', '<=', end_date),
                ('state', 'in', ['paid', 'done', 'invoiced'])
            ])

        if order_ids:
            query = """
                SELECT 
                    product.id, 
                    template.name, 
                    uom.name AS uom, 
                    product.default_code AS code, 
                    product.barcode AS barcode, 
                    (product_tmpl_id.list_price->>'1')::NUMERIC AS cost,
                    line.price_unit AS price,
                    (line.price_unit - (product_tmpl_id.list_price->>'1')::NUMERIC) AS margin,
                    SUM((line.price_unit - (product_tmpl_id.list_price->>'1')::NUMERIC) * qty) AS total_margin,
                    SUM(qty) AS qty, 
                    SUM(line.price_subtotal_incl) AS total 
                FROM product_product AS product
                JOIN pos_order_line AS line ON product.id = line.product_id
                JOIN product_template AS template ON template.id = product.product_tmpl_id
                JOIN uom_uom AS uom ON uom.id = template.uom_id 
                WHERE line.order_id IN %s 
                GROUP BY product.id, template.name, product.default_code, 
                         uom.name, product.barcode, product_tmpl_id.list_price, 
                         template.list_price, line.price_unit
                ORDER BY SUM(qty) DESC
            """
            self.env.cr.execute(query, (tuple(order_ids.ids),))

        product_summary = self.env.cr.dictfetchall()

        # Calculate totals
        total_margin_sum = sum(
            product['total_margin'] for product in product_summary if product['total_margin'] is not None)
        total_quantity = sum(
            product['qty'] for product in product_summary if product['qty'] is not None)
        total_margin = sum(
            product['margin'] for product in product_summary if product['margin'] is not None)

        return {
            'products': product_summary,
            'total_margin_sum': total_margin_sum,
            'total_quantity': total_quantity,
            'total_margin': total_margin,
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date,
            'type': type,
            'pos_session_id': self.env['pos.session'].browse(pos_session_id) if pos_session_id else False
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values"""
        data = dict(data or {})
        data.update(
            self.get_margin_products_details(
                data.get('type'),
                data.get('pos_session_id'),
                data.get('start_date'),
                data.get('end_date')
            ))
        return data
