from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero
import json
from odoo.addons.account.models.account_move_line import AccountMoveLine


import collections
import logging
import re
from collections import namedtuple
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round
#import all functions from stock_landed_costs_lib
from . import stock_landed_costs_lib as slcl
from . import allocate_lib as al
from .num_lib import round_total as round_total

_logger = logging.getLogger(__name__)


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    amount_local_currency = fields.Monetary('Value in local currency', currency_field='currency_id', default=0.0,
                                            store=True,
                                            readonly=True, compute='_compute_amount_local_currency')
    vendor_bill_ids = fields.Many2many('account.move', 'stock_landed_cost_vendor_bill_rel', 'landed_cost_id',
                                       'vendor_bill_id', string='Vendor Bills', copy=False,
                                       domain=[('move_type', '=', 'in_invoice')])
    stevedoring = fields.Monetary('Stevedoring', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_stevedoring')
    demurrage = fields.Monetary('Demurrage', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_demurrage')
    transport = fields.Monetary('Transport', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_transport')
    storage = fields.Monetary('Storage', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_storage')
    bank = fields.Monetary('Bank charges', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_bank')
    miscellaneous = fields.Monetary('Miscellaneous', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_miscellaneous')
    royalty_fee = fields.Monetary('Royalty fee', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_royalty_fee')
    freight = fields.Monetary('Freight', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_freight')
    clearance = fields.Monetary('Clearance', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_clearance')
    transit = fields.Monetary('Transit', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_transit')
    insurance = fields.Monetary('Insurance', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_insurance')
    shipping = fields.Monetary('DHL/Fedex/UPS...', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_shipping')
    other = fields.Monetary('Other', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_other')
    royalty_fee_info = fields.Monetary('Royalty fee info', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_royalty_fee_info')
    declared_value = fields.Monetary('Declared Value', currency_field='currency_id', default=0.0, readonly=True, store=True, compute='_compute_declared_value')
    customs_value = fields.Monetary('Total Duty', currency_field='currency_id', default=0.0, readonly=True, store=True, 
                                    compute='_compute_customs_value')
    customs_vat_value = fields.Monetary('Customs VAT', currency_field='currency_id', default=0.0, readonly=True,
                                        compute='_compute_vat_value')
    total_customs_value = fields.Monetary('Total Customs Value', currency_field='currency_id', default=0.0,
                                          compute='_compute_total_customs_value')
    total_landed_cost = fields.Monetary('Total Landed Cost', currency_field='currency_id', default=0.0,
                                        compute='_compute_total_landed_cost')
    received_products_ids = fields.One2many('import_fees.received.product.line',
                                            compute='_compute_received_products_ids',
                                            inverse="_none", readonly=True, store=True, inverse_name='landed_costs_id', copy=False, string='Received Products')
    customs_fees_ids = fields.One2many('import_fees.customs_fees', inverse_name='landed_costs_id', copy=False, string='Customs Fees')
    create_landed_bill = fields.Boolean('Create Shipping Bill', compute='_compute_create_landed_bill')
    valuation_adjustment_lines = fields.One2many(
        'stock.valuation.adjustment.lines', 'cost_id', 'Valuation Adjustments',
        context={'group_by': ['product_id']}
    )
    has_hscode_split = fields.Boolean(compute='_compute_has_hscode_split', store=True)
    should_calc_customs_fees = fields.Boolean('Calculate Customs Fees', default=False, readonly=True, store=True, compute='_should_calc_customs_fees')
    should_compute_valuation_adjustment_lines = fields.Boolean('Compute Valuation Adjustments', default=False, readonly=True, store=True, compute='_should_compute_valuation_adjustment_lines')
    customs_fees_dirty = fields.Boolean('Customs Fees Dirty', compute="_compute_customs_fees_dirty", store=True, readonly=True, default=False)

    @api.depends('customs_fees_ids','customs_fees_ids.edited_fields',
                 'customs_fees_ids.com_value', 'customs_fees_ids.exm_value', 'customs_fees_ids.cif_value', 'customs_fees_ids.cid_value',
                 'customs_fees_ids.surcharge_value', 'customs_fees_ids.pal_value', 'customs_fees_ids.eic_value', 'customs_fees_ids.cess_levy_value',
                 'customs_fees_ids.excise_duty_value', 'customs_fees_ids.ridl_value', 'customs_fees_ids.srl_value', 'customs_fees_ids.sscl_value',
                 'customs_fees_ids.vat_value', 'cost_lines.price_unit', 'cost_lines.split_method', 'cost_lines.product_id', 'cost_lines')
    def _compute_customs_fees_dirty(self):
        """
        Compute whether customs fees have been manually edited and need recalculation.
        Only marks as dirty when there are actual changes to customs fees.
        """
        for record in self:
            # Check if any customs fees have been edited
                
            # For non-test mode
            has_edited_fees = False
            
            # Check if any customs fees have edited fields
            for fee in record.customs_fees_ids:
                # Check if edited_fields is not empty
                if fee.edited_fields:
                    has_edited_fees = True
                    break
                
                # Also check if there are any changed fields
                changed_fields = fee._get_changed_fields()
                if changed_fields:
                    has_edited_fees = True
                    # Ensure edited_fields is updated with the changed fields
                    if not fee.edited_fields:
                        fee.edited_fields = json.dumps(changed_fields)
                    break
            
            record.customs_fees_dirty = has_edited_fees
            
    @api.depends('cost_lines.price_unit', 'valuation_adjustment_lines.additional_landed_cost')
    def _should_compute_valuation_adjustment_lines(self):
        for record in self:
            record.should_compute_valuation_adjustment_lines = not record._check_sum()

    @api.depends('cost_lines.split_method')
    def _compute_has_hscode_split(self):
        for record in self:
            record.has_hscode_split = any(line.split_method == 'by_hscode' for line in record.cost_lines)


    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_stevedoring(self):
        self._compute_cost('stevedoring')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_demurrage(self):
        self._compute_cost('demurrage')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_transport(self):
        self._compute_cost('transport')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_storage(self):
        self._compute_cost('storage')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_bank(self):
        self._compute_cost('bank')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_miscellaneous(self):
        self._compute_cost('miscellaneous')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_royalty_fee(self):
        self._compute_cost('royalty_fee')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_freight(self):
        self._compute_cost('freight')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_clearance(self):
        self._compute_cost('clearance')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_transit(self):
        self._compute_cost('transit')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_insurance(self):
        self._compute_cost('insurance')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_shipping(self):
        self._compute_cost('shipping')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_other(self):
        self._compute_cost('other')

    @api.depends('cost_lines', 'picking_ids', 'vendor_bill_ids')
    def _compute_royalty_fee_info(self):
        self._compute_cost('royalty_fee_info')
   
    def create(self, vals: dict) -> models.Model:
        res = super(StockLandedCost, self).create(vals)
        if vals.get('vendor_bill_ids'):
            # Extract the actual IDs from the command tuples or direct ID list
            vendor_bill_ids = []

            # Handle both formats: command tuples or direct ID list
            if isinstance(vals['vendor_bill_ids'], list) and vals['vendor_bill_ids'] and isinstance(vals['vendor_bill_ids'][0], (list, tuple)):
                # Command tuples format: [(6, 0, [ids])] or [(4, id, 0)]
                for cmd in vals['vendor_bill_ids']:
                    if cmd[0] == 6 and len(cmd) > 2:  # Command format: (6, 0, [ids])
                        vendor_bill_ids.extend(cmd[2])
                    elif cmd[0] == 4 and len(cmd) > 1:  # Command format: (4, id, 0)
                        vendor_bill_ids.append(cmd[1])
            else:
                # Direct ID list format: [id1, id2, ...]
                vendor_bill_ids = [int(id) for id in vals['vendor_bill_ids'] if isinstance(id, (int, str)) and str(id).isdigit()]

            if vendor_bill_ids:
                # First, ensure vendor_bill_ids is properly set
                res.write({'vendor_bill_ids': [(6, 0, vendor_bill_ids)]})

                # Now get the vendor bills and find related pickings
                vendor_bills = self.env['account.move'].browse(vendor_bill_ids)
                purchase_orders = self.env['purchase.order'].search([('invoice_ids', 'in', vendor_bills.ids)])
                picking_ids = self.env['stock.picking'].search([('origin', 'in', purchase_orders.mapped('name'))])

                if picking_ids:
                    res.write({'picking_ids': [(6, 0, picking_ids.ids)]})
        return res

    def _compute_cost(self, attr):
        for record in self:
            record.__setattr__(attr, sum(self.cost_lines.filtered(lambda it: it.product_id.id == self.env.ref('import_fees.%s' % attr).id).mapped('price_unit')))

    @api.onchange('picking_ids')
    def _onchange_picking_ids_vendor_bills(self):
        original_picking_ids = self._origin.picking_ids.ids if self._origin else []
        deleted_picking_ids = [pid for pid in original_picking_ids if pid not in self.picking_ids.ids]
        added_picking_ids = [pid for pid in self.picking_ids.ids if pid not in original_picking_ids]
        
        # Convert ID lists to recordsets
        deleted_pickings = self.env['stock.picking'].browse(deleted_picking_ids) if deleted_picking_ids else self.env['stock.picking']
        added_pickings = self.env['stock.picking'].browse(added_picking_ids) if added_picking_ids else self.env['stock.picking']
        
        deleted_pickings_purchase_orders = self.env['purchase.order'].search([('name', 'in', deleted_pickings.mapped('origin'))]) if deleted_pickings else self.env['purchase.order']
        added_pickings_purchase_orders = self.env['purchase.order'].search([('name', 'in', added_pickings.mapped('origin'))]) if added_pickings else self.env['purchase.order']
        
        deleted_pickings_vendor_bills = deleted_pickings_purchase_orders.mapped('invoice_ids').filtered(lambda x: x.move_type == 'in_invoice') if deleted_pickings_purchase_orders else self.env['account.move']
        added_pickings_vendor_bills = added_pickings_purchase_orders.mapped('invoice_ids').filtered(lambda x: x.move_type == 'in_invoice') if added_pickings_purchase_orders else self.env['account.move']
        
        # Remove vendor bills that are no longer linked to the pickings
        for bill_id in deleted_pickings_vendor_bills:
            self.vendor_bill_ids = [(3, bill_id.id, 0)]
        
        # Add new vendor bills to existing ones
        for bill_id in added_pickings_vendor_bills:
            self.vendor_bill_ids = [(4, bill_id.id, 0)]
    
    @api.onchange('vendor_bill_ids')
    def _onchange_vendor_bill_ids(self):
        original_vendor_bill_ids = self._origin.vendor_bill_ids.ids if self._origin else []
        deleted_vendor_bill_ids = [bid for bid in original_vendor_bill_ids if bid not in self.vendor_bill_ids.ids]
        added_vendor_bill_ids = [bid for bid in self.vendor_bill_ids.ids if bid not in original_vendor_bill_ids]
        
        # Convert ID lists to recordsets
        deleted_vendor_bills = self.env['account.move'].browse(deleted_vendor_bill_ids) if deleted_vendor_bill_ids else self.env['account.move']
        added_vendor_bills = self.env['account.move'].browse(added_vendor_bill_ids) if added_vendor_bill_ids else self.env['account.move']
        
        deleted_vendor_bills_purchase_orders = self.env['purchase.order'].search([('invoice_ids', 'in', deleted_vendor_bills.ids)])
        added_vendor_bills_purchase_orders = self.env['purchase.order'].search([('invoice_ids', 'in', added_vendor_bills.ids)])
        
        deleted_vendor_bills_pickings = self.env['stock.picking'].search([('origin', 'in', deleted_vendor_bills_purchase_orders.mapped('name'))]) if deleted_vendor_bills_purchase_orders else self.env['stock.picking']
        
        # Remove pickings that are no longer linked to the vendor bills
        for picking_id in deleted_vendor_bills_pickings:
            self.picking_ids = [(3, picking_id.id, 0)]


    
    @api.depends('received_products_ids','received_products_ids.local_price_total')
    def _compute_amount_local_currency(self):
        for record in self:
            record.amount_local_currency = sum([it.local_price_total for it in record.received_products_ids])
    
    @api.depends('customs_fees_ids.amount')
    def _compute_customs_value(self):
        for record in self:
            fees_ids = record.customs_fees_ids
            if fees_ids and fees_ids[0].amount:
                record.customs_value = slcl.round_total(sum(it.amount for it in fees_ids))
            else:
                record.customs_value = 0.0

    @api.depends('customs_fees_ids.value')
    def _compute_declared_value(self):
        for record in self:
            fees_ids = record.customs_fees_ids
            if fees_ids:
                record.declared_value = slcl.round_total(sum(it.value for it in fees_ids))
            else:
                record.declared_value = 0.0

    @api.depends('customs_fees_ids.vat_value')
    def _compute_vat_value(self):
        for record in self:
            fees_ids = record.customs_fees_ids
            if fees_ids:
                record.customs_vat_value = slcl.round_total(sum([it.vat_value for it in fees_ids]))
            else:
                record.customs_vat_value = 0.0

    @api.depends('customs_value', 'customs_vat_value')
    def _compute_total_customs_value(self):
        for record in self:
            record.total_customs_value = record.customs_value + record.customs_vat_value



    def _none(self):
        pass

   
    @api.depends('cost_lines')
    def _compute_create_landed_bill(self):
        for elm in self:
            has_cost_lines_with_no_vendor_bill = any([line.origin_vendor_bill_id for line in elm.cost_lines if not line.origin_vendor_bill_id])
            elm.create_landed_bill = has_cost_lines_with_no_vendor_bill and self.env['ir.config_parameter'].sudo().get_param(
                'import_fees.shipping_bill_visible', False)


    def calc_customs_fees(self):
        """
        Calculate customs fees for all products in the landed cost.
        This is triggered by the button click in the landed costs form.
        """
        if not self.vendor_bill_ids:
            raise UserError(_("Please select a vendor bill"))
        if not self.picking_ids:
            raise UserError(_("Please select at least one picking"))
            
        # No special handling for test mode - all code paths should work the same way
            
        # Check if customs fees have already been calculated
        if self.customs_fees_ids:
            ctx = {'default_landed_cost_id': self.id }
            changed_fields = [it.edited_fields_dict() for it in self.customs_fees_ids]
            cif_value_and_other_value_edited = any([it for it in changed_fields if it.get('cif_value') and len(it) > 1])
            if cif_value_and_other_value_edited:
                ctx['default_cif_value_and_other_value_edited'] = True
            return {
                'type': 'ir.actions.act_window',
                'name': _('Recalculate Customs Fees'),
                'res_model': 'import_fees.recalculate.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': ctx
            }
        else:
            # If no fees exist, calculate them directly
            # Normal flow - calculate directly for first-time calculation
            for record in self.customs_fees_ids:
                record.with_context(force_recalculate=True).write({
                    'landed_costs_id': self.id,
                    'edited_fields': record.edited_fields
                })
            self.with_context(force_recalculate=True)._compute_customs_fees_ids(recalculate=True)
            return True


    def _compute_customs_fees_ids(self, recalculate=False, edits=[]):
        """
        Compute customs fees IDs and update related fields.
        This is called by calc_customs_fees when the button is clicked.
        """
        # Prevent recursion in test mode
        if self._context.get('skip_compute_fees_ids', False):
            return
            
        # Prepare context for recalculation
        context = {
            'force_recalculate': True,
            'force_detect_changes': True
        }
        # Call the library function to compute customs fees
        slcl._compute_customs_fees_ids(self, recalculate, edits=edits)
        
        # Force recalculation of amounts for all customs fees
        for fee in self.customs_fees_ids:
            # Add context to prevent recursion
            context['from_compute_fees_ids'] = True
                
            # fee.with_context(**context)._compute_amount()
            
        
        # Update the customs duties cost line with force_update flag
        if not self._context.get('skip_update_duties', False):
            context['force_update_duties'] = True
            # Add context to prevent recursion
            context['from_compute_fees_ids'] = True
                
            self.with_context(**context).update_customs_duties()
        
        else:
            # Reset the dirty flag
            self.customs_fees_dirty = False

    
    def update_customs_duties(self, new_value=None):
        """
        Update the customs duties cost line based on the sum of customs fees.
        This should only be called when explicitly requested via the button click,
        not automatically on save or during other operations.
        """
        # Prevent recursion in test mode
        if self._context.get('skip_update_duties', False):
            return
            
        # Proceed if explicitly requested, if we have a new value, or if in test mode
        if (self._context.get('force_update_duties', False) or
            new_value is not None):
            
            # Calculate customs duties amount
            customs_duties = sum([it.amount for it in self.customs_fees_ids]) if not new_value else new_value
            customs_product = self.env.ref('import_fees.customs')
            
            # Find existing cost line for customs not from vendor bill
            customs_cost_line = self.cost_lines.filtered(lambda it: it.product_id.id == customs_product.id and it.origin_vendor_bill_id.id == False)
            
            # Update existing line or create new one
            if customs_cost_line:
                customs_cost_line.price_unit = customs_duties
            else:
                has_customs_cost_line_from_vendor_bill = any([it for it in self.cost_lines if it.product_id.id == customs_product.id and it.origin_vendor_bill_id.id])
                if not has_customs_cost_line_from_vendor_bill:
                    # Get the product accounts with the correct company context
                    product_with_company = customs_product.with_company(self.company_id)
                    stock_input_account = product_with_company.product_tmpl_id.get_product_accounts()['stock_input'].id
                    
                    self.cost_lines = [(0, 0, {
                        'cost_id': self.id,
                        'name': (_("%s (Calculated)") % customs_product.name),
                        'product_id': customs_product.id,
                        'price_unit': customs_duties,
                        'split_method': 'by_hscode',
                        'account_id': stock_input_account,
                    })]
            
            # Reset the dirty flag after updating
            self.customs_fees_dirty = False

    @api.depends('stevedoring', 'demurrage', 'transport', 'storage', 'bank', 'miscellaneous', 'royalty_fee',
                 'freight', 'clearance', 'transit', 'insurance', 'shipping', 'other', 'royalty_fee_info',
                 'customs_value', 'customs_vat_value', 'amount_local_currency'
                 )
    def _compute_total_landed_cost(self):
        for record in self:
            record.total_landed_cost = slcl.round_total(record.stevedoring + record.demurrage + record.transport + record.storage +
                                            record.bank + record.miscellaneous + record.royalty_fee + record.freight +
                                            record.clearance + record.transit + record.insurance + record.shipping +
                                            record.other + record.royalty_fee_info + record.customs_value +
                                            record.customs_vat_value + record.amount_local_currency)



    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        for picking in self.picking_ids:
            error = False
            if not picking.origin:
                error = {'warning': {
                    'message': (_('The transfer %s has no purchase order.') % picking.name)},
                    'title': _('Transfers')
                }
            if not error and not self.env['purchase.order'].search(
                    [('name', '=', picking.origin)]).mapped('invoice_ids'):
                error = {
                    'warning': {'message': (_('The transfer %s\'s purchase order (%s) has no vendor bill.') % (
                        picking.name, picking.origin))},
                    'title': _('Transfers')
                }
            if error:
                self.picking_ids -= picking
                return error

    @api.depends('picking_ids', 'vendor_bill_ids')
    def _compute_received_products_ids(self):
        for record in self:
            record.received_products_ids = [(5,)]
            record.cost_lines = [(5,)]
            record.customs_fees_ids = [(5,)]
            record.valuation_adjustment_lines = [(5,)]
            if record.vendor_bill_ids:
                bill_lines = self.env['account.move.line'].search([('move_id', 'in', record.vendor_bill_ids.ids)])
                if record.picking_ids:
                    transfer_lines =  self.env['stock.move.line'].search(
                        [('picking_id', 'in', record.picking_ids.ids)], order='id')
                    records = []
                    for transfer_item in transfer_lines:
                        bill_line : AccountMoveLine  = slcl._find_bill_line(record,transfer_item)
                        if bill_line and transfer_item.quantity > 0:
                            records.append((0, 0, {
                                'move_id': transfer_item.move_id.id,
                                'product_id': transfer_item.product_id.id,
                                'currency_id': bill_line.currency_id.id,
                                'quantity': transfer_item.quantity,
                                'price_unit': bill_line.price_unit,
                                'local_currency_id': record.company_id.currency_id.id,
                                'price_total': transfer_item.quantity * bill_line.price_unit,
                                'local_price_total': bill_line.currency_id._convert(from_amount=
                                    transfer_item.quantity * bill_line.price_unit, to_currency= record.currency_id, round=False),
                                }))
                    record.received_products_ids = records
                landed_costs_lines = bill_lines.filtered(
                    lambda it: it.is_landed_costs_line and it.product_id.landed_cost_ok)
                records = []
                for item in landed_costs_lines:
                    split_method = item.product_id.product_tmpl_id.split_method_landed_cost \
                        or 'by_hscode' if (item.product_id.id == self.env.ref('import_fees.customs').id or \
                                            re.search(r'customs', item.product_id.name, re.IGNORECASE)) \
                            else 'by_current_cost_price'
                    cost_vals = {
                            'cost_id': record.id,
                            'name': item.name if item.name else item.product_id.name,
                            'price_unit': item.currency_id._convert(item.price_subtotal, item.company_currency_id, item.company_id, item.move_id.date),
                            'product_id': item.product_id.id,
                            'split_method': split_method,
                            'account_id': item.account_id.id,
                    }
                    # Only set origin_vendor_bill_id if the field exists on the model
                    if 'origin_vendor_bill_id' in self.env['stock.landed.cost.lines']._fields:
                        cost_vals['origin_vendor_bill_id'] = item.move_id.id
                    records.append((0, 0, cost_vals))
                record.cost_lines = records
            customs_duties = sum(record.cost_lines.filtered(lambda it: it.split_method == 'by_hscode').mapped('price_unit'))
            al.allocate_customs_duties(record, customs_duties)
            if customs_duties:
                self.update_customs_duties(new_value=customs_duties)
        return

    @api.depends('vendor_bill_ids', 'picking_ids', 'received_products_ids')
    def _compute_currency_value(self):
        self.amount_foreign_currency = sum(item.price_total for item in self.received_products_ids)

    @api.depends('received_products_ids', 'customs_value', 'vendor_bill_ids','cost_lines')
    def _should_calc_customs_fees(self):
        for record in self:
            has_customs_in_vendor_bills_move_lines = any([it.is_landed_costs_line and it.product_id.id == self.env.ref('import_fees.customs').id for it in record.vendor_bill_ids.mapped('line_ids')])
            has_international_products = any([it.is_domestic == 'international' for it in record.received_products_ids])
            has_pickings = len(record.picking_ids) > 0
            has_vendor_bills = len(record.vendor_bill_ids) > 0
            record.should_calc_customs_fees = has_pickings and has_vendor_bills and record.state == 'draft' and has_international_products and not has_customs_in_vendor_bills_move_lines
                    
    def button_create_landed_bill(self):
        def safe_flatten(lst, max_depth=10):
            result = []
            stack = [(lst, 0)]
            while stack:
                current, depth = stack.pop()
                if depth > max_depth:
                    result.append(current)
                    continue
                if isinstance(current, (bytes, str)) or not isinstance(current, collections.abc.Iterable):
                    result.append(current)
                else:
                    stack.extend((item, depth + 1) for item in reversed(current))
            return result

        # Search for all shipping bills with the same vendor bill by invoice origin
        lc_bills = self.env['account.move'].search(
            [('invoice_origin', '=', self.name), ('is_landed_bill', '=', True)])
        if lc_bills:
            return {
                'type': 'ir.actions.act_window',
                'name': _("Landed Costs Bill"),
                'res_model': 'account.move',
                'res_id': lc_bills[0]['id'],
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }
        else:
            # Find an appropriate account without filtering by company to avoid company mismatch issues
            account_inv_line = self.env['account.account'].with_company(self.company_id).search([
                ('account_type', '=', 'asset_current')
            ], limit=1)
            items = []
            customs_id = self.env.ref('import_fees.customs')
            cost_lines = self.cost_lines.filtered(lambda it: not it.origin_vendor_bill_id)
            for item in cost_lines:
                if item.product_id.id != customs_id.id:
                    items.append((0, 0, {
                        'product_id': item.product_id.id,
                        'quantity': 1,
                        'price_unit': item.price_unit,
                        'account_id': account_inv_line.id,
                        'name': item.name,
                    }))
            vendor_bill_id_invoice_line_ids = safe_flatten(self.vendor_bill_ids.mapped('invoice_line_ids'))
            for item in vendor_bill_id_invoice_line_ids:
                matching_customs_fees_item = next(iter([it for it in self.customs_fees_ids if
                                                        it.harmonized_code_id.harmonized_code_id.id ==
                                                        item.product_id.search_harmonized_code_id().id]),
                                                  False)
                if matching_customs_fees_item:
                    price_subtotal_local_currency = item.price_subtotal
                    proportion = price_subtotal_local_currency / sum(
                        [it.value for it in self.customs_fees_ids if
                         it.harmonized_code_id.harmonized_code_id.id ==
                         item.product_id.search_harmonized_code_id().id])
                    product_id = self.env.ref('import_fees.customs')
                    if matching_customs_fees_item.amount:
                        items.append((0, 0, {
                            'product_id': product_id.id,
                            'quantity': 1,
                            'price_unit': matching_customs_fees_item.amount * proportion,
                            'account_id': account_inv_line.id,
                            'name': "Customs / %s" % (item.product_id.name),
                        }))
                    if matching_customs_fees_item.vat_value:
                        items.append((0, 0, {
                            'product_id': product_id.id,
                            'quantity': 1,
                            'price_unit': matching_customs_fees_item.vat_value * proportion,
                            'account_id': account_inv_line.id,
                            'name': "VAT / %s" % (item.product_id.name),
                        }))
            result = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'invoice_line_ids': items,
                'invoice_date': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                'invoice_origin': self.name,
                'is_landed_bill': True,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': _("Landed Costs Bill"),
                'res_model': 'account.move',
                'res_id': result['id'],
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

    def compute_landed_cost(self):
        slcl.compute_landed_cost(self)
    
    def _check_sum(self: models.Model):
        """ Check if each cost line its valuation lines sum to the correct amount
        and if the overall total amount is correct also """
        prec_digits = 0
        for landed_cost in self:
            total_amount = sum(landed_cost.valuation_adjustment_lines.mapped('additional_landed_cost'))
            if not tools.float_is_zero(total_amount - landed_cost.amount_total, precision_digits=prec_digits):
                return False

            val_to_cost_lines = defaultdict(lambda: 0.0)
            for val_line in landed_cost.valuation_adjustment_lines:
                val_to_cost_lines[val_line.cost_line_id] += val_line.additional_landed_cost
            if any(not tools.float_is_zero(cost_line.price_unit - val_amount, precision_digits=prec_digits)
                    for cost_line, val_amount in val_to_cost_lines.items()):
                return False
        return True
