from odoo import models, fields, api, _
import logging
import json

_logger = logging.getLogger(__name__)

# Recalculate Customs Fees Wizard
class RecalculateWizard(models.TransientModel):
    _name = 'import_fees.recalculate.wizard'
    _description = 'Recalculate Customs Fees Wizard'

    landed_cost_id = fields.Many2one('stock.landed.cost', string='Landed Cost', required=True)
    cif_value_and_other_value_edited = fields.Boolean(string='CIF Value and Other Value Edited')

    def action_recalculate(self):
        self.ensure_one()
        edits = []
        
        # Prepare context for recalculation
        context = {
            'force_recalculate': True,
            'force_detect_changes': True
        }
        
        # Process all customs fees
        for record in self.landed_cost_id.customs_fees_ids:
                
            data = {'harmonized_code_id': record.harmonized_code_id, 'edits': record.edited_fields}
            edits.append(data)
        
        # Use context to ensure proper recalculation
        self.landed_cost_id.with_context(**context)._compute_customs_fees_ids(recalculate=True, edits=edits)
        
        # Update the customs duties cost line
        self.landed_cost_id.with_context(**context).update_customs_duties()
            
        return True

    def action_cancel(self):
        return True