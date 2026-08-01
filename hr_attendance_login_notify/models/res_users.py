import logging
from datetime import timedelta

from pytz import UTC

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    attendance_automation_enabled = fields.Boolean(
        string="Enable Missing Check-In Emails",
        help="Send repeated email reminders when this user logs in without checking in.",
    )
    attendance_checkin_reminder_minutes = fields.Integer(
        string="First Email After Login",
        default=5,
        help="Minutes after login before sending the first missing check-in email.",
    )
    attendance_checkin_repeat_minutes = fields.Integer(
        string="Repeat Email Every",
        default=15,
        help="Minutes between missing check-in reminder emails.",
    )
    attendance_last_checkin_reminder_login = fields.Datetime(copy=False, readonly=True)
    attendance_last_checkin_reminder_at = fields.Datetime(copy=False, readonly=True)

    @api.constrains(
        "attendance_checkin_reminder_minutes",
        "attendance_checkin_repeat_minutes",
    )
    def _check_attendance_automation_delays(self):
        for user in self:
            values = (
                user.attendance_checkin_reminder_minutes,
                user.attendance_checkin_repeat_minutes,
            )
            if any(value < 1 for value in values):
                raise ValidationError(_("Attendance email delays must be at least one minute."))

    def _attendance_employee(self):
        self.ensure_one()
        return self.employee_id.filtered(lambda employee: employee.company_id in self.company_ids)[:1]

    def _attendance_send_checkin_email(self):
        self.ensure_one()
        subject = _("Please check in to Odoo Attendances")
        message = _(
            "You logged in to Odoo but have not checked in through the "
            "Attendances application. Please check in as soon as possible."
        )
        email_to = self.employee_id.work_email or self.email
        if email_to:
            self.env["mail.mail"].sudo().create({
                "subject": subject,
                "body_html": _(
                    "<p>Hello %(employee)s,</p>"
                    "<p>%(message)s</p>",
                    employee=self.employee_id.name or self.name,
                    message=message,
                ),
                "email_to": email_to,
                "auto_delete": True,
            }).send(raise_exception=False)
        self._bus_send("attendance_checkin_reminder", {
            "title": subject,
            "message": message,
        })

    def _attendance_has_work_on_day(self, employee, moment):
        calendar = employee.resource_calendar_id
        if not calendar or calendar.flexible_hours:
            return False
        calendar_tz = calendar.tz or "UTC"
        localized = fields.Datetime.context_timestamp(
            self.with_context(tz=calendar_tz), moment
        )
        start = localized.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        intervals = calendar._work_intervals_batch(
            start, end, resources=employee.resource_id, compute_leaves=True
        ).get(employee.resource_id.id, [])
        return bool(intervals)

    @api.model
    def _cron_attendance_login_notify(self):
        now = fields.Datetime.now()
        users = self.sudo().search([
            ("active", "=", True),
            ("share", "=", False),
            ("attendance_automation_enabled", "=", True),
            ("employee_id", "!=", False),
        ])
        for user in users:
            try:
                with self.env.cr.savepoint():
                    user._process_login_attendance(now)
            except Exception:
                _logger.exception("Attendance login automation failed for user %s", user.id)

    def _process_login_attendance(self, now):
        self.ensure_one()
        employee = self._attendance_employee()
        login_at = self.login_date
        if not employee or not login_at or not self._attendance_has_work_on_day(employee, login_at):
            return

        login_local = fields.Datetime.context_timestamp(self, login_at)
        now_local = fields.Datetime.context_timestamp(self, now)
        if login_local.date() != now_local.date():
            return
        local_midnight = login_local.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start = local_midnight.astimezone(UTC).replace(tzinfo=None)
        attendance_today = self.env["hr.attendance"].sudo().search_count([
            ("employee_id", "=", employee.id),
            ("check_in", ">=", day_start),
        ], limit=1)
        if attendance_today:
            return

        first_due = login_at + timedelta(minutes=self.attendance_checkin_reminder_minutes)
        if now < first_due:
            return

        is_new_login = self.attendance_last_checkin_reminder_login != login_at
        repeat_due = (
            not is_new_login
            and self.attendance_last_checkin_reminder_at
            and now >= self.attendance_last_checkin_reminder_at
            + timedelta(minutes=self.attendance_checkin_repeat_minutes)
        )
        if is_new_login or repeat_due:
            self._attendance_send_checkin_email()
            self.write({
                "attendance_last_checkin_reminder_login": login_at,
                "attendance_last_checkin_reminder_at": now,
            })
