from odoo import models, fields


class TSPosReport(models.TransientModel):
    _name = 'ts.pos.report'

    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    partner_ids = fields.Many2many('res.partner', string='Customers')
    product_ids = fields.Many2many('product.product', string='Products')
    pos_order_id = fields.Many2one('pos.order', string="Pos Order")
    company_id = fields.Many2one('res.company', string="Company")
    location_id = fields.Many2one('stock.location', string="Location")
    product_type = fields.Selection([
        ("consu", "Consumable"),
        ("service", "Service"),
        ("product", "Storable Product"),
    ])

    def generate_pos_report(self):
        data = {
            # 'report_type': self.report_type,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'product_ids': self.product_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'pos_order_id': self.pos_order_id.id,
            'company_id': self.company_id.id,
            'location_id': self.location_id.id,
            'product_type': self.product_type,
        }
        return self.env.ref('ts_pos_profit_margin_report.action_pos_gp_report_xlsx').report_action(self, data=data)


class PosReportXLSX(models.AbstractModel):
    _name = 'report.ts_pos_profit_margin_report.pos_report'
    _inherit = 'report.report_xlsx.abstract'

    def _compute_pos_sale_profit_data(self, data):
        domain = [('order_id.state', 'not in', ('draft', 'cancel'))]
        if data.get('date_from', False):
            domain.append(('order_id.date_order', '>=', data.get('date_from')))
        if data.get('date_to', False):
            domain.append(('order_id.date_order', '<=', data.get('date_to')))
        if data.get('product_ids', False):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('partner_ids', False):
            domain.append(('order_id.partner_id', 'in', data.get('partner_ids')))
        if data.get('pos_order_id', False):
            domain.append(('order_id', '=', data.get('pos_order_id')))
        if data.get('company_id', False):
            domain.append(('order_id.company_id', '=', data.get('company_id')))
        if data.get('location_id', False):
            domain.append(('order_id.picking_ids.location_id', '=', data.get('location_id')))
        if data.get('product_type', False):
            domain.append(('product_id.type', '=', data.get('product_type')))

        pos_order_lines = self.env['pos.order.line'].search(domain)
        return pos_order_lines

    def generate_xlsx_report(self, workbook, data, records):
        company_id = self.env['res.company'].search([])[0]
        report_name = 'Pos Report'
        sheet = workbook.add_worksheet(report_name)
        bold = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#08013d', 'border': 1})
        bold.set_font_color('white')
        bold.set_border_color('white')
        bold.set_text_wrap()

        style1 = workbook.add_format({'bold': True, 'font_size': 11, 'fg_color': '#dfe4e4'})
        style3 = workbook.add_format({'bold': True, 'border': 1, 'fg_color': '#b0b8b3', 'num_format': '0.00"%"'})
        style3.set_border_color('918888')
        style4 = workbook.add_format(
            {'bold': True, 'border': 1, 'fg_color': '#08013d', 'font_color': 'white', 'num_format': '0.00"%"'})
        style4.set_border_color('white')
        style4.set_border(6)
        style2 = workbook.add_format({'bold': False, 'border': 1, })
        style2.set_border_color('918888')
        style5 = workbook.add_format(
            {'bold': True, 'num_format': '0.00"%"', 'align': 'right', 'valign': 'vcenter', 'fg_color': '#b0b8b3',
             'border': 1})
        style5.set_border_color('918888')
        money = workbook.add_format({'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'})
        date_format = workbook.add_format({'num_format': 'm/d/yyyy', 'border': 1})
        date_format.set_border_color('918888')
        money_bold = workbook.add_format(
            {'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)', 'bold': True, 'border': 1,
             'fg_color': '#b0b8b3'})
        money_bold.set_border_color('918888')
        percent_bold = workbook.add_format({'num_format': '0.00%', 'bold': True, 'border': 1, 'fg_color': '#b0b8b3'})
        percent_bold.set_border_color('918888')
        footer_bold = workbook.add_format(
            {'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)', 'bold': True, 'fg_color': '#08013d',
             'border': 1})
        footer_bold.set_font_color('white')
        footer_bold.set_border(6)
        footer_bold.set_border_color('white')
        footer_per_bold = workbook.add_format({'num_format': '0.00', 'bold': True, 'border': 1, 'fg_color': '#08013d'})
        footer_per_bold.set_font_color('white')
        footer_per_bold.set_border(6)
        footer_per_bold.set_border_color('white')
        money_style1 = workbook.add_format(
            {'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)', 'bold': True, 'fg_color': '#c6d9f0'})
        row = 1
        title_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#08013d', 'font_size': 16})
        title_format.set_font_color('white')
        title_format.set_border(6)
        title_format.set_border_color('white')
        sheet.set_row(0, 35)
        sheet.set_row(3, 24)
        # sheet.set_row(4, 23)
        sheet.merge_range('A1:N1', 'POS Gross Profit Report', title_format)
        sheet.merge_range('A4:E4', 'General Information', bold)
        sheet.merge_range('F4:J4', 'Sales Price ', bold)
        sheet.merge_range('K4:L4', 'Cost', bold)
        sheet.merge_range('M4:M5', 'Gross Profit', bold)
        sheet.merge_range('N4:N5', 'Margin', bold)
        row += 2
        sheet.write(1, 0, 'Date From', style2)
        sheet.write(1, 1, data.get('date_from', ''), style2)
        sheet.write(2, 0, 'Date To', style2)
        sheet.write(2, 1, data.get('date_to', ''), style2)
        if data.get('company_id', False):
            sheet.write(1, 3, 'POS Name', style2)
            company_id = self.env['res.company'].search([('id', '=', data.get('company_id'))])
            sheet.write(1, 4, company_id.name, style2)

        col = 0
        row += 1

        self._generate_pos_profit_report(sheet, data, row, col, bold, date_format, style2, money_bold, footer_bold,
                                         percent_bold, footer_per_bold, style3, style4, style5)

    def _generate_pos_profit_report(self, sheet, data, row, col, bold, date_format, style2, money_bold, footer_bold,
                                    percent_bold, footer_per_bold, style3, style4, style5):
        sheet.set_column('A:F', 16)
        sheet.set_column('B:B', 25)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 16)
        sheet.write(row, col, 'POS Order No', bold)
        sheet.write(row, col + 1, 'Product', bold)
        sheet.write(row, col + 2, 'Customer', bold)
        sheet.write(row, col + 3, 'Pos Name', bold)
        sheet.write(row, col + 4, 'Date', bold)
        sheet.write(row, col + 5, 'Qty', bold)
        sheet.write(row, col + 6, 'Unit Price', bold)
        sheet.write(row, col + 7, 'Discount', bold)
        sheet.write(row, col + 8, 'Taxes', bold)
        sheet.write(row, col + 9, 'Total', bold)
        sheet.merge_range('K5:L5', 'Direct Product Cost', bold)

        row += 1
        total_quant = 0
        total_price = 0
        direct_pro_cost = 0
        total_gross_profit = 0
        total_margin = 0
        total_taxes = 0
        total_discount = 0

        order_lines = self._compute_pos_sale_profit_data(data)
        for order_line in order_lines:
            print("fff", order_line.order_id.picking_ids)
            order_date = order_line.order_id.date_order or ''
            order_no = str(order_line.order_id.name) or ''
            pos_name = str(order_line.order_id.session_id.config_id.name) or ''
            customer = order_line.order_id.partner_id.name or 'Unknown'
            product = str(order_line.product_id.display_name)
            disc = 0
            if order_line.discount > 0:
                disc = (order_line.price_unit * order_line.qty * order_line.discount) / 100

            picking_iddd = self.env['stock.picking'].search([('origin', '=', order_line.order_id.name)])
            # picking_iddd=picking_iddd.move_id.stock_valuation_layer_ids.unit_cost
            move_liness = self.env['stock.move.line'].search(
                [('reference', '=', picking_iddd.name), ('product_id', '=', order_line.product_id.id)])
            stock_valuation_layer = self.env['stock.valuation.layer'].search(
                [('id', 'in', move_liness.move_id.stock_valuation_layer_ids.ids),
                 ('reference', '=', move_liness.reference),
                 ('product_id', '=', move_liness.product_id.id), ('quantity', '=', -abs(order_line.qty))])

            recipe_cons_cost = 0
            stored_pd_cost = 0
            if order_line.product_id.product_tmpl_id.is_recipe:
                mv_line_ids = self.env['stock.move.line'].search([('pos_order_id', '=', order_line.order_id.id), (
                    'parent_product_id', '=', order_line.product_id.product_tmpl_id.id)])
                for pd in mv_line_ids:
                    recipe_cons_cost += pd.value
            if order_line.order_id.session_id.picking_ids:
                if not order_line.product_id.product_tmpl_id.is_recipe:
                    for pick in order_line.order_id.session_id.picking_ids:
                        picking_lines = pick.move_line_ids_without_package
                        for pl in picking_lines:
                            if order_line.product_id == pl.product_id:
                                stored_pd_cost += pl.product_id.standard_price * order_line.qty

            sheet.write(row, col, order_no, style2)
            sheet.write(row, col + 1, product, style2)
            sheet.write(row, col + 2, customer, style2)
            sheet.write(row, col + 3, pos_name, style2)
            sheet.write(row, col + 4, order_date, date_format)
            sheet.write(row, col + 5, order_line.qty, money_bold)
            sheet.write(row, col + 6, order_line.price_unit, money_bold)
            sheet.write(row, col + 7, float(disc), money_bold)
            sheet.write(row, col + 8, order_line.price_subtotal_incl - order_line.price_subtotal, money_bold)
            sheet.write(row, col + 9, order_line.price_subtotal_incl, money_bold)
            product_profit = order_line.price_subtotal_incl - stock_valuation_layer.unit_cost
            sheet.merge_range(f"K{row + 1}:L{row + 1}", order_line.product_id.standard_price, money_bold)
            prc_total = product_profit
            sheet.write(row, col + 12, str(prc_total), style5)
            if order_line.price_subtotal:
                margin = prc_total / order_line.price_subtotal_incl
                margin = margin * 100
            else:
                margin = 0
            sheet.write(row, col + 13, margin, style3)
            row += 1
            total_quant += order_line.qty
            total_price = total_price + order_line.price_subtotal_incl
            direct_pro_cost += stored_pd_cost
            total_gross_profit += prc_total
            total_margin += margin
            total_taxes += order_line.price_subtotal_incl - order_line.price_subtotal
            total_discount += float(disc)

        sheet.set_row(row, 8)
        sheet.merge_range(f"A{row + 2}:E{row + 2}", "TOTAL", bold)
        sheet.merge_range(f"K{row + 2}:L{row + 2}", "-", bold)
        sheet.write(row + 1, 5, total_quant, footer_bold)
        sheet.write(row + 1, 6, '', footer_bold)
        sheet.write(row + 1, 7, total_discount, footer_bold)
        sheet.write(row + 1, 8, total_taxes, footer_bold)
        sheet.write(row + 1, 9, total_price, footer_bold)
        sheet.write(row + 1, 10, order_line.product_id.list_price, footer_per_bold)
        sheet.write(row + 1, 12, total_gross_profit, footer_bold)
        length_of_orderlines = len(order_lines)
        if length_of_orderlines > 0:
            average_of_margin = total_margin / length_of_orderlines
            sheet.write(row + 1, 13, average_of_margin, style4)
