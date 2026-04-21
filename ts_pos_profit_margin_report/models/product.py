import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # def get_default_consumption_location(self):
        # return self.env.ref('ts_pos_profit_margin_report.stock_location_material_consumption').id

    consumption_location_id = fields.Many2one(
        'stock.location', "Consumption Location", company_dependent=True, check_company=True,
        # default=get_default_consumption_location,
        domain="[('usage', '=', 'inventory'), '|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]",
        help="This stock location will be used, instead of the default one, as the source location for stock moves "
             "generated when you do an inventory consumption.")
    is_recipe = fields.Boolean('Is Recipe')
    recipe_structure_ids = fields.One2many('recipe.structure', 'parent_id', 'Recipe Structure')

    @api.onchange('is_recipe')
    def _onchange_set_service(self):
        if self.is_recipe:
            self.detailed_type = 'service'
            return
        self.detailed_type = 'product'
        return

    def check_if_structure_available(self, *args, **kwargs):
        result = {'error': False, 'message': ''}
        qty = kwargs.get('qty')
        if qty and kwargs.get('product_tmpl_id'):
            for product in self.env['product.template'].browse([kwargs.get('product_tmpl_id')]):
                if product.is_recipe and product.recipe_structure_ids:
                    for rs in product.recipe_structure_ids:
                        requird_qty = float(qty) * rs.qty_to_consum
                        if rs.product_id and rs.product_id.qty_available >= requird_qty:
                            _logger.info(rs.product_id.qty_available)
                        else:
                            result['error'] = True
                            result[
                                'message'] = "{0} -> {1} has no required quantity for consumption. Required {2} but available {3}".format(
                                product.name, rs.product_id.name, requird_qty, rs.product_id.qty_available)
                            return result
                    return result
                else:
                    result['error'] = True
                    result['message'] = "No Recipe Structure available for product: {0}".format(product.name)
                return result
            return result
        else:
            return result

    def verify_order(self, *args, **kwargs):
        result = {'error': False, 'message': ''}
        if kwargs.get('kwargs'):
            for line in kwargs.get('kwargs'):
                result = self.check_if_structure_available(
                    [line['product_tmpl_id']], qty=line.get('qty'), product_tmpl_id=line.get('product_tmpl_id')
                )
                if result['error']:
                    return result
        return result


class RecipeStructure(models.Model):
    _name = 'recipe.structure'
    _description = 'Recipe Structure'

    parent_id = fields.Many2one("product.template", string="Recipe Product", required=True)
    product_id = fields.Many2one("product.product", string="Product", domain="[('type','=','product')]")
    location_id = fields.Many2one("stock.location", string="Location", domain="[('usage','=','internal')]")
    company_id = fields.Many2one("res.company", string="Company")
    qty_to_consum = fields.Float('Qty Consumed')
