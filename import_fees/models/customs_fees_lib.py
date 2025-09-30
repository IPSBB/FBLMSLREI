from odoo import models
from collections import namedtuple
from typing import Optional
from .num_lib import round_tariff, round_total

def mynamedtuple(typename, field_names, defaults=()):
    T = namedtuple(typename, field_names)
    T.__new__.__defaults__ = defaults
    return T

def _build_customs_fees_ids(self, recalculate=False, edits=[]):
    list_customs_fees_ids = []
    lc_id = self.id.origin if isinstance(self.id, models.NewId) else self.id
    hs_codes = set([it.hs_code_id for it in self.received_products_ids if it.hs_code_id])
    # If there are no HS codes or no received products, return an empty list
    if not hs_codes:
        return list_customs_fees_ids
        
    for harmonized_code_id in hs_codes:
        # For new records, check existing fees in memory rather than searching DB
        filter= [
            ('landed_costs_id', '=', lc_id),
            ('harmonized_code_id', '=', harmonized_code_id.id)
        ]
        existing = self.env['import_fees.customs_fees'].search(filter)
        if not existing:
            change_list = [it['edits'] for it in edits if it['harmonized_code_id'].id == harmonized_code_id.id]
            changes = change_list[0] if change_list else ''
            data = self.env['import_fees.customs_fees'].with_context(
                no_store=True,
                default_harmonized_code_id=harmonized_code_id.id,
                default_landed_costs_id=lc_id
            ).new().calculate_tariffs(recalculate=recalculate, changes=changes)
            data['landed_costs_id'] = lc_id
            data['harmonized_code_id'] = harmonized_code_id.id
            list_customs_fees_ids.append((0, 0, data))
    return list_customs_fees_ids

