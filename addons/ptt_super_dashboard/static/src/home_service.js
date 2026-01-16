/** @odoo-module **/

import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";

/**
 * PTT Home Service
 * 
 * Frontend service that communicates with ptt.home.data backend
 * to fetch aggregated data from standard Odoo models.
 */
export const homeService = {
    dependencies: ["orm"],
    
    start(env, { orm }) {
        // Reactive state for caching
        const state = reactive({
            homeData: null,
            salesData: null,
            calendarData: null,
            lastFetch: null,
            loading: false,
        });
        
        const CACHE_DURATION = 60000; // 1 minute cache
        
        return {
            state,
            
            /**
             * Get complete home summary data
             */
            async getHomeSummary(forceRefresh = false) {
                const now = Date.now();
                if (!forceRefresh && state.homeData && state.lastFetch && (now - state.lastFetch < CACHE_DURATION)) {
                    return state.homeData;
                }
                
                state.loading = true;
                try {
                    const data = await orm.call("ptt.home.data", "get_home_summary", []);
                    state.homeData = data;
                    state.lastFetch = now;
                    return data;
                } finally {
                    state.loading = false;
                }
            },
            
            /**
             * Get My Work tasks categorized by due date
             */
            async getMyWorkTasks() {
                return await orm.call("ptt.home.data", "get_my_work_tasks", []);
            },
            
            /**
             * Get assigned tasks with hierarchy info
             */
            async getAssignedTasks() {
                return await orm.call("ptt.home.data", "get_assigned_tasks", []);
            },
            
            /**
             * Get assigned comments/mentions
             */
            async getAssignedComments(limit = 20) {
                return await orm.call("ptt.home.data", "get_assigned_comments", [limit]);
            },
            
            /**
             * Get agenda events for the next N days
             */
            async getAgendaEvents(days = 14) {
                return await orm.call("ptt.home.data", "get_agenda_events", [days]);
            },
            
            /**
             * Get event calendar data with status colors
             */
            async getEventCalendarData(startDate = null, endDate = null) {
                return await orm.call("ptt.home.data", "get_event_calendar_data", [startDate, endDate]);
            },
            
            /**
             * Get sales KPIs
             */
            async getSalesKpis() {
                return await orm.call("ptt.home.data", "get_sales_kpis", []);
            },
            
            /**
             * Get personal todos
             */
            async getPersonalTodos() {
                return await orm.call("ptt.personal.todo", "get_my_todos", []);
            },
            
            /**
             * Get comprehensive dashboard tasks (all sections)
             */
            async getDashboardTasks() {
                return await orm.call("ptt.home.data", "get_dashboard_tasks", []);
            },
            
            /**
             * Get task leaderboard by user
             */
            async getTaskLeaderboard() {
                return await orm.call("ptt.home.data", "get_task_leaderboard", []);
            },
            
            /**
             * Create a new personal todo
             */
            async createPersonalTodo(name, dueDate = null, priority = "1") {
                const vals = { name, priority };
                if (dueDate) {
                    vals.due_date = dueDate;
                }
                // orm.create returns an array of IDs, we want the first one
                const ids = await orm.create("ptt.personal.todo", [vals]);
                this.invalidateCache();
                return ids[0];
            },
            
            /**
             * Toggle personal todo done status
             */
            async togglePersonalTodo(id) {
                await orm.call("ptt.personal.todo", "action_toggle_done", [[id]]);
                this.invalidateCache();
            },
            
            /**
             * Delete a personal todo
             */
            async deletePersonalTodo(id) {
                await orm.unlink("ptt.personal.todo", [id]);
                this.invalidateCache();
            },
            
            /**
             * Invalidate cache to force refresh
             */
            invalidateCache() {
                state.homeData = null;
                state.salesData = null;
                state.calendarData = null;
                state.lastFetch = null;
            },
        };
    },
};

registry.category("services").add("ptt_home", homeService);

