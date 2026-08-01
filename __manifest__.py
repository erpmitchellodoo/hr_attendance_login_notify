{
    "name": "Attendance Login Notify",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Attendances",
    "summary": "Email and sound notifications for missing attendance check-ins",
    "description": """
Attendance Login Notify reminds employees who log in to Odoo but forget to
check in. It sends a configurable email and a sticky in-app notification with
sound, then repeats the reminder until attendance is recorded.
    """,
    "author": "Mitchel Admin",
    "maintainer": "Mitchel Admin",
    "support": "erpmitchellodoo@gmail.com",
    "license": "LGPL-3",
    "price": 0.0,
    "currency": "EUR",
    "depends": ["hr_attendance", "mail"],
    "data": [
        "data/ir_cron.xml",
        "views/res_users_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_login_notify/static/src/services/checkin_reminder_service.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
