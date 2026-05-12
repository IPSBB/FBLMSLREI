# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, api, models,_
from odoo.exceptions import ValidationError


class AccountPeriodLock(models.Model):
    _name = "account.period.lock"
    _description = "Accounting Period Lock"

    name = fields.Char(compute="compute_name", default="New")
    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    journal_ids = fields.Many2many(
        "account.journal", "period_journal", string="Journal"
    )
    company_ids = fields.Many2many("res.company", string="Company")

    state = fields.Selection(
        [("draft", "Draft"), ("locked", "Locked"), ("unlocked", "Unlocked")],
        string="Status",
        default="draft",
        tracking=True,
    )

    @api.constrains("from_date", "to_date")
    def _check_date_range(self):
        """
        Validates that the 'to_date' is greater than the 'from_date'.
        Raises a ValidationError if the 'to_date' is earlier than or equal to the 'from_date'.
        """
        for record in self:
            if (
                record.to_date
                and record.from_date
                and record.to_date <= record.from_date
            ):
                raise ValidationError(
                    _(
                        "The 'To Date' must be greater than the 'From Date'. Please select valid dates."
                    )
                )

    @api.constrains("from_date", "to_date", "journal_ids", "company_ids")
    def _check_duplicate_period_lock(self):
        """
        Ensures that there are no duplicate period locks for the same journal(s) and company(ies)
        within the specified date range. If a period lock exists with the same date range, journal,
        and company, raises a ValidationError.
        """
        for record in self:
            existing_period_lock = self.search(
                [
                    ("id", "!=", record.id),
                    ("from_date", "=", record.from_date),
                    ("to_date", "=", record.to_date),
                    ("journal_ids", "in", record.journal_ids.ids),
                    ("company_ids", "in", record.company_ids.ids),
                ]
            )

            if existing_period_lock:
                raise ValidationError(
                    _("Already period lock created for this journal for the given period.")
                )

    @api.constrains("from_date", "to_date")
    def _check_overlapping_of_period_lock(self):
        """
        Checks if the current period lock overlaps any previous period lock record's date range
        with same journals and companies.
        """
        for record in self:
            conflicting_period_lock = self.search(
                [
                    ("id", "!=", record.id),
                    ("journal_ids", "in", record.journal_ids.ids),
                    ("company_ids", "in", record.company_ids.ids),
                    "|",
                    "&",
                    ("from_date", "<=", record.to_date),
                    ("to_date", ">=", record.from_date),
                    "&",
                    ("from_date", "<=", record.to_date),
                    ("to_date", ">=", record.from_date),
                ]
            )

            if conflicting_period_lock:
                raise ValidationError(
                    _("Cannot generate overlapped period lock. Dates are creating conflict with previous record"
                ))

    def compute_name(self):
        """
        Computes the name field for each record by concatenating the string 'PD000'
        with the record's unique identifier (id).
        """
        for rec in self:
            rec.name = f"PD000{rec.id}"

    def is_locked(self, date, journal_id, company_id):
        """
        Checks whether a period lock exists for a specific journal, company, and date.
        Returns True if a lock is found, otherwise returns False.

        Args:
            date (datetime.date): The date to check for a lock.
            journal_id (int): The ID of the journal to check.
            company_id (int): The ID of the company to check.
        """
        lock = self.search(
            [
                ("from_date", "<=", date),
                ("to_date", ">=", date),
                ("journal_ids.id", "in", [journal_id]),
                ("company_ids.id", "in", [company_id]),
                ("state", "=", "locked"),
            ],
            limit=1,
        )
        return lock

    def action_lock(self):
        """
        Changes the state of the record to 'locked' if it is currently in 'draft' or 'unlocked' state.
        """
        for record in self:
            if record.state == "draft" or record.state == "unlocked":
                record.state = "locked"

    def action_unlock(self):
        """
        Changes the state of the record to 'unlocked' if it is currently in 'locked' state.
        """
        for record in self:
            if record.state == "locked":
                record.state = "unlocked"

    def action_draft(self):
        """
        Changes the state of the record to 'draft' if it is currently in either 'locked'
        or 'unlocked' state.
        """
        for record in self:
            if record.state == "locked" or record.state == "unlocked":
                record.state = "draft"
