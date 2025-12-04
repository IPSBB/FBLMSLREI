from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PosMarginSelling(models.TransientModel):
    _name = 'pos.margin.selling'

    start_date = fields.Datetime(string="Start Date", required=False, help="Starting date")
    end_date = fields.Datetime(string="End Date", required=False, help="Ending date")
    pos_session_id = fields.Many2one('pos.session', string="Session", copy=False, required=False)
    type = fields.Selection(
        [('session', 'Session'), ('date', 'Date')],
        string='Report Print By', default='session', required=True)

    @api.onchange('type')
    def _onchange_type(self):
        """Clear values when type changes"""
        if self.type == 'session':
            self.start_date = False
            self.end_date = False
        elif self.type == 'date':
            self.pos_session_id = False

    def action_generate_report(self):
        """Generate top_selling product report from pos"""
        if self.type == 'date' and (not self.start_date or not self.end_date):
            raise ValidationError(_("Start Date and End Date are required for Date-based report"))

        # Check if 'session' type is selected, and validate pos_session_id
        if self.type == 'session' and not self.pos_session_id:
            raise ValidationError(_("POS Session is required for Session-based report"))

        # Prepare data for report
        data = {
            'start_date': self.start_date if self.type == 'date' else False,
            'end_date': self.end_date if self.type == 'date' else False,
            'type': self.type,
            'pos_session_id': self.pos_session_id.id if self.pos_session_id else False
        }

        return self.env.ref(
            'egy_pos_margin_reports.pos_margin_products_report'
        ).report_action([], data=data)
