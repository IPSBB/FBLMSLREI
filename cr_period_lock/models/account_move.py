# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains("move_type", "journal_id", "company_id", "date", "invoice_date")
    def _check_for_period_lock(self):
        """
        Constraint that checks whether the accounting move's date falls within a locked accounting period.
        It validates each record based on its move type, journal, company, and relevant date.

        - For journal entries (`move_type == 'entry'`), it checks the `date` field.
        - For other move types (e.g., invoices), it checks the `invoice_date`.

        If the date falls within a locked period for the specified journal and company, 
        a `ValidationError` is raised, preventing the operation.

        Raises:
            ValidationError: If the accounting period is locked for the given date, 
            journal, and company.
        """
        for record in self:
            journal_id = record.journal_id.id
            company_id = record.company_id.id
            move_type = record.move_type
            if move_type == 'entry':
                date = record.date
            else:
                date = record.invoice_date

            lock = self.env["account.period.lock"].is_locked(date, journal_id, company_id)

            if bool(lock):
                raise ValidationError(
                    _(
                        f"You cannot post account between '{lock.from_date}' and '{lock.to_date}'"
                    )
                )
