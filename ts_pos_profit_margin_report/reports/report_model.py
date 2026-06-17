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
            'date_from': str(self.date_from) if self.date_from else False,
            'date_to': str(self.date_to) if self.date_to else False,
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
        if data.get('date_from'):
            domain.append(('order_id.date_order', '>=', data['date_from']))
        if data.get('date_to'):
            domain.append(('order_id.date_order', '<=', data['date_to']))
        if data.get('product_ids'):
            domain.append(('product_id', 'in', data['product_ids']))
        if data.get('partner_ids'):
            domain.append(('order_id.partner_id', 'in', data['partner_ids']))
        if data.get('pos_order_id'):
            domain.append(('order_id', '=', data['pos_order_id']))
        if data.get('company_id'):
            domain.append(('order_id.company_id', '=', data['company_id']))
        if data.get('location_id'):
            domain.append(('order_id.picking_ids.location_id', '=', data['location_id']))
        if data.get('product_type'):
            domain.append(('product_id.type', '=', data['product_type']))
        return self.env['pos.order.line'].search(domain)

    def _get_product_cost(self, order_line):
        """
        Returns the actual cost for the order line.
        Tries stock valuation layer first (AVCO/FIFO).
        Falls back to standard_price (standard costing).
        Returns (unit_cost, total_cost).
        """
        # Find the stock picking linked to this POS order
        picking = self.env['stock.picking'].search(
            [('origin', '=', order_line.order_id.name)], limit=1
        )

        unit_cost = 0.0
        if picking:
            # Find the stock move lines for this product in this picking
            move_lines = self.env['stock.move.line'].search([
                ('picking_id', '=', picking.id),
                ('product_id', '=', order_line.product_id.id),
            ])
            if move_lines:
                # Get the stock valuation layer linked to these moves (outgoing = negative qty)
                svl = self.env['stock.valuation.layer'].search([
                    ('id', 'in', move_lines.move_id.stock_valuation_layer_ids.ids),
                    ('product_id', '=', order_line.product_id.id),
                ], limit=1)
                if svl:
                    # SVL value is negative for outgoing; use abs per unit
                    unit_cost = abs(svl.value / svl.quantity) if svl.quantity else svl.unit_cost

        # Fallback to standard_price if no SVL found
        if not unit_cost:
            unit_cost = order_line.product_id.standard_price

        total_cost = unit_cost * abs(order_line.qty)
        return unit_cost, total_cost

    def generate_xlsx_report(self, workbook, data, records):
        report_name = 'Pos Report'
        sheet = workbook.add_worksheet(report_name)

        # ── Formats ──────────────────────────────────────────────────────────
        bold = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'fg_color': '#08013d', 'border': 1,
        })
        bold.set_font_color('white')
        bold.set_border_color('white')
        bold.set_text_wrap()

        style2 = workbook.add_format({'bold': False, 'border': 1})
        style2.set_border_color('918888')

        style3 = workbook.add_format({
            'bold': True, 'border': 1, 'fg_color': '#b0b8b3', 'num_format': '0.00"%"',
        })
        style3.set_border_color('918888')

        style4 = workbook.add_format({
            'bold': True, 'border': 1, 'fg_color': '#08013d',
            'font_color': 'white', 'num_format': '0.00"%"',
        })
        style4.set_border_color('white')
        style4.set_border(6)

        style5 = workbook.add_format({
            'bold': True, 'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)',
            'align': 'right', 'valign': 'vcenter', 'fg_color': '#b0b8b3', 'border': 1,
        })
        style5.set_border_color('918888')

        date_format = workbook.add_format({'num_format': 'm/d/yyyy', 'border': 1})
        date_format.set_border_color('918888')

        money_bold = workbook.add_format({
            'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)',
            'bold': True, 'border': 1, 'fg_color': '#b0b8b3',
        })
        money_bold.set_border_color('918888')

        footer_bold = workbook.add_format({
            'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)',
            'bold': True, 'fg_color': '#08013d', 'border': 1,
        })
        footer_bold.set_font_color('white')
        footer_bold.set_border(6)
        footer_bold.set_border_color('white')

        footer_per_bold = workbook.add_format({
            'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)',
            'bold': True, 'border': 1, 'fg_color': '#08013d',
        })
        footer_per_bold.set_font_color('white')
        footer_per_bold.set_border(6)
        footer_per_bold.set_border_color('white')

        title_format = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'fg_color': '#08013d', 'font_size': 16,
        })
        title_format.set_font_color('white')
        title_format.set_border(6)
        title_format.set_border_color('white')

        # ── Header ───────────────────────────────────────────────────────────
        sheet.set_row(0, 35)
        sheet.set_row(3, 24)
        sheet.merge_range('A1:N1', 'POS Gross Profit Report', title_format)
        sheet.merge_range('A4:E4', 'General Information', bold)
        sheet.merge_range('F4:J4', 'Sales Price', bold)
        sheet.merge_range('K4:L4', 'Cost', bold)
        sheet.merge_range('M4:M5', 'Gross Profit', bold)
        sheet.merge_range('N4:N5', 'Margin', bold)

        sheet.write(1, 0, 'Date From', style2)
        sheet.write(1, 1, data.get('date_from', '') or '', style2)
        sheet.write(2, 0, 'Date To', style2)
        sheet.write(2, 1, data.get('date_to', '') or '', style2)

        if data.get('company_id'):
            company = self.env['res.company'].browse(data['company_id'])
            sheet.write(1, 3, 'Company', style2)
            sheet.write(1, 4, company.name or '', style2)

        self._generate_pos_profit_report(
            sheet, data, 4, 0,
            bold, date_format, style2, money_bold,
            footer_bold, footer_per_bold, style3, style4, style5,
        )

    def _generate_pos_profit_report(self, sheet, data, row, col,
                                    bold, date_format, style2, money_bold,
                                    footer_bold, footer_per_bold, style3, style4, style5):
        # ── Column widths ────────────────────────────────────────────────────
        sheet.set_column('A:A', 16)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:F', 16)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:N', 16)

        # ── Column headers (row 4, index 4) ──────────────────────────────────
        headers = [
            'POS Order No', 'Product', 'Customer', 'Pos Name', 'Date',
            'Qty', 'Unit Price', 'Discount', 'Taxes', 'Total',
        ]
        for i, h in enumerate(headers):
            sheet.write(row, col + i, h, bold)
        sheet.merge_range(f'K{row + 1}:L{row + 1}', 'Direct Product Cost', bold)

        row += 1  # move to data rows

        # ── Totals accumulators ───────────────────────────────────────────────
        total_quant = 0.0
        total_price = 0.0
        total_cost = 0.0
        total_gross_profit = 0.0
        total_margin = 0.0
        total_taxes = 0.0
        total_discount = 0.0

        order_lines = self._compute_pos_sale_profit_data(data)

        for order_line in order_lines:
            order_date = order_line.order_id.date_order or ''
            order_no = order_line.order_id.name or ''
            pos_name = order_line.order_id.session_id.config_id.name or ''
            customer = order_line.order_id.partner_id.name or 'Unknown'
            product = order_line.product_id.display_name or ''

            # Discount amount
            disc = 0.0
            if order_line.discount > 0:
                disc = (order_line.price_unit * order_line.qty * order_line.discount) / 100.0

            # Tax amount
            tax_amount = order_line.price_subtotal_incl - order_line.price_subtotal

            # Cost (unit + total)
            unit_cost, line_total_cost = self._get_product_cost(order_line)

            # Gross profit = revenue (incl. tax) - cost
            revenue = order_line.price_subtotal_incl
            gross_profit = revenue - line_total_cost

            # Margin %
            if revenue:
                margin = (gross_profit / revenue) * 100.0
            else:
                margin = 0.0

            # ── Write row ────────────────────────────────────────────────────
            sheet.write(row, col + 0, order_no, style2)
            sheet.write(row, col + 1, product, style2)
            sheet.write(row, col + 2, customer, style2)
            sheet.write(row, col + 3, pos_name, style2)
            sheet.write(row, col + 4, order_date, date_format)
            sheet.write(row, col + 5, order_line.qty, money_bold)
            sheet.write(row, col + 6, order_line.price_unit, money_bold)
            sheet.write(row, col + 7, disc, money_bold)
            sheet.write(row, col + 8, tax_amount, money_bold)
            sheet.write(row, col + 9, revenue, money_bold)
            sheet.merge_range(f'K{row + 1}:L{row + 1}', line_total_cost, money_bold)
            sheet.write(row, col + 12, gross_profit, style5)
            sheet.write(row, col + 13, margin, style3)

            row += 1

            # Accumulate totals
            total_quant += order_line.qty
            total_price += revenue
            total_cost += line_total_cost
            total_gross_profit += gross_profit
            total_margin += margin
            total_taxes += tax_amount
            total_discount += disc

        # ── Footer ───────────────────────────────────────────────────────────
        sheet.set_row(row, 8)  # spacer row
        footer_row = row + 1   # actual footer (1-indexed: row+2 in merge_range)

        sheet.merge_range(f'A{footer_row + 1}:E{footer_row + 1}', 'TOTAL', bold)
        sheet.merge_range(f'K{footer_row + 1}:L{footer_row + 1}', total_cost, footer_per_bold)
        sheet.write(footer_row, col + 5, total_quant, footer_bold)
        sheet.write(footer_row, col + 6, '', footer_bold)
        sheet.write(footer_row, col + 7, total_discount, footer_bold)
        sheet.write(footer_row, col + 8, total_taxes, footer_bold)
        sheet.write(footer_row, col + 9, total_price, footer_bold)
        sheet.write(footer_row, col + 12, total_gross_profit, footer_bold)

        if order_lines:
            average_margin = total_margin / len(order_lines)
            sheet.write(footer_row, col + 13, average_margin, style4)