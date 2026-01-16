/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * EventCalendarFull Component
 * 
 * Full calendar view showing ALL CRM events company-wide.
 * Events are color-coded by CRM pipeline stage.
 * 
 * Features:
 * - Shows ALL events by default (company-wide view)
 * - "My Events" toggle to filter to user's assigned events
 * - Stage filter to show/hide specific stages
 * - Day panel showing selected date's events
 * - Click event to open CRM Lead form
 * 
 * Data Source: crm.lead with ptt_event_date field
 */
export class EventCalendarFull extends Component {
    static template = "ptt_super_dashboard.EventCalendarFull";
    static props = {};

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        
        // Get current month date range
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        
        this.state = useState({
            currentDate: new Date(),
            events: [],
            stages: [],
            loading: true,
            myEventsOnly: false,
            selectedDate: null,
            selectedDateEvents: [],
            visibleStages: {}, // stage_id -> boolean
            currentUserId: null,
            startDate: this.formatDateForInput(firstDay),
            endDate: this.formatDateForInput(lastDay),
            dateRange: 'this_month', // this_week, this_month, custom
        });
        
        onWillStart(async () => {
            await this.loadCalendarData();
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
        
        // Add days from previous month to fill the first week (start on Sunday)
        const startDayOfWeek = firstDay.getDay();
        for (let i = startDayOfWeek - 1; i >= 0; i--) {
            const date = new Date(year, month, -i);
            days.push(this._createDayObject(date, false, today));
        }
        
        // Add days of current month
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(year, month, day);
            days.push(this._createDayObject(date, true, today));
        }
        
        // Add days from next month to complete the grid (6 rows = 42 days)
        const totalDays = 42;
        const remainingDays = totalDays - days.length;
        for (let i = 1; i <= remainingDays; i++) {
            const date = new Date(year, month + 1, i);
            days.push(this._createDayObject(date, false, today));
        }
        
        return days;
    }

    _createDayObject(date, isCurrentMonth, today) {
        const dateStr = this._formatDateStr(date);
        const isSelected = this.state.selectedDate === dateStr;
        
        return {
            date: date,
            dateStr: dateStr,
            day: date.getDate(),
            isCurrentMonth: isCurrentMonth,
            isToday: date.getTime() === today.getTime(),
            isSelected: isSelected,
            events: this.getEventsForDate(dateStr),
        };
    }

