from odoo import models, fields, api, _
from . import customs_fees_lib as cfl
from typing import Optional
from .num_lib import round_tariff, round_total
import json

# Customs Fees store the customs fees calculated for each HS Code
class CustomsFees(models.Model):
    _name = "import_fees.customs_fees"
    _order = "harmonized_code_id"
    _description = "Customs Fees"
    harmonized_code_id = fields.Many2one('import_fees.harmonized_code_per_region', "HS Code")
    landed_costs_id = fields.Many2one('stock.landed.cost', "Landed Costs")
    rate = fields.Float("Rate")
    state = fields.Selection(related='landed_costs_id.state', string='Status', readonly=True, store=True)
    local_currency_id = fields.Many2one(related='landed_costs_id.currency_id', string='Local Currency',
                                        readonly=True, store=True)
    value = fields.Monetary("Declared Value", currency_field='local_currency_id')
    amount = fields.Monetary("Customs Duties", currency_field='local_currency_id',
                             digits='Product Price', store=True, readonly=True)
    com_value = fields.Monetary("COM", currency_field='local_currency_id')
    exm_value = fields.Monetary("EXM", currency_field='local_currency_id')
    cif_value = fields.Monetary("CIF", currency_field='local_currency_id')
    cid_value = fields.Monetary("CID", currency_field='local_currency_id')
    surcharge_value = fields.Monetary("Surcharge", currency_field='local_currency_id')
    pal_value = fields.Monetary("PAL", currency_field='local_currency_id')
    eic_value = fields.Monetary("EIC", currency_field='local_currency_id')
    cess_levy_value = fields.Monetary("Cess Levy", currency_field='local_currency_id')
    excise_duty_value = fields.Monetary("Excise Duty", currency_field='local_currency_id')
    ridl_value = fields.Monetary("RIDL", currency_field='local_currency_id')
    srl_value = fields.Monetary("SRL", currency_field='local_currency_id')
    sscl_value = fields.Monetary("SSCL", currency_field='local_currency_id')
    vat_value = fields.Monetary("VAT", currency_field='local_currency_id')
    origin_vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)
    is_com_visible = fields.Boolean('COM Visible', compute='_compute_visible_com_value', store=False)
    is_exm_visible = fields.Boolean('EXM Visible', compute='_compute_visible_exm_value', store=False)
    is_cid_visible = fields.Boolean('CID Visible', compute='_compute_visible_cid_value', store=False)
    is_surcharge_visible = fields.Boolean('Surcharge Visible', compute='_compute_visible_surcharge_value', store=False)
    is_pal_visible = fields.Boolean('PAL Visible', compute='_compute_visible_pal_value', store=False)
    is_eic_visible = fields.Boolean('EIC Visible', compute='_compute_visible_eic_value', store=False)
    is_cess_levy_visible = fields.Boolean('Cess Levy Visible', compute='_compute_visible_cess_levy_value', store=False)
    is_excise_duty_visible = fields.Boolean('Excise Duty Visible', compute='_compute_visible_excise_duty_value', store=False)
    is_ridl_visible = fields.Boolean('RIDL Visible', compute='_compute_visible_ridl_value', store=False)
    is_srl_visible = fields.Boolean('SRL Visible', compute='_compute_visible_srl_value', store=False)
    is_sscl_visible = fields.Boolean('SSCL Visible', compute='_compute_visible_sscl_value', store=False)
    is_vat_visible = fields.Boolean('VAT Visible', compute='_compute_visible_vat_value', store=False)
    is_edited_com = fields.Boolean('COM Edited', compute='_compute_edited_com_value', store=False)
    is_edited_exm = fields.Boolean('EXM Edited', compute='_compute_edited_exm_value', store=False)
    is_edited_cif = fields.Boolean('CIF Edited', compute='_compute_edited_cif_value', store=False)
    is_edited_cid = fields.Boolean('CID Edited', compute='_compute_edited_cid_value', store=False)
    is_edited_surcharge = fields.Boolean('Surcharge Edited', compute='_compute_edited_surcharge_value', store=False)
    is_edited_pal = fields.Boolean('PAL Edited', compute='_compute_edited_pal_value', store=False)
    is_edited_eic = fields.Boolean('EIC Edited', compute='_compute_edited_eic_value', store=False)
    is_edited_cess_levy = fields.Boolean('Cess Levy Edited', compute='_compute_edited_cess_levy_value', store=False)
    is_edited_excise_duty = fields.Boolean('Excise Duty Edited', compute='_compute_edited_excise_duty_value', store=False)
    is_edited_ridl = fields.Boolean('RIDL Edited', compute='_compute_edited_ridl_value', store=False)
    is_edited_srl = fields.Boolean('SRL Edited', compute='_compute_edited_srl_value', store=False)
    is_edited_sscl = fields.Boolean('SSCL Edited', compute='_compute_edited_sscl_value', store=False)
    is_edited_vat = fields.Boolean('VAT Edited', compute='_compute_edited_vat_value', store=False)
    edited_fields = fields.Text('Edited Fields', store=True)
    
    def __getattr__(self, name):
        # This is called when an attribute isn't found normally
        
        # Check if the attribute name follows our pattern
        if name.startswith('_compute_edited_'):
            # Extract the field name (everything after '_compute_edited_')
            field = name[len('_compute_edited_'):]
            
            # Return a function that calls the actual method with the field
            return lambda: self._compute_edited(field)
        if name.startswith('_compute_visible_'):
            # Extract the field name (everything after '_compute_visible_')
            field = name[len('_compute_visible_'):]
            return lambda: self._compute_visible(field)
        # Standard behavior for attributes that don't match our pattern
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def _compute_edited(self, field_name):
        """Check if a specific field has been edited."""
        for record in self:
            prefix = field_name[:-6] if field_name.endswith('_value') else field_name
            if not record.edited_fields:
                setattr(record, "is_edited_{}".format(prefix), False)
            else:
                try:
                    edited_fields = json.loads(record.edited_fields)
                except (ValueError, TypeError):
                    # Handle case where existing data isn't valid JSON
                    # or might be in the old comma-separated format
                    edited_fields = {}
                setattr(record, "is_edited_{}".format(prefix), field_name in edited_fields)
    
    @api.onchange('com_value', 'exm_value', 'cif_value', 'cid_value', 'surcharge_value',
                 'pal_value', 'eic_value', 'cess_levy_value', 'excise_duty_value',
                    'ridl_value', 'srl_value', 'sscl_value', 'vat_value')
    def onchange_values(self):
        """
        Handle UI changes to values by updating edited_fields.
        This is triggered by UI interactions only.
        """
        self._update_edited_fields()
    
    def _update_edited_fields(self):
        """
        Update edited_fields based on changed fields.
        This is used by both UI onchange and programmatic write.
        
        This method handles both singleton records and recordsets.
        """
        for record in self:
            # Get changed fields with their values
            changed_fields_dict = record._get_changed_fields()
            
            # Always recalculate when force_recalculate is set
            recalculate = self._context.get('force_recalculate', False)
            
            # If any fields changed or force_recalculate is set
            if changed_fields_dict or recalculate:
                # Get existing edited fields
                existing_dict = {}
                if record.edited_fields:
                    try:
                        existing_dict = json.loads(record.edited_fields)
                    except (ValueError, TypeError):
                        # Handle case where existing data isn't valid JSON
                        # or might be in the old comma-separated format
                        existing_dict = {}
                        
                # Merge existing and new changed fields
                existing_dict.update(changed_fields_dict)
                    
                # Update edited_fields as JSON
                record.edited_fields = json.dumps(existing_dict)
                for field in changed_fields_dict:
                    # Call the compute method for each field that has changed
                    record._compute_edited(field)
                record.landed_costs_id.customs_fees_dirty = True
    
    def write(self, vals):
        """
        Override write to handle programmatic changes.
        This ensures that edited_fields is updated even when changes
        are made programmatically (not through the UI).
        
        This method handles both singleton records and recordsets.
        """
        # Check if we're updating any tracked fields
        tracked_fields = set(self._get_float_fields())
        updated_tracked_fields = set(vals.keys()) & tracked_fields
        
        # If we're updating tracked fields, update edited_fields
        if updated_tracked_fields:
            # Get current edited_fields
            for record in self:
                if record.edited_fields:
                    try:
                        edited_fields_dict = json.loads(record.edited_fields)
                    except (ValueError, TypeError):
                        edited_fields_dict = {}
                else:
                    edited_fields_dict = {}
                
                # Update edited_fields with new values
                for field in updated_tracked_fields:
                    edited_fields_dict[field] = float(vals[field])
                
                # Update edited_fields in vals
                if edited_fields_dict:
                    vals['edited_fields'] = json.dumps(edited_fields_dict)
        
        result = super(CustomsFees, self).write(vals)

        return result

    def _compute_visible(self, field_name):
        """Compute visibility of fields based on configuration parameters."""
        for code in self:
            # remove the _value suffix from the field name to get the prefix
            prefix = field_name[:-6] if field_name.endswith('_value') else field_name
            # Get the visibility parameter from the configuration
            setattr(code,"is_{}_visible".format(prefix), self.env['ir.config_parameter'].sudo().get_param('import_fees.{}_visible'.format(prefix), False))

    @api.depends('com_value', 'exm_value', 'cif_value', 'cid_value', 'surcharge_value',
                'pal_value', 'eic_value', 'cess_levy_value', 'excise_duty_value',
                'ridl_value', 'srl_value', 'sscl_value', 'vat_value', 'edited_fields')
    def _compute_amount(self):
        """
        Compute the total amount of customs fees.
        This is triggered by changes to any of the fee values or edited_fields.
        However, it does NOT automatically recalculate all values - that only happens
        when explicitly requested via the button in the landed costs form.
        """
        for record in self:
            # Check if we're in a recalculation context
            force_recalculate = record._context.get('force_recalculate', False)
            
            # Check if we need to recalculate
            if force_recalculate:
                data = record.calculate_tariffs(recalculate=True)
                for key, value in data.items():
                    setattr(record, key, value)
                record.amount = data['amount']
            else:
                # Just sum up the values
                record.amount = sum([
                    record.com_value or 0.0,
                    record.exm_value or 0.0,
                    record.cid_value or 0.0,
                    record.surcharge_value or 0.0,
                    record.pal_value or 0.0,
                    record.eic_value or 0.0,
                    record.cess_levy_value or 0.0,
                    record.excise_duty_value or 0.0,
                    record.ridl_value or 0.0,
                    record.srl_value or 0.0,
                    record.sscl_value or 0.0
                ])
            changes = record._get_changed_fields()
            
            # If we're forcing recalculation or there are changes
            if force_recalculate or changes:
                # If we're forcing recalculation or CIF value changed, recalculate dependent values
                if force_recalculate or 'cif_value' in changes:
                    data = record.calculate_tariffs(recalculate=True)
                    for key, value in data.items():
                        setattr(record, key, value)
                    record.amount = data['amount']
                else:
                    # Just sum up the current values without recalculating
                    record.amount = record.com_value + record.exm_value + record.cid_value \
                        + record.surcharge_value + record.pal_value + record.eic_value + \
                            record.cess_levy_value + record.excise_duty_value + record.ridl_value + \
                                record.srl_value + record.sscl_value
            else:
                # No changes, use current values
                record.amount = record.com_value + record.exm_value + record.cid_value \
                    + record.surcharge_value + record.pal_value + record.eic_value + \
                        record.cess_levy_value + record.excise_duty_value + record.ridl_value + \
                            record.srl_value + record.sscl_value
        
        # Don't automatically update customs duties - this should only happen
        # when explicitly requested via the button

    def calculate_tariffs(self, recalculate=False, changes=""):
        """
        Calculate tariffs based on the harmonized code rates and values.
        This method is called by customs_fees_lib._build_customs_fees_ids.
        """
            
        hs = self.harmonized_code_id
        #get json changes
        if changes:
            try:
                new_value = json.loads(changes)
            except (ValueError, TypeError):
                # Handle case where existing data isn't valid JSON
                # or might be in the old comma-separated format
                new_value = {}
        else:
            new_value = {}
            
        # No special handling needed
            
        # If recalculate is True, we need to recalculate all fields
        def formula_or_value(attr: str, formula):
            '''Return the formula value if the field has not changed and recalculation is needed,
            otherwise return the old value if the field has not changed, otherwise return the new value'''
            if not attr in new_value:
                return formula() if recalculate else self[attr]
            else:
                return new_value[attr]
        exchange_rate = self.landed_costs_id.currency_id.with_context(date=self.landed_costs_id.date).rate
        currency_rate = self.landed_costs_id.company_id.currency_id.with_context(date=self.landed_costs_id.date).rate
        declared_value_local = sum([it.local_price_total for it in self.landed_costs_id.received_products_ids if
                                     it.hs_code_id.id == hs.id]) * exchange_rate
        proportion = declared_value_local / (self.landed_costs_id.amount_local_currency * (
                exchange_rate / currency_rate)) if self.landed_costs_id.amount_local_currency else 0.0
        com_value = formula_or_value('com_value', lambda: round_tariff(hs.com_value))
        exm_value = formula_or_value('exm_value', lambda: round_tariff(hs.exm_value))
        
        # Calculate CIF value if not provided
        if not 'cif_value' in new_value:
            cif_value = round_tariff(declared_value_local + proportion * (
                        sum([it.price_unit for it in self.landed_costs_id.cost_lines if it.product_id.id == self.env.ref('import_fees.insurance').id]) +
                        sum([it.price_unit for it in self.landed_costs_id.cost_lines if it.product_id.id == self.env.ref('import_fees.freight').id]))) \
                            if recalculate else \
                                self.cif_value
        else:
            cif_value = new_value['cif_value']
        cid_value = formula_or_value('cid_value', lambda: round_tariff(cif_value * hs.cid_rate))
        surcharge_value = formula_or_value('surcharge_value', lambda: round_tariff(cid_value * hs.surcharge_rate))
        pal_value = formula_or_value('pal_value', lambda: round_tariff(cif_value * hs.pal_rate))
        eic_value = formula_or_value('eic_value', lambda: round_tariff(cif_value * hs.eic_rate))
        cess_levy_value = formula_or_value('cess_levy_value', lambda: round_tariff(
            (cif_value + (cif_value * 0.1)) * hs.cess_levy_rate))
        excise_duty_value = formula_or_value('excise_duty_value', lambda: round_tariff(
            cif_value * hs.excise_duty_rate))
        vat_value = formula_or_value('vat_value', lambda: round_tariff(((cif_value * 1.1) + (
                cid_value + pal_value + eic_value + cess_levy_value + excise_duty_value)) * hs.vat_rate))
        srl_value = formula_or_value('srl_value', lambda: round_tariff((
                                    cid_value + surcharge_value + excise_duty_value) * hs.srl_rate))
        ridl_value = formula_or_value('ridl_value', lambda: round_tariff((cid_value + cif_value + surcharge_value + pal_value + cess_levy_value +
                            vat_value + excise_duty_value + srl_value) * hs.ridl_rate))
        sscl_value = formula_or_value('sscl_value', lambda: round_tariff((cif_value + 0.1 * cif_value + cid_value + pal_value + cess_levy_value +
                            excise_duty_value) * hs.sscl_rate))
        amount = round_total((cid_value + surcharge_value + pal_value + eic_value + cess_levy_value +
                                excise_duty_value + ridl_value + srl_value + sscl_value + com_value + exm_value))
        return {
            'rate': amount / declared_value_local if declared_value_local else 0.0,
            'value': declared_value_local,
            'com_value': com_value,
            'exm_value': exm_value,
            'amount': amount,
            'cif_value': cif_value,
            'cid_value': cid_value,
            'surcharge_value': surcharge_value,
            'pal_value': pal_value,
            'eic_value': eic_value,
            'cess_levy_value': cess_levy_value,
            'excise_duty_value': excise_duty_value,
            'vat_value': vat_value,
            'srl_value': srl_value,
            'ridl_value': ridl_value,
            'sscl_value': sscl_value,
        }

    def _get_float_fields(self):
        """Return the list of float fields we want to track changes for."""
        return [
            'com_value', 'exm_value', 'cif_value', 'cid_value', 'surcharge_value',
            'pal_value', 'eic_value', 'cess_levy_value', 'excise_duty_value',
            'ridl_value', 'srl_value', 'sscl_value', 'vat_value'
        ]
    
    def reset_edited_fields(self):
        """Reset the edited_fields to empty."""
        # Reset edited_fields to empty using direct SQL to ensure it's properly reset
        self.env.cr.execute(
            "UPDATE import_fees_customs_fees SET edited_fields = NULL WHERE id = %s",
            (self.id,)
        )
        # Invalidate the cache to ensure the change is reflected
        self.invalidate_recordset(['edited_fields'])
        
        # Also update the landed_cost's customs_fees_dirty flag if it exists
        if self.landed_costs_id:
            # Use direct SQL to update the landed_cost's customs_fees_dirty flag
            self.env.cr.execute(
                "UPDATE stock_landed_cost SET customs_fees_dirty = FALSE WHERE id = %s",
                (self.landed_costs_id.id,)
            )
            # Invalidate the cache to ensure the change is reflected
            self.landed_costs_id.invalidate_recordset(['customs_fees_dirty'])
    
    def edited_fields_dict(self):
        """Parses json string and returns a dictionary of edited fields."""
        if not self.edited_fields:
            return {}
        try:
            edited_fields = json.loads(self.edited_fields)
        except (ValueError, TypeError):
            # Handle case where existing data isn't valid JSON
            # or might be in the old comma-separated format
            edited_fields = {}
        return edited_fields
    

    def _get_changed_fields(self):
        """
        Detect changes in float fields by comparing current values with original values.
        Works in both UI and programmatic/test environments.
        
        This method handles both singleton records and recordsets.
        """
        # Ensure we're working with a singleton
        self.ensure_one()
        
        # Get fields to track
        fields_to_track = self._get_float_fields()
        
        # Initialize changed_fields_dict
        changed_fields_dict = {}
        
        # No special handling for force_recalculate or force_detect_changes
            
        # Otherwise, identify changed fields with their values
        changed_fields_dict = {}

        # Get original record from database
        original_id = self.id if isinstance(self.id, int) else (self._origin.id if self._origin else False)
        
        # If we have an existing record in the database
        if original_id:
            original = self.env['import_fees.customs_fees'].browse(original_id)
            
            # Check if original exists and has the fields
            if original.exists():
                for field in fields_to_track:
                    original_value = original[field]
                    current_value = self[field]
                    
                    # Compare with a small tolerance for float comparison
                    # Be more sensitive to CIF value changes
                    tolerance = 0.000001
                    if field == 'cif_value':
                        tolerance = 0.0000001  # More sensitive for CIF value
                        
                    if abs(current_value - original_value) > tolerance:
                        changed_fields_dict[field] = float(current_value)
        
        # No special handling for force_recalculate or force_detect_changes
        
                
        return changed_fields_dict
    
    def _get_value_id(self, attr) -> Optional[int]:
        value = self[attr]
        if not value:
            return False
        return value.id
    
    def _get_value_ids(self, attr) -> list[int]:
        value = self[attr]
        if not value:
            return []
        return [it.id for it in value]
