/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * EventCalendarFull Component
 * 
 * Full calendar view showing all events colored by CRM lead status.
 * Each event is clickable and opens the project.project form.
 */
export class EventCalendarFull extends Component {
    static template = "ptt_operational_dashboard.EventCalendarFull";
    static props = {};

    setup() {
        this.action = useService("action");
        this.homeService = useService("ptt_home");
        
        this.state = useState({
            currentDate: new Date(),
            events: [],
            loading: true,
        });
        
        onWillStart(async () => {
            await this.loadEvents();
        });
    }

    get currentMonthYear() {
        return this.state.currentDate.toLocaleDateString("en-US", { 
            month: "long", 
            year: "numeric" 
        });
    }

    get calendarDays() {
        const year = this.state.currentDate.getFullYear();
        const month = this.state.currentDate.getMonth();
        
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        
        const days = [];
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // Add days from previous month to fill the first week
        const startDayOfWeek = firstDay.getDay();
        for (let i = startDayOfWeek - 1; i >= 0; i--) {
            const date = new Date(year, month, -i);
            days.push({
                date: date,
                dateStr: date.toISOString().split('T')[0],
                day: date.getDate(),
                isCurrentMonth: false,
                isToday: false,
                events: [],
            });
        }
        
        // Add days of current month
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(year, month, day);
            const dateStr = date.toISOString().split('T')[0];
            days.push({
                date: date,
                dateStr: dateStr,
                day: day,
                isCurrentMonth: true,
                isToday: date.getTime() === today.getTime(),
                events: this.getEventsForDate(dateStr),
            });
        }
        
        // Add days from next month to complete the last week
        const remainingDays = 7 - (days.length % 7);
        if (remainingDays < 7) {
            for (let i = 1; i <= remainingDays; i++) {
                const date = new Date(year, month + 1, i);
                days.push({
                    date: date,
                    dateStr: date.toISOString().split('T')[0],
                    day: i,
                    isCurrentMonth: false,
                    isToday: false,
                    events: [],
                });
            }
        }
        
        return days;
    }

    get weekDays() {
        return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    }

    get legend() {
        return [
            { label: "Lead", color: "#87CEEB" },
            { label: "Awaiting Deposit", color: "#FFD700" },
            { label: "Booked", color: "#28A745" },
            { label: "Planning", color: "#FFA500" },
            { label: "Completed", color: "#6C757D" },
        ];
    }

    getEventsForDate(dateStr) {
        return this.state.events.filter(e => e.event_date === dateStr);
    }

    async loadEvents() {
        this.state.loading = true;
        try {
            const year = this.state.currentDate.getFullYear();
            const month = this.state.currentDate.getMonth();
            
            // Get first day of month and last day of month
            const startDate = new Date(year, month, 1).toISOString().split('T')[0];
            const endDate = new Date(year, month + 1, 0).toISOString().split('T')[0];
            
            this.state.events = await this.homeService.getEventCalendarData(startDate, endDate);
        } finally {
            this.state.loading = false;
        }
    }

    async onPrevMonth() {
        this.state.currentDate = new Date(
            this.state.currentDate.getFullYear(),
            this.state.currentDate.getMonth() - 1,
            1
        );
        await this.loadEvents();
    }

    async onNextMonth() {
        this.state.currentDate = new Date(
            this.state.currentDate.getFullYear(),
            this.state.currentDate.getMonth() + 1,
            1
        );
        await this.loadEvents();
    }

    async onToday() {
        this.state.currentDate = new Date();
        await this.loadEvents();
    }

    onEventClick(event) {
        if (event.action) {
            this.action.doAction(event.action);
        }
    }

    onViewInProjectApp() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Events",
            res_model: "project.project",
            views: [[false, "calendar"], [false, "list"], [false, "form"]],
            domain: [["x_event_date", "!=", false]],
            target: "current",
        });
    }
}

