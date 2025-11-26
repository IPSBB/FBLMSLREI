from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Landed Cost Lines store the cost of the landed cost per product. This module adds a
# new split method to divide the cost by HS Code.
class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'
    split_method = fields.Selection(selection_add=[('by_hscode', 'By HS Code'), ],
                                    ondelete={'by_hscode': "cascade"},
                                    string='Split Method',
                                    required=True,
                                    help="Equal : Cost will be equally divided.\n"
                                         "By Quantity : Cost will be divided according to product's quantity.\n"
                                         "By Current cost : Cost will be divided according to product's current cost.\n"
                                         "By Weight : Cost will be divided depending on its weight.\n"
                                         "By Volume : Cost will be divided depending on its volume.\n"
                                         "By HS Code : Cost will be divided depending on its Harmonized System Code.")
    origin_vendor_bill_id = fields.Many2one('account.move', string='Origin Vendor Bill', readonly=True, store=True)

    #reject manual creation of split method by_hscode on update
    @api.model
    def write(self, vals):
        #reject manual creation of split method by_hscode
        if 'split_method' in vals and vals['split_method'] == 'by_hscode':
            raise UserError(_("You cannot manually use the split method 'By HS Code', please add this entry from a vendor/logistics bill."))
        #reject change of split method from by_hscode to another method
        old_split_method = self._origin.split_method
        if 'split_method' in vals and old_split_method == 'by_hscode':
            raise UserError(_("You cannot manually use the split method 'By HS Code', please add this entry from a vendor/logistics bill."))
        if self._check_requires_customs_duties_recalculation():
           self.cost_id._compute_customs_fees_ids(recalculate=True)
        return super(StockLandedCostLines, self).write(vals)
    
    #reject change of split method to by_hscode
    @api.onchange('split_method')
    def _onchange_split_method(self):
        old_split_method = self._origin.split_method
        if old_split_method == 'by_hscode':
            raise UserError(_("You cannot change the split method from 'By HS Code' to another method."))
        if self.split_method == 'by_hscode':
            raise UserError(_("You cannot manually use the split method 'By HS Code', please add this entry from a vendor/logistics bill."))
    
    #reject change of product_id for by_hscode split method
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.split_method == 'by_hscode':
            raise UserError(_("You cannot change the product for a line with split method 'By HS Code'."))
        if self._check_requires_customs_duties_recalculation():
           self.cost_id._compute_customs_fees_ids(recalculate=True)
        
        
    #reject change of quantity for by_hscode split method
    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        if self.split_method == 'by_hscode':
            raise UserError(_("You cannot change the unit price for a line with split method 'By HS Code', please add this entry from a vendor/logistics bill."))
        if self._check_requires_customs_duties_recalculation():
           self.cost_id._compute_customs_fees_ids(recalculate=True)
        
    def _check_requires_customs_duties_recalculation(self) -> bool:
        """Check if the cost line is for insurance or freight."""
        return (self.product_id.id == self.env.ref('import_fees.insurance').id or \
                self.product_id.id == self.env.ref('import_fees.freight').id) and \
                    len(self.cost_id.customs_fees_ids) > 0 and \
                        not any([it.is_landed_costs_line and \
                            it.product_id.id == self.env.ref('import_fees.customs').id \
                                for it in self.cost_id.vendor_bill_ids.mapped('line_ids')])    