    _formatDateStr(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    get weekDays() {
        return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    }

    get filteredEvents() {
        let events = this.state.events;
        
        // Filter by visible stages
        if (Object.keys(this.state.visibleStages).length > 0) {
            events = events.filter(e => {
                const stageId = e.stage_id || 'unknown';
                return this.state.visibleStages[stageId] !== false;
            });
        }
        
        return events;
    }

    getEventsForDate(dateStr) {
        return this.filteredEvents.filter(e => e.event_date === dateStr);
    }

    get selectedDateDisplay() {
        if (!this.state.selectedDate) return "";
        const date = new Date(this.state.selectedDate + "T00:00:00");
        return date.toLocaleDateString("en-US", {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric"
        });
    }

    get eventCounts() {
        const total = this.state.events.length;
        const myEvents = this.state.events.filter(e => e.is_mine).length;
        return { total, myEvents };
    }

    formatDateForInput(date) {
        return date.toISOString().split('T')[0];
    }

    async loadCalendarData() {
        this.state.loading = true;
        try {
            let startDate, endDate;
            
            if (this.state.dateRange === 'custom') {
                startDate = this.state.startDate;
                endDate = this.state.endDate;
            } else {
                // Use current month view
                const year = this.state.currentDate.getFullYear();
                const month = this.state.currentDate.getMonth();
                startDate = this._formatDateStr(new Date(year, month - 1, 1));
                endDate = this._formatDateStr(new Date(year, month + 2, 0));
            }
            
            // Call backend method
            const result = await this.orm.call(
                "ptt.home.data",
                "get_event_calendar_data",
                [],
                {
                    start_date: startDate,
                    end_date: endDate,
                    my_events_only: this.state.myEventsOnly,
                }
            );
            
            this.state.events = result.events || [];
            this.state.stages = result.stages || [];
            this.state.currentUserId = result.current_user_id;
            
            // Initialize visible stages (all visible by default)
            if (Object.keys(this.state.visibleStages).length === 0) {
                for (const stage of this.state.stages) {
                    this.state.visibleStages[stage.id] = true;
                }
            }
            
            // Select today by default
            if (!this.state.selectedDate) {
                this.state.selectedDate = this._formatDateStr(new Date());
                this.state.selectedDateEvents = this.getEventsForDate(this.state.selectedDate);
            }
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
        await this.loadCalendarData();
    }

    async onNextMonth() {
        this.state.currentDate = new Date(
            this.state.currentDate.getFullYear(),
            this.state.currentDate.getMonth() + 1,
            1
        );
        await this.loadCalendarData();
    }

    async onToday() {
        this.state.currentDate = new Date();
        this.state.selectedDate = this._formatDateStr(new Date());
        await this.loadCalendarData();
    }

    async onToggleMyEvents() {
        this.state.myEventsOnly = !this.state.myEventsOnly;
        await this.loadCalendarData();
    }

    async     setDateRange(range) {
        const now = new Date();
        let startDate, endDate;
        
        switch (range) {
            case 'this_week':
                const dayOfWeek = now.getDay();
                const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Monday
                startDate = new Date(now.getFullYear(), now.getMonth(), diff);
                endDate = new Date(now.getFullYear(), now.getMonth(), diff + 6);
                this.state.currentDate = new Date(startDate);
                break;
            case 'this_month':
                startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                this.state.currentDate = new Date(startDate);
                break;
            case 'last_month':
                startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), 0);
                this.state.currentDate = new Date(startDate);
                break;
            case 'ytd':
                startDate = new Date(now.getFullYear(), 0, 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                this.state.currentDate = new Date(startDate);
                break;
            case 'custom':
                this.state.dateRange = 'custom';
                return; // Don't reload, let user set dates manually
            default:
                return;
        }
        
        this.state.startDate = this.formatDateForInput(startDate);
        this.state.endDate = this.formatDateForInput(endDate);
        this.state.dateRange = range;
        await this.loadCalendarData();
    }

    async onDateChange() {
        this.state.dateRange = 'custom';
        await this.loadCalendarData();
    }

    get dateRangeLabel() {
        if (this.state.dateRange === 'custom') {
            const start = new Date(this.state.startDate + "T00:00:00");
            const end = new Date(this.state.endDate + "T00:00:00");
            const options = { month: 'short', day: 'numeric' };
            return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
        }
        return this.currentMonthYear;
    }

    onToggleStage(stageId) {
        this.state.visibleStages[stageId] = !this.state.visibleStages[stageId];
        // Update selected date events
        this.state.selectedDateEvents = this.getEventsForDate(this.state.selectedDate);
    }

    onDayClick(day) {
        this.state.selectedDate = day.dateStr;
        this.state.selectedDateEvents = this.getEventsForDate(day.dateStr);
    }

    onEventClick(event) {
        // Prefer Project when available (avoids CRM/Project duplication and matches operational flow)
        if (event.project_action) {
            this.action.doAction(event.project_action);
        } else if (event.action) {
            this.action.doAction(event.action);
        }
    }

    onViewInCRM() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Events Calendar",
            res_model: "crm.lead",
            views: [[false, "calendar"], [false, "list"], [false, "kanban"], [false, "form"]],
            domain: [["ptt_event_date", "!=", false]],
            context: {
                default_type: "opportunity",
            },
            target: "current",
        });
    }

    getEventTypeLabel(eventType) {
        if (!eventType) return "";
        // Convert snake_case to Title Case
        return eventType
            .split("_")
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }
}
