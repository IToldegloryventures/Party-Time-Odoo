/** @odoo-module */
/**
 * PTT Project Dashboard - Owl Component
 *
 * Based on:
 * - Odoo 19 Official Tutorial: https://www.odoo.com/documentation/19.0/developer/tutorials/discover_js_framework/02_build_a_dashboard.html
 * - Cybrosys project_dashboard_odoo/static/src/js/dashboard.js
 *
 * Key patterns:
 * - All hooks (useState, useRef, onWillStart, onMounted) called in setup()
 * - useService("action") for drill-down navigation
 * - rpc() for JSON-RPC calls to controllers
 * - Chart.js for visualizations
 */

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class PTTProjectDashboard extends Component {
    /**
     * Setup method - all hooks must be called here per Odoo 19 patterns.
     */
    setup() {
        // Services
        this.action = useService("action");

        // Refs for chart canvases
        this.taskDeadlineChart = useRef("taskDeadlineChart");
        this.taskStagesChart = useRef("taskStagesChart");
        this.taskProjectChart = useRef("taskProjectChart");
        this.priorityChart = useRef("priorityChart");

        // Refs for filter inputs
        this.startDateRef = useRef("startDate");
        this.endDateRef = useRef("endDate");
        this.managerRef = useRef("managerSelect");
        this.customerRef = useRef("customerSelect");
        this.projectRef = useRef("projectSelect");

        // Reactive state
        this.state = useState({
            // KPI Tiles
            myTasks: 0,
            myTasksIds: [],
            totalProjects: 0,
            totalProjectsIds: [],
            activeTasks: 0,
            activeTasksIds: [],
            myOverdueTasks: 0,
            myOverdueTasksIds: [],
            overdueTasks: 0,
            overdueTasksIds: [],
            todayTasks: 0,
            todayTasksIds: [],
            isManager: false,
            userName: '',

            // Task table
            tasks: [],
            taskPage: 1,
            taskPages: 1,

            // Activities table
            activities: [],
            activityPage: 1,
            activityPages: 1,

            // Filter options
            managers: [],
            customers: [],
            projects: [],

            // Loading state
            loading: true,
        });

        // Chart instances (need to destroy before re-render)
        this.charts = {};

        // Lifecycle hooks
        onWillStart(async () => {
            await this.loadInitialData();
        });

        onMounted(() => {
            this.renderAllCharts();
        });
    }

    /**
     * Load all initial data from controllers.
     */
    async loadInitialData() {
        try {
            // Fetch all data in parallel
            const [tiles, tasks, activities, filters] = await Promise.all([
                rpc('/ptt/dashboard/tiles'),
                rpc('/ptt/dashboard/tasks', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/activities', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/filter'),
            ]);

            // Update state with tiles data
            this.state.myTasks = tiles.my_tasks;
            this.state.myTasksIds = tiles.my_tasks_ids;
            this.state.totalProjects = tiles.total_projects;
            this.state.totalProjectsIds = tiles.total_projects_ids;
            this.state.activeTasks = tiles.active_tasks;
            this.state.activeTasksIds = tiles.active_tasks_ids;
            this.state.myOverdueTasks = tiles.my_overdue_tasks;
            this.state.myOverdueTasksIds = tiles.my_overdue_tasks_ids;
            this.state.overdueTasks = tiles.overdue_tasks;
            this.state.overdueTasksIds = tiles.overdue_tasks_ids;
            this.state.todayTasks = tiles.today_tasks;
            this.state.todayTasksIds = tiles.today_tasks_ids;
            this.state.isManager = tiles.is_manager;
            this.state.userName = tiles.user_name;

            // Update state with tasks
            this.state.tasks = tasks.tasks;
            this.state.taskPage = tasks.page;
            this.state.taskPages = tasks.pages;

            // Update state with activities
            this.state.activities = activities.activities;
            this.state.activityPage = activities.page;
            this.state.activityPages = activities.pages;

            // Update filter options
            this.state.managers = filters.managers;
            this.state.customers = filters.customers;
            this.state.projects = filters.projects;

            this.state.loading = false;
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.state.loading = false;
        }
    }

    /**
     * Render all Chart.js charts.
     */
    async renderAllCharts() {
        // Destroy existing charts first
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });

        // Fetch chart data
        const [deadlineData, stagesData, projectData, priorityData] = await Promise.all([
            rpc('/ptt/dashboard/task-deadline-chart'),
            rpc('/ptt/dashboard/task-stages-chart'),
            rpc('/ptt/dashboard/task-project-chart'),
            rpc('/ptt/dashboard/priority-chart'),
        ]);

        // Render Task Deadline Pie Chart
        if (this.taskDeadlineChart.el) {
            this.charts.deadline = new Chart(this.taskDeadlineChart.el, {
                type: 'pie',
                data: {
                    labels: deadlineData.labels,
                    datasets: [{
                        data: deadlineData.data,
                        backgroundColor: deadlineData.colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' }
                    }
                }
            });
        }

        // Render Task By Stages Doughnut Chart
        if (this.taskStagesChart.el) {
            this.charts.stages = new Chart(this.taskStagesChart.el, {
                type: 'doughnut',
                data: {
                    labels: stagesData.labels,
                    datasets: [{
                        data: stagesData.data,
                        backgroundColor: stagesData.colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }

        // Render Task By Project Bar Chart
        if (this.taskProjectChart.el) {
            this.charts.project = new Chart(this.taskProjectChart.el, {
                type: 'bar',
                data: {
                    labels: projectData.labels,
                    datasets: [{
                        label: 'Total Tasks',
                        data: projectData.data,
                        backgroundColor: projectData.colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        // Render Priority Wise Bar Chart
        if (this.priorityChart.el) {
            this.charts.priority = new Chart(this.priorityChart.el, {
                type: 'bar',
                data: {
                    labels: priorityData.labels,
                    datasets: [{
                        label: 'Priority',
                        data: priorityData.data,
                        backgroundColor: priorityData.colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    }

    // =========================================================================
    // DRILL-DOWN ACTIONS (using action.doAction)
    // =========================================================================

    openMyTasks(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.action.doAction({
            name: _t("My Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.myTasksIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openTotalProjects(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.action.doAction({
            name: _t("Projects"),
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            domain: [['id', 'in', this.state.totalProjectsIds]],
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openActiveTasks(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.action.doAction({
            name: _t("Active Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.activeTasksIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openMyOverdueTasks(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.action.doAction({
            name: _t("My Overdue Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.myOverdueTasksIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openOverdueTasks(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.action.doAction({
            name: _t("Overdue Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.overdueTasksIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
        });
    }

    openTodayTasks(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.action.doAction({
            name: _t("Today's Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [['id', 'in', this.state.todayTasksIds]],
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
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

    viewActivity(resModel, resId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: resModel,
            res_id: resId,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
        });
    }

    // =========================================================================
    // PAGINATION
    // =========================================================================

    async prevTaskPage() {
        if (this.state.taskPage > 1) {
            const data = await rpc('/ptt/dashboard/tasks', {
                page: this.state.taskPage - 1,
                limit: 5
            });
            this.state.tasks = data.tasks;
            this.state.taskPage = data.page;
            this.state.taskPages = data.pages;
        }
    }

    async nextTaskPage() {
        if (this.state.taskPage < this.state.taskPages) {
            const data = await rpc('/ptt/dashboard/tasks', {
                page: this.state.taskPage + 1,
                limit: 5
            });
            this.state.tasks = data.tasks;
            this.state.taskPage = data.page;
            this.state.taskPages = data.pages;
        }
    }

    async prevActivityPage() {
        if (this.state.activityPage > 1) {
            const data = await rpc('/ptt/dashboard/activities', {
                page: this.state.activityPage - 1,
                limit: 5
            });
            this.state.activities = data.activities;
            this.state.activityPage = data.page;
            this.state.activityPages = data.pages;
        }
    }

    async nextActivityPage() {
        if (this.state.activityPage < this.state.activityPages) {
            const data = await rpc('/ptt/dashboard/activities', {
                page: this.state.activityPage + 1,
                limit: 5
            });
            this.state.activities = data.activities;
            this.state.activityPage = data.page;
            this.state.activityPages = data.pages;
        }
    }

    // =========================================================================
    // FILTERS
    // =========================================================================

    async applyFilters() {
        const startDate = this.startDateRef.el ? this.startDateRef.el.value : null;
        const endDate = this.endDateRef.el ? this.endDateRef.el.value : null;
        const managerId = this.managerRef.el ? this.managerRef.el.value : null;
        const customerId = this.customerRef.el ? this.customerRef.el.value : null;
        const projectId = this.projectRef.el ? this.projectRef.el.value : null;

        const data = await rpc('/ptt/dashboard/filter-apply', {
            data: {
                start_date: startDate || 'null',
                end_date: endDate || 'null',
                manager: managerId || 'null',
                customer: customerId || 'null',
                project: projectId || 'null',
            }
        });

        // Update KPI tiles
        this.state.myTasks = data.my_tasks;
        this.state.myTasksIds = data.my_tasks_ids;
        this.state.totalProjects = data.total_projects;
        this.state.totalProjectsIds = data.total_projects_ids;
        this.state.activeTasks = data.active_tasks;
        this.state.activeTasksIds = data.active_tasks_ids;
        this.state.myOverdueTasks = data.my_overdue_tasks;
        this.state.myOverdueTasksIds = data.my_overdue_tasks_ids;
        this.state.overdueTasks = data.overdue_tasks;
        this.state.overdueTasksIds = data.overdue_tasks_ids;
        this.state.todayTasks = data.today_tasks;
        this.state.todayTasksIds = data.today_tasks_ids;

        // Re-render charts
        await this.renderAllCharts();
    }

    async resetFilters() {
        // Reset filter inputs
        if (this.startDateRef.el) this.startDateRef.el.value = '';
        if (this.endDateRef.el) this.endDateRef.el.value = '';
        if (this.managerRef.el) this.managerRef.el.value = '';
        if (this.customerRef.el) this.customerRef.el.value = '';
        if (this.projectRef.el) this.projectRef.el.value = '';

        // Reload all data
        await this.loadInitialData();
        await this.renderAllCharts();
    }

    /**
     * Get greeting based on time of day.
     */
    getGreeting() {
        const hour = new Date().getHours();
        if (hour < 12) return _t("Good Morning");
        if (hour < 18) return _t("Good Afternoon");
        return _t("Good Evening");
    }
}

// Template assignment (required for Odoo 19)
PTTProjectDashboard.template = "ptt_project_management.Dashboard";

// Register as client action
registry.category("actions").add("ptt_project_dashboard", PTTProjectDashboard);
