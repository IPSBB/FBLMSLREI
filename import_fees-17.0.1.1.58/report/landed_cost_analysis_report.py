from odoo import models, fields, tools


class LandedCostAnalysisReport(models.Model):
    _name = 'landed.cost.analysis.report'
    _description = 'Landed Cost Analysis Report'
    _auto = False

    date = fields.Date(string='Date')
    landed_cost_id = fields.Many2one('stock.landed.cost', string='Landed Cost')
    product_id = fields.Many2one('product.product', string='Product')
    product_category_id = fields.Many2one('product.category', string='Product Category')

    base_purchase_price = fields.Float(string='Base Purchase Price')
    shipping_cost = fields.Float(string='Shipping Cost')
    customs_duties = fields.Float(string='Customs Duties')
    additional_landed_costs = fields.Float(string='Additional Landed Costs')
    other_fees = fields.Float(string='Other Fees')
    specific_tariffs = fields.Float(string='Specific Tariffs')
    miscellaneous_costs = fields.Float(string='Miscellaneous Costs')

    total_landed_cost = fields.Float(string='Total Landed Cost')
    quantity = fields.Float(string='Quantity')
    landed_cost_per_unit = fields.Float(string='Landed Cost per Unit')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
                SELECT
                    row_number() OVER () as id,
                    sl.date as date,
                    sl.id as landed_cost_id,
                    move.product_id as product_id,
                    pt.categ_id as product_category_id,
                    COALESCE(pol.price_unit * pol.product_qty, 0) as base_purchase_price,
                    COALESCE(cf.amount, 0) as customs_duties,
                    COALESCE(
                        (SELECT SUM(cl_add.price_unit)
                         FROM stock_landed_cost_lines cl_add
                         JOIN product_product pp_add ON pp_add.id = cl_add.product_id
                         WHERE cl_add.cost_id = sl.id
                         AND pp_add.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'stevedoring'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'demurrage'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'transport'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'storage')
                         )
                        ), 0
                    ) as additional_landed_costs,
                    COALESCE(
                        (SELECT SUM(cl_other.price_unit)
                         FROM stock_landed_cost_lines cl_other
                         JOIN product_product pp_other ON pp_other.id = cl_other.product_id
                         WHERE cl_other.cost_id = sl.id
                         AND pp_other.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'bank'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'clearance')
                         )
                        ), 0
                    ) as other_fees,
                    COALESCE(cf.pal_value + cf.eic_value + cf.ridl_value + cf.srl_value + cf.sscl_value, 0) as specific_tariffs,
                    COALESCE(
                        (SELECT SUM(cl_misc.price_unit)
                         FROM stock_landed_cost_lines cl_misc
                         JOIN product_product pp_misc ON pp_misc.id = cl_misc.product_id
                         WHERE cl_misc.cost_id = sl.id
                         AND pp_misc.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'miscellaneous'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'other')
                         )
                        ), 0
                    ) as miscellaneous_costs,
                    (COALESCE(pol.price_unit * pol.product_qty, 0) + 
                     COALESCE(
                        (SELECT SUM(cl_ship.price_unit)
                         FROM stock_landed_cost_lines cl_ship
                         JOIN product_product pp_ship ON pp_ship.id = cl_ship.product_id
                         WHERE cl_ship.cost_id = sl.id
                         AND pp_ship.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'freight'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'insurance')
                         )
                        ), 0
                     ) +
                     COALESCE(cf.amount, 0) +
                     COALESCE(
                        (SELECT SUM(cl_add.price_unit)
                         FROM stock_landed_cost_lines cl_add
                         JOIN product_product pp_add ON pp_add.id = cl_add.product_id
                         WHERE cl_add.cost_id = sl.id
                         AND pp_add.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'stevedoring'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'demurrage'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'transport'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'storage')
                         )
                        ), 0
                     ) +
                     COALESCE(
                        (SELECT SUM(cl_other.price_unit)
                         FROM stock_landed_cost_lines cl_other
                         JOIN product_product pp_other ON pp_other.id = cl_other.product_id
                         WHERE cl_other.cost_id = sl.id
                         AND pp_other.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'bank'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'clearance')
                         )
                        ), 0
                     ) +
                     COALESCE(cf.pal_value + cf.eic_value + cf.ridl_value + cf.srl_value + cf.sscl_value, 0) +
                     COALESCE(
                        (SELECT SUM(cl_misc.price_unit)
                         FROM stock_landed_cost_lines cl_misc
                         JOIN product_product pp_misc ON pp_misc.id = cl_misc.product_id
                         WHERE cl_misc.cost_id = sl.id
                         AND pp_misc.id IN (
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'miscellaneous'),
                             (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'other')
                         )
                        ), 0
                     )) as total_landed_cost,
                    move.product_qty as quantity,
                    CASE WHEN move.product_qty > 0 THEN
                        (COALESCE(pol.price_unit * pol.product_qty, 0) + 
                         COALESCE(
                            (SELECT SUM(cl_ship.price_unit)
                             FROM stock_landed_cost_lines cl_ship
                             JOIN product_product pp_ship ON pp_ship.id = cl_ship.product_id
                             WHERE cl_ship.cost_id = sl.id
                             AND pp_ship.id IN (
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'freight'),
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'insurance')
                             )
                            ), 0
                         ) +
                         COALESCE(cf.amount, 0) +
                         COALESCE(
                            (SELECT SUM(cl_add.price_unit)
                             FROM stock_landed_cost_lines cl_add
                             JOIN product_product pp_add ON pp_add.id = cl_add.product_id
                             WHERE cl_add.cost_id = sl.id
                             AND pp_add.id IN (
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'stevedoring'),
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'demurrage'),
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'transport'),
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'storage')
                             )
                            ), 0
                         ) +
                         COALESCE(
                            (SELECT SUM(cl_other.price_unit)
                             FROM stock_landed_cost_lines cl_other
                             JOIN product_product pp_other ON pp_other.id = cl_other.product_id
                             WHERE cl_other.cost_id = sl.id
                             AND pp_other.id IN (
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'bank'),
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'clearance')
                             )
                            ), 0
                         ) +
                         COALESCE(cf.pal_value + cf.eic_value + cf.ridl_value + cf.srl_value + cf.sscl_value, 0) +
                         COALESCE(
                            (SELECT SUM(cl_misc.price_unit)
                             FROM stock_landed_cost_lines cl_misc
                             JOIN product_product pp_misc ON pp_misc.id = cl_misc.product_id
                             WHERE cl_misc.cost_id = sl.id
                             AND pp_misc.id IN (
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'miscellaneous'),
                                 (SELECT res_id FROM ir_model_data WHERE model = 'product.product' AND module = 'import_fees' AND name = 'other')
                             )
                            ), 0
                         )) / move.product_qty
                    ELSE 0 END as landed_cost_per_unit
                FROM stock_landed_cost sl
                JOIN stock_valuation_adjustment_lines sval ON sval.cost_id = sl.id
                JOIN stock_move move ON move.id = sval.move_id
                JOIN product_product pp ON pp.id = move.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN purchase_order_line pol ON pol.id = move.purchase_line_id
                LEFT JOIN import_fees_customs_fees cf ON cf.landed_costs_id = sl.id
            )
        """ % self._table)
