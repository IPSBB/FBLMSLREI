from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = "stock.move"

    consumption_id = fields.Many2one('stock.consumption', 'Consumption')

    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries """
        if not self.consumption_id:
            return super(StockMove, self)._account_entry_move(qty, description, svl_id, cost)

        am_vals = []
        self.ensure_one()
        am_vals += (super(StockMove, self)._account_entry_move(qty, description, svl_id, cost))
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return am_vals
        if self.restrict_partner_id and self.restrict_partner_id != self.company_id.partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return am_vals
        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        # redirect to this expense account
        expense_account = self.product_id.categ_id.property_account_expense_categ_id.id
        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            am_vals.append(
                self.with_context(expense_account=expense_account).with_company(company_to)._prepare_account_move_vals(
                    expense_account, acc_src, journal_id, qty, description, svl_id, cost))

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = -1 * cost
            am_vals.append(self.with_context(expense_account=expense_account).with_company(
                company_from)._prepare_account_move_vals(
                acc_dest, expense_account, journal_id, qty, description, svl_id, cost))
        return am_vals


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.depends('pos_order_id', 'pos_session_id')
    def _compute_unitcost_product(self):
        for move_line in self:
            if move_line.state == 'done':
                valuation_layers = move_line.move_id.stock_valuation_layer_ids
                cost = sum(valuation_layers.mapped(lambda svl: svl.unit_cost if svl.quantity > 0 else -svl.unit_cost))
                move_line.unit_cost = cost
                move_line.value = cost * move_line.quantity
            else:
                move_line.unit_cost = 0
                move_line.value = 0
        return

    uom_id = fields.Many2one(related='product_id.uom_id', readonly=True)
    unit_cost = fields.Float(compute='_compute_unitcost_product', string='Unit Value', store=True)
    value = fields.Float('Total Value')
    parent_product_id = fields.Many2one('product.template', string="Recipe Product")
    sale_order_id = fields.Many2one('sale.order', string="Order")
    pos_order_id = fields.Many2one('pos.order', string="Order")
    pos_session_id = fields.Many2one('pos.session', string="Session")

    # @api.model
    def set_recipe_product(self):
        stock_consum_ids = self.env['stock.consumption'].search([])
        for stock in stock_consum_ids:
            st_pd_list = []
            if stock.sale_order_id:
                ol_pd_list = []
                for spd in stock.product_ids:
                    st_pd_list.append(spd.id)
                order_lines = stock.sale_order_id.order_line
                for pd in order_lines:
                    if pd.product_id.product_tmpl_id.is_recipe:
                        for t in pd.product_id.product_tmpl_id.recipe_structure_ids:
                            ol_pd_list.append(t.product_id.id)
                        st_pd_list.sort()
                        ol_pd_list.sort()
                        if st_pd_list == ol_pd_list:
                            stock.parent_product_id = pd.product_id.product_tmpl_id
            if stock.pos_order_id:
                move_ids = stock.move_ids
                pos_pd_list = []
                for spd in stock.product_ids:
                    st_pd_list.append(spd.id)
                pos_lines = stock.pos_order_id.lines
                for pd in pos_lines:
                    if pd.product_id.product_tmpl_id.is_recipe:
                        for t in pd.product_id.product_tmpl_id.recipe_structure_ids:
                            pos_pd_list.append(t.product_id.id)
                        st_pd_list.sort()
                        pos_pd_list.sort()
                        if st_pd_list == pos_pd_list:
                            stock.parent_product_id = pd.product_id.product_tmpl_id
                for mv in move_ids:
                    for mv_line in mv.move_line_ids:
                        valuation_layers = mv_line.move_id.stock_valuation_layer_ids
                        cost = sum(
                            valuation_layers.mapped(lambda svl: svl.unit_cost if svl.quantity > 0 else -svl.unit_cost))
                        mv_line.unit_cost = cost
                        mv_line.value = cost * mv_line.qty_done
                        mv_line.parent_product_id = stock.parent_product_id
                        mv_line.pos_order_id = stock.pos_order_id
                        mv_line.pos_session_id = stock.pos_session_id

        pos_orders = self.env['pos.order'].search([])
        for pol in pos_orders.lines:
            if not pol.product_id.product_tmpl_id.is_recipe:
                if pol.order_id.picking_ids:
                    picking_lines = pol.order_id.picking_ids.move_line_ids_without_package
                    for pl in picking_lines:
                        # if pd.product_id == pl.product_id:
                        valuation_layers = pl.move_id.stock_valuation_layer_ids
                        cost = sum(
                            valuation_layers.mapped(lambda svl: svl.unit_cost if svl.quantity > 0 else -svl.unit_cost))
                        pl.unit_cost = cost
                        pl.value = cost * pl.qty_done
                        # stored_pd_cost += pl.value
