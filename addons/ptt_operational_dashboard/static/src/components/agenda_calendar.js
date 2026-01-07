/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * AgendaCalendar Component
 * 
 * Mini calendar widget showing upcoming events from CRM leads for the current user.
 * Shows events at ALL stages - from new leads through booked projects.
 * Each event is clickable and opens the CRM lead form.
 */
export class AgendaCalendar extends Component {
    static template = "ptt_operational_dashboard.AgendaCalendar";
    static props = {
        events: { type: Array },
    };

    setup() {
        this.action = useService("action");
    }

    get groupedEvents() {
        const groups = {};
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        for (const event of this.props.events) {
            if (!event.event_date) continue;
            
            const dateKey = event.event_date;
            if (!groups[dateKey]) {
                groups[dateKey] = {
                    date: dateKey,
                    label: this.formatDateLabel(dateKey),
                    isToday: this.isToday(dateKey),
                    events: [],
                };
            }
            groups[dateKey].events.push(event);
        }
        
        // Sort by date and return as array
        return Object.values(groups).sort((a, b) => a.date.localeCompare(b.date));
    }

    formatDateLabel(dateStr) {
        const date = new Date(dateStr + "T00:00:00");
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        const dateOnly = new Date(date);
        dateOnly.setHours(0, 0, 0, 0);
        
        if (dateOnly.getTime() === today.getTime()) {
            return "Today";
        }
        if (dateOnly.getTime() === tomorrow.getTime()) {
            return "Tomorrow";
        }
        
        return date.toLocaleDateString("en-US", { 
            weekday: "short", 
            month: "short", 
            day: "numeric" 
        });
    }

    isToday(dateStr) {
        const date = new Date(dateStr + "T00:00:00");
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        date.setHours(0, 0, 0, 0);
        return date.getTime() === today.getTime();
    }

    onEventClick(event) {
        if (event.project_action) {
            this.action.doAction(event.project_action);
        } else if (event.action) {
            this.action.doAction(event.action);
        }
    }

    onViewAllClick() {
        // Open CRM leads with event dates (the Event Calendar tab)
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "My Events",
            res_model: "crm.lead",
            views: [[false, "calendar"], [false, "list"], [false, "kanban"], [false, "form"]],
            domain: [["x_event_date", "!=", false], ["user_id", "=", this.env.services.user.userId]],
            target: "current",
        });
    }
}
