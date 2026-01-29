/** @odoo-module */
/**
 * PTT Project Dashboard - Owl Component v2.5.0
 *
 * Layout:
 * 1. Event Calendar (top)
 * 2. 4 KPI cards
 * 3. My Tasks list
 * 4. Two donut charts (Projects + Tasks by Stage)
 */

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";

export class PTTProjectDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.notification = useService("notification");

        // Chart refs
        this.taskStagesChart = useRef("taskStagesChart");
        this.salesByRepChart = useRef("salesByRepChart");

        // Filter refs
        this.userRef = useRef("userSelect");
        this.projectRef = useRef("projectSelect");

        // Reactive state
        this.state = useState({
            // KPIs
            totalRevenue: '0',
            confirmedSOIds: [],
            myTasks: 0,
            myTasksIds: [],
            myProjects: 0,
            myProjectsIds: [],
            myOverdueTasks: 0,
            myOverdueTasksIds: [],
            dueThisWeek: 0,
            dueThisWeekIds: [],

            // My Projects list
            myProjectsList: [],
            projectPage: 1,
            projectPages: 1,

            // My Tasks list
            myTasksList: [],
            taskPage: 1,
            taskPages: 1,

            // Upcoming Events (from CRM + Projects)
            upcomingEvents: [],
            calendarDays: [],
            calendarTitle: '',
            calendarMonth: new Date().getMonth(),
            calendarYear: new Date().getFullYear(),

            // Filters
            users: [],
            projects: [],

            // UI
            loading: true,
            refreshing: false,
            error: null,
            activePeriod: '',
        });

        this.currentFilters = {
            user: null,
            project: null,
            start_date: null,
            end_date: null,
        };

        this.charts = {};
        this.pollInterval = null;
        this.POLL_INTERVAL_MS = 120000;

        onWillStart(async () => {
            try {
                await loadBundle("web.chartjs_lib");
                await this.loadInitialData();
            } catch (error) {
                console.error("Dashboard init error:", error);
                this.state.error = "Failed to load dashboard.";
            }
        });

        onMounted(() => {
            this.renderCharts();
            this.pollInterval = setInterval(() => this.refreshDashboard(true), this.POLL_INTERVAL_MS);
        });
        
        onWillUnmount(() => {
            if (this.pollInterval) clearInterval(this.pollInterval);
        });
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async loadInitialData() {
        try {
            const [kpis, salesKpis, myProjects, myTasks, events, filters] = await Promise.all([
                rpc('/ptt/dashboard/kpis'),
                rpc('/ptt/dashboard/sales-kpis'),
                rpc('/ptt/dashboard/my-projects', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/my-tasks', { page: 1, limit: 8 }),
                rpc('/ptt/dashboard/events'),
                rpc('/ptt/dashboard/filter'),
            ]);

            // Sales KPIs
            this.state.totalRevenue = salesKpis.total_revenue || '0';
            this.state.confirmedSOIds = salesKpis.confirmed_so_ids || [];

            // KPIs
            this.state.myTasks = kpis.my_tasks || 0;
            this.state.myTasksIds = kpis.my_tasks_ids || [];
            this.state.myProjects = kpis.my_projects || 0;
            this.state.myProjectsIds = kpis.my_projects_ids || [];
            this.state.myOverdueTasks = kpis.my_overdue_tasks || 0;
            this.state.myOverdueTasksIds = kpis.my_overdue_tasks_ids || [];
            this.state.dueThisWeek = kpis.due_this_week || 0;
            this.state.dueThisWeekIds = kpis.due_this_week_ids || [];

            // Lists
            this.state.myProjectsList = myProjects.projects || [];
            this.state.projectPage = myProjects.page || 1;
            this.state.projectPages = myProjects.pages || 1;
            this.state.myTasksList = myTasks.tasks || [];
            this.state.taskPage = myTasks.page || 1;
            this.state.taskPages = myTasks.pages || 1;

            // Events
            this.state.upcomingEvents = events.events || [];
            this.buildCalendarDays();

            // Filters
            this.state.users = filters.users || [];
            this.state.projects = filters.projects || [];

            this.state.loading = false;
        } catch (error) {
            console.error('Load error:', error);
            this.state.error = "Failed to load data.";
            this.state.loading = false;
        }
    }

    getFilterParams() {
        return {
            user: this.currentFilters.user || '',
            project: this.currentFilters.project || '',
            start_date: this.currentFilters.start_date || '',
            end_date: this.currentFilters.end_date || '',
        };
    }

    buildCalendarDays() {
        const year = this.state.calendarYear;
        const month = this.state.calendarMonth;
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'];
        
        // Set calendar title
        this.state.calendarTitle = `${monthNames[month]} ${year}`;
        
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // First day of the month
        const firstDay = new Date(year, month, 1);
        // Last day of the month
        const lastDay = new Date(year, month + 1, 0);
        
        // Start from Sunday of the week containing the 1st
        const startDate = new Date(firstDay);
        startDate.setDate(firstDay.getDate() - firstDay.getDay());
        
        // End on Saturday of the week containing the last day
        const endDate = new Date(lastDay);
        endDate.setDate(lastDay.getDate() + (6 - lastDay.getDay()));
        
        const days = [];
        const currentDate = new Date(startDate);
        
        while (currentDate <= endDate) {
            const dateStr = currentDate.toISOString().split('T')[0];
            const isCurrentMonth = currentDate.getMonth() === month;
            
            // Find events for this day
            const dayEvents = this.state.upcomingEvents.filter(e => e.date === dateStr);
            
            days.push({
                date: dateStr,
                dayNum: currentDate.getDate(),
                isToday: currentDate.getTime() === today.getTime(),
                isOtherMonth: !isCurrentMonth,
                events: dayEvents,
            });
            
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        this.state.calendarDays = days;
    }

    prevMonth() {
        if (this.state.calendarMonth === 0) {
            this.state.calendarMonth = 11;
            this.state.calendarYear--;
        } else {
            this.state.calendarMonth--;
        }
        this.loadEventsForMonth();
    }

    nextMonth() {
        if (this.state.calendarMonth === 11) {
            this.state.calendarMonth = 0;
            this.state.calendarYear++;
        } else {
            this.state.calendarMonth++;
        }
        this.loadEventsForMonth();
    }

    goToToday() {
        const today = new Date();
        this.state.calendarMonth = today.getMonth();
        this.state.calendarYear = today.getFullYear();
        this.loadEventsForMonth();
    }

    async loadEventsForMonth() {
        const year = this.state.calendarYear;
        const month = this.state.calendarMonth;
        
        // Get first and last day of displayed calendar (including overflow days)
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(firstDay.getDate() - firstDay.getDay());
        const endDate = new Date(lastDay);
        endDate.setDate(lastDay.getDate() + (6 - lastDay.getDay()));
        
        const events = await rpc('/ptt/dashboard/events', {
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDate.toISOString().split('T')[0],
        });
        
        this.state.upcomingEvents = events.events || [];
        this.buildCalendarDays();
    }

    // =========================================================================
    // CHARTS
    // =========================================================================

    isDarkMode() {
        return document.documentElement.classList.contains('o_dark') || 
               document.body.classList.contains('o_dark');
    }

    async renderCharts() {
        // Destroy existing charts
        if (this.charts.stages) this.charts.stages.destroy();
        if (this.charts.salesByRep) this.charts.salesByRep.destroy();

        const isDark = this.isDarkMode();
        const textColor = isDark ? '#e5e7eb' : '#374151';
        const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';

        // Fetch data for charts
        const [stagesData, salesByRepData] = await Promise.all([
            rpc('/ptt/dashboard/task-stages-chart', { filters: this.getFilterParams() }),
            rpc('/ptt/dashboard/sales-by-rep', { filters: this.getFilterParams() }),
        ]);

        // Tasks by Stage donut
        if (this.taskStagesChart.el && stagesData.data?.length > 0) {
            this.charts.stages = new Chart(this.taskStagesChart.el, {
                type: 'doughnut',
                data: {
                    labels: stagesData.labels || [],
                    datasets: [{
                        data: stagesData.data || [],
                        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '55%',
                    plugins: {
                        legend: { 
                            position: 'bottom',
                            labels: { color: textColor, padding: 8, font: { size: 10 } }
                        }
                    }
                }
            });
        }

        // Sales by Rep bar chart
        if (this.salesByRepChart.el && salesByRepData.data?.length > 0) {
            this.charts.salesByRep = new Chart(this.salesByRepChart.el, {
                type: 'bar',
                data: {
                    labels: salesByRepData.labels || [],
                    datasets: [{
                        label: 'Sales ($)',
                        data: salesByRepData.data || [],
                        backgroundColor: '#22c55e',
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: { color: textColor, font: { size: 10 } },
                            grid: { color: gridColor }
                        },
                        y: {
                            ticks: { color: textColor, font: { size: 10 } },
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    }

    // =========================================================================
    // REFRESH
    // =========================================================================

    async refreshDashboard(silent = false) {
        if (!silent) this.state.refreshing = true;
        try {
            await this.loadInitialData();
            await this.renderCharts();
            if (!silent) this.notification.add(_t("Refreshed"), { type: "success" });
        } catch (e) {
            if (!silent) this.notification.add(_t("Refresh failed"), { type: "danger" });
        } finally {
            this.state.refreshing = false;
        }
    }

    // =========================================================================
    // DATE PERIOD
    // =========================================================================

    getDateRangeFromPreset(preset) {
        const today = new Date();
        const year = today.getFullYear();
        let startDate = null, endDate = null;

        switch (preset) {
            case 'today':
                startDate = endDate = today.toISOString().split('T')[0];
                break;
            case 'week': {
                const weekStart = new Date(today);
                weekStart.setDate(today.getDate() - today.getDay());
                const weekEnd = new Date(weekStart);
                weekEnd.setDate(weekStart.getDate() + 6);
                startDate = weekStart.toISOString().split('T')[0];
                endDate = weekEnd.toISOString().split('T')[0];
                break;
            }
            case 'month':
                startDate = new Date(year, today.getMonth(), 1).toISOString().split('T')[0];
                endDate = new Date(year, today.getMonth() + 1, 0).toISOString().split('T')[0];
                break;
        }
        return { startDate, endDate };
    }

    async setDatePeriod(period) {
        this.state.activePeriod = period;
        const { startDate, endDate } = this.getDateRangeFromPreset(period);
        this.currentFilters.start_date = startDate;
        this.currentFilters.end_date = endDate;
        await this.applyFilters();
    }

    // =========================================================================
    // FILTERS
    // =========================================================================

    async applyFilters() {
        this.currentFilters.user = this.userRef.el?.value || null;
        this.currentFilters.project = this.projectRef.el?.value || null;

        const params = this.getFilterParams();

        const [kpis, myProjects, myTasks] = await Promise.all([
            rpc('/ptt/dashboard/kpis', { filters: params }),
            rpc('/ptt/dashboard/my-projects', { page: 1, limit: 5, filters: params }),
            rpc('/ptt/dashboard/my-tasks', { page: 1, limit: 8, filters: params }),
        ]);

        this.state.myTasks = kpis.my_tasks || 0;
        this.state.myTasksIds = kpis.my_tasks_ids || [];
        this.state.myProjects = kpis.my_projects || 0;
        this.state.myProjectsIds = kpis.my_projects_ids || [];
        this.state.myOverdueTasks = kpis.my_overdue_tasks || 0;
        this.state.myOverdueTasksIds = kpis.my_overdue_tasks_ids || [];
        this.state.dueThisWeek = kpis.due_this_week || 0;
        this.state.dueThisWeekIds = kpis.due_this_week_ids || [];

        this.state.myProjectsList = myProjects.projects || [];
        this.state.projectPage = 1;
        this.state.projectPages = myProjects.pages || 1;
        this.state.myTasksList = myTasks.tasks || [];
        this.state.taskPage = 1;
        this.state.taskPages = myTasks.pages || 1;

        await this.renderCharts();
    }

    // =========================================================================
    // PAGINATION
    // =========================================================================

    async prevProjectPage() {
        if (this.state.projectPage > 1) {
            const data = await rpc('/ptt/dashboard/my-projects', {
                page: this.state.projectPage - 1, limit: 5, filters: this.getFilterParams()
            });
            this.state.myProjectsList = data.projects || [];
            this.state.projectPage = data.page;
            this.state.projectPages = data.pages;
        }
    }

    async nextProjectPage() {
        if (this.state.projectPage < this.state.projectPages) {
            const data = await rpc('/ptt/dashboard/my-projects', {
                page: this.state.projectPage + 1, limit: 5, filters: this.getFilterParams()
            });
            this.state.myProjectsList = data.projects || [];
            this.state.projectPage = data.page;
            this.state.projectPages = data.pages;
        }
    }

    async prevTaskPage() {
        if (this.state.taskPage > 1) {
            const data = await rpc('/ptt/dashboard/my-tasks', {
                page: this.state.taskPage - 1, limit: 8, filters: this.getFilterParams()
            });
            this.state.myTasksList = data.tasks || [];
            this.state.taskPage = data.page;
            this.state.taskPages = data.pages;
        }
    }

    async nextTaskPage() {
        if (this.state.taskPage < this.state.taskPages) {
            const data = await rpc('/ptt/dashboard/my-tasks', {
                page: this.state.taskPage + 1, limit: 8, filters: this.getFilterParams()
            });
            this.state.myTasksList = data.tasks || [];
            this.state.taskPage = data.page;
            this.state.taskPages = data.pages;
        }
    }

    // =========================================================================
    // DRILL-DOWN ACTIONS
    // =========================================================================

    openConfirmedSOs(ev) {
        ev?.stopPropagation();
        this.action.doAction({
            name: _t("Confirmed Sales Orders"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            domain: [['id', 'in', this.state.confirmedSOIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openMyTasks(ev) {
        ev?.stopPropagation();
        this.action.doAction({
            name: _t("My Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.myTasksIds]],
            view_mode: 'list,kanban,form',
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            target: 'current',
        });
    }

    openMyProjects(ev) {
        ev?.stopPropagation();
        this.action.doAction({
            name: _t("My Projects"),
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            domain: [['id', 'in', this.state.myProjectsIds]],
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openMyOverdueTasks(ev) {
        ev?.stopPropagation();
        this.action.doAction({
            name: _t("Overdue Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.myOverdueTasksIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openDueThisWeek(ev) {
        ev?.stopPropagation();
        this.action.doAction({
            name: _t("Due This Week"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.dueThisWeekIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    viewProject(projectId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            res_id: projectId,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
        });
    }

    viewTask(taskId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            res_id: taskId,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
        });
    }

    viewEvent(event) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: event.model,
            res_id: event.id,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

PTTProjectDashboard.template = "ptt_project_management.Dashboard";

registry.category("actions").add("ptt_project_dashboard", PTTProjectDashboard);
