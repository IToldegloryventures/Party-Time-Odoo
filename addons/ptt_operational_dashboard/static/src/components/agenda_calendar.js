/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * AgendaCalendar Component
 * 
 * Mini calendar widget showing upcoming events for the current user.
 * Each event is clickable and opens the project.project form.
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
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        if (date.getTime() === today.getTime()) {
            return "Today";
        }
        if (date.getTime() === tomorrow.getTime()) {
            return "Tomorrow";
        }
        
        return date.toLocaleDateString("en-US", { 
            weekday: "short", 
            month: "short", 
            day: "numeric" 
        });
    }

    isToday(dateStr) {
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        date.setHours(0, 0, 0, 0);
        return date.getTime() === today.getTime();
    }

    getStatusClass(event) {
        const stageName = event.lead_stage?.name || "";
        const stageMap = {
            "New": "status-lead",
            "Qualified": "status-lead",
            "Awaiting Deposit": "status-awaiting",
            "Proposition": "status-awaiting",
            "Booked": "status-booked",
            "Won": "status-booked",
            "Planning": "status-planning",
            "Completed": "status-completed",
        };
        return stageMap[stageName] || "status-booked";
    }

    onEventClick(event) {
        if (event.action) {
            this.action.doAction(event.action);
        }
    }

    onViewAllClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "My Events",
            res_model: "project.project",
            views: [[false, "list"], [false, "form"]],
            domain: [["x_event_date", "!=", false]],
            context: { search_default_my_projects: 1 },
            target: "current",
        });
    }
}

