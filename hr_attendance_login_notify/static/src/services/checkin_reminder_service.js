import { registry } from "@web/core/registry";

const checkinReminderService = {
    dependencies: ["bus_service", "notification", "mail.sound_effects"],

    start(env, services) {
        services.bus_service.subscribe("attendance_checkin_reminder", ({ message, title }) => {
            services.notification.add(message, {
                title,
                type: "warning",
                sticky: true,
            });
            services["mail.sound_effects"].play("new-message");
        });
        services.bus_service.start();
    },
};

registry.category("services").add("attendance_checkin_reminder", checkinReminderService);
