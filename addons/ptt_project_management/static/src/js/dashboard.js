/** @odoo-module */
/**
 * PTT Project Dashboard - Owl Component v2.3.0
 *
 * Focused Layout:
 * - 4 KPI cards (My Tasks, My Projects, Overdue, Due This Week)
 * - My Projects list with customer, task count, status
 * - My Tasks list with deadline and priority
 * - 2 charts (Tasks by Stage, Task Deadlines)
 */

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";

export class PTTProjectDashboard extends Component {
    setup() {
        // Services
        this.action = useService("action");
        this.notification = useService("notification");

        // Chart canvas refs (only 2 charts now)
        this.taskDeadlineChart = useRef("taskDeadlineChart");
        this.taskStagesChart = useRef("taskStagesChart");

        // Filter refs
        this.customerRef = useRef("customerSelect");
        this.projectRef = useRef("projectSelect");

        // Reactive state
        this.state = useState({
            // KPI counts
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

            // Filter options
            customers: [],
            projects: [],

            // UI state
            loading: true,
            refreshing: false,
            error: null,
            activePeriod: '',
        });

        // Current filters
        this.currentFilters = {
            customer: null,
            project: null,
            start_date: null,
            end_date: null,
        };

        // Chart instances
        this.charts = {};
        
        // Auto-polling (2 min)
        this.pollInterval = null;
        this.POLL_INTERVAL_MS = 120000;

        // Lifecycle
        onWillStart(async () => {
            try {
                await loadBundle("web.chartjs_lib");
                await this.loadInitialData();
            } catch (error) {
                console.error("PTT Dashboard: Failed to initialize", error);
                this.state.error = "Failed to load dashboard. Please refresh the page.";
            }
        });

        onMounted(() => {
            this.renderCharts();
            this.pollInterval = setInterval(() => this.refreshDashboard(true), this.POLL_INTERVAL_MS);
        });
        
        onWillUnmount(() => {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }
        });
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async loadInitialData() {
        try {
            const [kpis, myProjects, myTasks, filters] = await Promise.all([
                rpc('/ptt/dashboard/kpis'),
                rpc('/ptt/dashboard/my-projects', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/my-tasks', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/filter'),
            ]);

            // KPIs
            this.state.myTasks = kpis.my_tasks || 0;
            this.state.myTasksIds = kpis.my_tasks_ids || [];
            this.state.myProjects = kpis.my_projects || 0;
            this.state.myProjectsIds = kpis.my_projects_ids || [];
            this.state.myOverdueTasks = kpis.my_overdue_tasks || 0;
            this.state.myOverdueTasksIds = kpis.my_overdue_tasks_ids || [];
            this.state.dueThisWeek = kpis.due_this_week || 0;
            this.state.dueThisWeekIds = kpis.due_this_week_ids || [];

            // My Projects list
            this.state.myProjectsList = myProjects.projects || [];
            this.state.projectPage = myProjects.page || 1;
            this.state.projectPages = myProjects.pages || 1;

            // My Tasks list
            this.state.myTasksList = myTasks.tasks || [];
            this.state.taskPage = myTasks.page || 1;
            this.state.taskPages = myTasks.pages || 1;

            // Filters
            this.state.customers = filters.customers || [];
            this.state.projects = filters.projects || [];

            this.state.loading = false;
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.state.error = "Failed to load data. Please refresh.";
            this.state.loading = false;
        }
    }

    getFilterParams() {
        return {
            customer: this.currentFilters.customer || '',
            project: this.currentFilters.project || '',
            start_date: this.currentFilters.start_date || '',
            end_date: this.currentFilters.end_date || '',
        };
    }

    // =========================================================================
    // CHARTS (only 2 now)
    // =========================================================================

    isDarkMode() {
        return document.documentElement.classList.contains('o_dark') || 
               document.body.classList.contains('o_dark');
    }

