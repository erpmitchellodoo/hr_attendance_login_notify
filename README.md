# Attendance Login Notify

This free Odoo 19 addon sends email and in-app reminders with sound when an
employee logs in to Odoo but does not check in through Attendances.

## Flow

1. The employee logs in on a scheduled working day.
2. If no attendance exists after 5 minutes, Odoo sends an email and a sticky
   in-app warning with a notification sound.
3. If attendance is still missing, Odoo repeats both reminders every 15 minutes.
4. Emails stop immediately after the employee checks in.

The delays can be configured by an administrator on the user's **Attendance
Automation** tab. The employee must be linked to an employee record with a work
email and a fixed working schedule. Non-working days, approved time off, and
flexible schedules are skipped.

The scheduled action runs every minute. This addon does not create or update
attendance records. Sound playback requires the employee to have an open Odoo
backend tab and may require prior interaction with the page due to browser
autoplay restrictions.
