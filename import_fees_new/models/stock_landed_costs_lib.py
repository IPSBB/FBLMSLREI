from collections import defaultdict

from odoo import models, tools, _
from odoo.exceptions import UserError


import logging

from . import customs_fees_lib as cfl
from .customs_fees import CustomsFees
from .num_lib import round_tariff, round_total
from odoo.addons.account.models.account_move_line import AccountMoveLine
from typing import Optional

_logger = logging.getLogger(__name__)


def _none(self):
    pass



def calc_customs_fees(self):
    if not self.vendor_bill_ids:
        raise UserError(_("Please select a vendor bill"))
    if not self.picking_ids:
        raise UserError(_("Please select at least one picking"))
    # Check if customs fees have already been calculated
    if self.customs_fees_ids:
        if self.cost_lines.filtered(lambda it: it.split_method == 'by_hscode'):
            raise UserError(_("Customs fees have already been calculated"))
        # If fees exist, show a confirmation dialog
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recalculate Customs Fees'),
            'res_model': 'import_fees.recalculate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_landed_cost_id': self.id}
        }
    else:
        # If no fees exist, calculate them directly
        self._compute_customs_fees_ids(recalculate=True)


def _find_bill_line(self, transfer_item) -> Optional[AccountMoveLine|bool]:
    """
    Find the exact bill line (account.move.line) that corresponds to the transfer item (stock.move.line).
    The search uses the purchase_line_id field of the stock.move to find the corresponding account move line.

    :param transfer_item: stock.move.line record
    :return: account.move.line record or False if not found
    """
    self.ensure_one()

    # Get the related stock.move from the stock.move.line
    move = transfer_item.move_id

    # Check if the move has a purchase line
    if not move or not move.purchase_line_id:
        return False

    purchase_line = move.purchase_line_id

    # Find the vendor bill (account.move) related to this purchase line
    invoice_lines = self.env['account.move.line'].search([
        ('purchase_line_id', '=', purchase_line.id),
        ('product_id', '=', move.product_id.id)
    ])

    # If we have multiple invoice lines, try to match by quantity
    if len(invoice_lines) > 1:
        raise UserError(_("Multiple invoice lines found for the same purchase line."))

    # If we have exactly one invoice line, return it
    elif len(invoice_lines) == 1:
        return invoice_lines[0]

    # No invoice line found
    return False


def _compute_create(self):
    pass

def _compute_customs_fees_ids(self, recalculate=False,edits=[]):
    self.customs_fees_ids = [(5,)]
    if self.received_products_ids:
        # create a list of all hs codes in the received products, filtering out False values (domestic vendors)
        hs_codes = set([it.hs_code_id for it in self.received_products_ids if it.hs_code_id])
        _logger.info(f"Found HS codes in received products: {[hc.name for hc in hs_codes]}")
        
        for harmonized_code_id in hs_codes:
            _logger.info(f"Processing HS code: {harmonized_code_id.name}, region: {harmonized_code_id.region_id.name}")
            
        self.customs_fees_ids = cfl._build_customs_fees_ids(self, recalculate, edits=edits)
        self.customs_vat_value = sum([it.vat_value for it in self.customs_fees_ids])


# Retrieve or create tax rates
def get_or_create_tax(self, amount):
    tax = self.env['account.tax'].search([('amount', '=', amount), ('type_tax_use', '=', 'purchase')], limit=1)
    if not tax:
        tax = self.env['account.tax'].create({
            'name': f'Tax {amount}%',
            'amount': amount,
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'display_name': f'{amount}%',
            # Assuming these are purchase taxes
            # Add other necessary fields according to your tax configuration
        })
    else:
        tax = tax[0]
    return tax
    

def compute_landed_cost(self):
    adjustment_lines = self.env['stock.valuation.adjustment.lines']
    adjustment_lines.search([('cost_id', 'in', self.ids)]).unlink()

    towrite_dict = {}
    for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
        cost = cost.with_company(cost.company_id)
        rounding = cost.currency_id.rounding
        total_qty = 0.0
        total_cost = 0.0
        total_weight = 0.0
        total_volume = 0.0
        total_line = 0.0
        all_val_line_values = cost.get_valuation_lines()
        all_customs_costs = []
        for val_line_values in all_val_line_values:
            for cost_line in cost.cost_lines:
                val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                self.env['stock.valuation.adjustment.lines'].create(val_line_values)
            hs_code = self.env['product.product'].search([('id', '=', val_line_values.get('product_id'))],
                                                            limit=1).search_harmonized_code_id() or False
            if hs_code:
                customs_cost = val_line_values.copy()
                customs_cost.update({
                    'hs_code': hs_code.id,

                })
                all_customs_costs.append(customs_cost)
            total_qty += val_line_values.get('quantity', 0.0)
            total_weight += val_line_values.get('weight', 0.0)
            total_volume += val_line_values.get('volume', 0.0)

            former_cost = val_line_values.get('former_cost', 0.0)
            total_cost += former_cost

            total_line += 1

        for line in cost.cost_lines:
            value_split = 0.0
            for valuation in cost.valuation_adjustment_lines:
                value = 0.0
                if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                    if line.split_method == 'by_quantity' and total_qty:
                        per_unit = (line.price_unit / total_qty)
                        value = valuation.quantity * per_unit
                    elif line.split_method == 'by_weight' and total_weight:
                        per_unit = (line.price_unit / total_weight)
                        value = valuation.weight * per_unit
                    elif line.split_method == 'by_volume' and total_volume:
                        per_unit = (line.price_unit / total_volume)
                        value = valuation.volume * per_unit
                    elif line.split_method == 'equal':
                        value = (line.price_unit / total_line)
                    elif line.split_method == 'by_current_cost_price' and total_cost:
                        per_unit = (line.price_unit / total_cost)
                        value = valuation.former_cost * per_unit
                    elif line.split_method == 'by_hscode' and total_qty:
                        move_id = valuation.move_id
                        received_product_list = self.received_products_ids.filtered(lambda it: it.move_id.id == move_id.id)
                        hs_code_list = set([it.hs_code_id.id for it in received_product_list if it.hs_code_id])
                        if received_product_list:
                            item_price_local = sum([it.local_price_total for it in received_product_list])
                            total_price_local = sum([it.local_price_total for it in self.received_products_ids \
                                if it.hs_code_id.id in hs_code_list])
                            customs_for_hscode = sum([it.amount for it in self.customs_fees_ids \
                                if it.harmonized_code_id.id in hs_code_list])
                            value = (customs_for_hscode * (item_price_local / total_price_local)) \
                                if total_price_local else 0.0 
                                    
                    else:
                        value = (line.price_unit / total_line)

                    if rounding:
                        value = tools.float_round(value, precision_rounding=rounding, rounding_method='UP')
                        fnc = min if line.price_unit > 0 else max
                        value = fnc(value, line.price_unit - value_split)
                        value_split += value

                    if valuation.id not in towrite_dict:
                        towrite_dict[valuation.id] = value
                    else:
                        towrite_dict[valuation.id] += value
    for key, value in towrite_dict.items():
        adjustment_lines.browse(key).write({'additional_landed_cost': value})
    return True