    async renderCharts() {
        // Destroy existing
        Object.values(this.charts).forEach(c => c && c.destroy());

        const isDark = this.isDarkMode();
        const textColor = isDark ? '#e5e7eb' : '#374151';
        const gridColor = isDark ? '#374151' : '#e5e7eb';

        const filterParams = this.getFilterParams();
        const [stagesData, deadlineData] = await Promise.all([
            rpc('/ptt/dashboard/task-stages-chart', { filters: filterParams }),
            rpc('/ptt/dashboard/task-deadline-chart', { filters: filterParams }),
        ]);

        // Tasks by Stage (doughnut)
        if (this.taskStagesChart.el) {
            this.charts.stages = new Chart(this.taskStagesChart.el, {
                type: 'doughnut',
                data: {
                    labels: stagesData.labels || [],
                    datasets: [{
                        data: stagesData.data || [],
                        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '50%',
                    plugins: {
                        legend: { 
                            position: 'right',
                            labels: { color: textColor, padding: 12, font: { size: 11 } }
                        }
                    }
                }
            });
        }

        // Task Deadlines (pie)
        if (this.taskDeadlineChart.el) {
            this.charts.deadline = new Chart(this.taskDeadlineChart.el, {
                type: 'pie',
                data: {
                    labels: deadlineData.labels || ['Overdue', 'Today', 'Upcoming'],
                    datasets: [{
                        data: deadlineData.data || [0, 0, 0],
                        backgroundColor: ['#ef4444', '#f59e0b', '#22c55e'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'right',
                            labels: { color: textColor, padding: 12, font: { size: 11 } }
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
            if (!silent) {
                this.notification.add(_t("Dashboard refreshed"), { type: "success" });
            }
        } catch (error) {
            console.error('Refresh error:', error);
            if (!silent) {
                this.notification.add(_t("Failed to refresh"), { type: "danger" });
            }
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
                const dayOfWeek = today.getDay();
                const weekStart = new Date(today);
                weekStart.setDate(today.getDate() - dayOfWeek);
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
        this.currentFilters.customer = this.customerRef.el?.value || null;
        this.currentFilters.project = this.projectRef.el?.value || null;

        const params = this.getFilterParams();

        const [kpis, myProjects, myTasks] = await Promise.all([
            rpc('/ptt/dashboard/kpis', { filters: params }),
            rpc('/ptt/dashboard/my-projects', { page: 1, limit: 5, filters: params }),
            rpc('/ptt/dashboard/my-tasks', { page: 1, limit: 5, filters: params }),
        ]);

        // Update KPIs
        this.state.myTasks = kpis.my_tasks || 0;
        this.state.myTasksIds = kpis.my_tasks_ids || [];
        this.state.myProjects = kpis.my_projects || 0;
        this.state.myProjectsIds = kpis.my_projects_ids || [];
        this.state.myOverdueTasks = kpis.my_overdue_tasks || 0;
        this.state.myOverdueTasksIds = kpis.my_overdue_tasks_ids || [];
        this.state.dueThisWeek = kpis.due_this_week || 0;
        this.state.dueThisWeekIds = kpis.due_this_week_ids || [];

        // Update lists
        this.state.myProjectsList = myProjects.projects || [];
        this.state.projectPage = myProjects.page || 1;
        this.state.projectPages = myProjects.pages || 1;
        this.state.myTasksList = myTasks.tasks || [];
        this.state.taskPage = myTasks.page || 1;
        this.state.taskPages = myTasks.pages || 1;

        await this.renderCharts();
    }

    // =========================================================================
    // PAGINATION - Projects
    // =========================================================================

    async prevProjectPage() {
        if (this.state.projectPage > 1) {
            const data = await rpc('/ptt/dashboard/my-projects', {
                page: this.state.projectPage - 1,
                limit: 5,
                filters: this.getFilterParams()
            });
            this.state.myProjectsList = data.projects || [];
            this.state.projectPage = data.page;
            this.state.projectPages = data.pages;
        }
    }

    async nextProjectPage() {
        if (this.state.projectPage < this.state.projectPages) {
            const data = await rpc('/ptt/dashboard/my-projects', {
                page: this.state.projectPage + 1,
                limit: 5,
                filters: this.getFilterParams()
            });
            this.state.myProjectsList = data.projects || [];
            this.state.projectPage = data.page;
            this.state.projectPages = data.pages;
        }
    }

    // =========================================================================
    // PAGINATION - Tasks
    // =========================================================================

    async prevTaskPage() {
        if (this.state.taskPage > 1) {
            const data = await rpc('/ptt/dashboard/my-tasks', {
                page: this.state.taskPage - 1,
                limit: 5,
                filters: this.getFilterParams()
            });
            this.state.myTasksList = data.tasks || [];
            this.state.taskPage = data.page;
            this.state.taskPages = data.pages;
        }
    }

    async nextTaskPage() {
        if (this.state.taskPage < this.state.taskPages) {
            const data = await rpc('/ptt/dashboard/my-tasks', {
                page: this.state.taskPage + 1,
                limit: 5,
                filters: this.getFilterParams()
            });
            this.state.myTasksList = data.tasks || [];
            this.state.taskPage = data.page;
            this.state.taskPages = data.pages;
        }
    }

    // =========================================================================
    // DRILL-DOWN ACTIONS
    // =========================================================================

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
}

PTTProjectDashboard.template = "ptt_project_management.Dashboard";

registry.category("actions").add("ptt_project_dashboard", PTTProjectDashboard);
