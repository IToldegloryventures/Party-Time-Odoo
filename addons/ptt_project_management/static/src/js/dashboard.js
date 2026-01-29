/** @odoo-module */
/**
 * PTT Project Dashboard - Owl Component
 *
 * Matches the screenshot layout:
 * - Header with greeting, avatar, filters, and Print button
 * - 6 KPI tiles in 2 rows
 * - All Task table + Task Deadline pie chart
 * - Task By Stages doughnut + Task By Project bar
 * - Activities table + Priority bar chart
 *
 * NO Timesheet Hours (enterprise feature not included)
 *
 * Chart.js is loaded via loadBundle("web.chartjs_lib") - Odoo 19 best practice
 * This uses Odoo's bundled Chart.js instead of a CDN for Odoo.sh compatibility
 *
 * Enhanced Features (v2.1.0):
 * - Refresh button for manual data reload
 * - Auto-polling every 2 minutes
 * - Custom date range picker
 * - Fiscal quarter filters (Q1-Q4)
 * - Saved filter presets
 * - Quick task assignment from table
 * - Excel export functionality
 */

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";

export class PTTProjectDashboard extends Component {
    /**
     * Setup method - all hooks must be called here per Odoo 19 patterns.
     */
    setup() {
        // Services
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        // Refs for chart canvases
        this.taskDeadlineChart = useRef("taskDeadlineChart");
        this.taskStagesChart = useRef("taskStagesChart");
        this.taskProjectChart = useRef("taskProjectChart");
        this.priorityChart = useRef("priorityChart");

        // Refs for filter inputs
        this.userRef = useRef("userSelect");
        this.customerRef = useRef("customerSelect");
        this.projectRef = useRef("projectSelect");
        this.datePresetRef = useRef("datePreset");
        
        // Refs for custom date range inputs
        this.startDateRef = useRef("startDate");
        this.endDateRef = useRef("endDate");
        
        // Refs for saved presets
        this.presetSelectRef = useRef("presetSelect");

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
            userAvatar: '',

            // Task table
            tasks: [],
            taskPage: 1,
            taskPages: 1,

            // Activities table
            activities: [],
            activityPage: 1,
            activityPages: 1,

            // Filter options
            users: [],
            customers: [],
            projects: [],
            
            // Saved filter presets
            presets: [],
            currentPresetId: null,

            // Loading state
            loading: true,
            refreshing: false,
            
            // Error state (for initialization failures)
            error: null,
            
            // Available users for task assignment
            availableUsers: [],
            
            // Active date period pill
            activePeriod: '',
        });

        // Current filter state (used by all data fetches)
        this.currentFilters = {
            user: null,
            customer: null,
            project: null,
            start_date: null,
            end_date: null,
        };

        // Chart instances (need to destroy before re-render)
        this.charts = {};
        
        // Auto-polling interval (2 minutes = 120000ms)
        this.pollInterval = null;
        this.POLL_INTERVAL_MS = 120000;

        // Lifecycle hooks
        onWillStart(async () => {
            try {
                // Load Chart.js from Odoo's bundled library (Odoo.sh best practice)
                await loadBundle("web.chartjs_lib");
                await this.loadInitialData();
            } catch (error) {
                console.error("PTT Dashboard: Failed to initialize", error);
                this.state.error = "Failed to load dashboard. Please refresh the page.";
            }
        });

        onMounted(() => {
            this.renderAllCharts();
            
            // Start auto-polling every 2 minutes
            this.pollInterval = setInterval(() => {
                this.refreshDashboard(true); // silent refresh
            }, this.POLL_INTERVAL_MS);
        });
        
        onWillUnmount(() => {
            // Clean up polling interval to prevent memory leaks
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }
        });
    }

    /**
     * Load all initial data from controllers.
     */
    async loadInitialData() {
        try {
            // Fetch all data in parallel
            const [tiles, tasks, activities, filters, presets] = await Promise.all([
                rpc('/ptt/dashboard/tiles'),
                rpc('/ptt/dashboard/tasks', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/activities', { page: 1, limit: 5 }),
                rpc('/ptt/dashboard/filter'),
                rpc('/ptt/dashboard/presets'),
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
            this.state.userAvatar = tiles.user_avatar || '';

            // Update state with tasks
            this.state.tasks = tasks.tasks;
            this.state.taskPage = tasks.page;
            this.state.taskPages = tasks.pages;

            // Update state with activities
            this.state.activities = activities.activities;
            this.state.activityPage = activities.page;
            this.state.activityPages = activities.pages;

            // Update filter options
            this.state.users = filters.users || [];
            this.state.customers = filters.customers;
            this.state.projects = filters.projects;
            
            // Update saved presets and available users for assignment
            this.state.presets = presets.presets || [];
            this.state.availableUsers = filters.users || []; // Use user list as assignable users

            this.state.loading = false;
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.state.loading = false;
        }
    }

    /**
     * Get current filter parameters for RPC calls.
     */
    getFilterParams() {
        return {
            user: this.currentFilters.user || 'null',
            customer: this.currentFilters.customer || 'null',
            project: this.currentFilters.project || 'null',
            start_date: this.currentFilters.start_date || 'null',
            end_date: this.currentFilters.end_date || 'null',
        };
    }

    /**
     * Check if dark mode is active.
     */
    isDarkMode() {
        return document.documentElement.classList.contains('o_dark') || 
               document.body.classList.contains('o_dark') ||
               document.documentElement.classList.contains('dark');
    }
    
    /**
     * Get theme-aware colors for charts.
     */
    getChartColors() {
        const isDark = this.isDarkMode();
        return {
            textColor: isDark ? '#e5e7eb' : '#374151',
            gridColor: isDark ? '#374151' : '#e5e7eb',
            legendColor: isDark ? '#d1d5db' : '#4b5563',
        };
    }

    /**
     * Render all Chart.js charts with theme-aware colors.
     */
    async renderAllCharts() {
        // Destroy existing charts first
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });

        // Get theme colors
        const { textColor, gridColor, legendColor } = this.getChartColors();

        // Fetch chart data with current filters
        const filterParams = this.getFilterParams();
        const [deadlineData, stagesData, projectData, priorityData] = await Promise.all([
            rpc('/ptt/dashboard/task-deadline-chart', { filters: filterParams }),
            rpc('/ptt/dashboard/task-stages-chart', { filters: filterParams }),
            rpc('/ptt/dashboard/task-project-chart', { filters: filterParams }),
            rpc('/ptt/dashboard/priority-chart', { filters: filterParams }),
        ]);

        // Common legend config with theme colors
        const legendConfig = {
            labels: {
                color: legendColor,
                usePointStyle: true,
                pointStyle: 'rect',
                padding: 12,
                font: { size: 11 }
            }
        };

        // Render Task Deadline Pie Chart
        if (this.taskDeadlineChart.el) {
            this.charts.deadline = new Chart(this.taskDeadlineChart.el, {
                type: 'pie',
                data: {
                    labels: deadlineData.labels,
                    datasets: [{
                        data: deadlineData.data,
                        backgroundColor: ['#9ca3af', '#fbbf24', '#c4b5fd'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'right',
                            ...legendConfig
                        }
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
                        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '50%',
                    plugins: {
                        legend: { 
                            position: 'top',
                            ...legendConfig
                        }
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
                        label: 'Tasks',
                        data: projectData.data,
                        backgroundColor: '#86efac',
                        borderColor: '#22c55e',
                        borderWidth: 1,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'top',
                            align: 'end',
                            ...legendConfig
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: textColor },
                            grid: { display: false }
                        }
                    }
                }
            });
        }

        // Render Priority Bar Chart
        if (this.priorityChart.el) {
            this.charts.priority = new Chart(this.priorityChart.el, {
                type: 'bar',
                data: {
                    labels: priorityData.labels,
                    datasets: [{
                        label: 'Tasks',
                        data: priorityData.data,
                        backgroundColor: priorityData.colors || ['#93c5fd', '#fcd34d', '#f97316', '#ef4444'],
                        borderColor: ['#3b82f6', '#f59e0b', '#ea580c', '#dc2626'],
                        borderWidth: 1,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'top',
                            align: 'end',
                            ...legendConfig
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: textColor },
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    }

    // =========================================================================
    // REFRESH FUNCTIONALITY
    // =========================================================================

    /**
     * Refresh all dashboard data without full page reload.
     * @param {boolean} silent - If true, don't show loading indicator (for auto-polling)
     */
    async refreshDashboard(silent = false) {
        if (!silent) {
            this.state.refreshing = true;
        }
        
        try {
            await this.loadInitialData();
            await this.renderAllCharts();
            
            if (!silent) {
                this.notification.add(_t("Dashboard refreshed"), {
                    type: "success",
                    sticky: false,
                });
            }
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            if (!silent) {
                this.notification.add(_t("Failed to refresh dashboard"), {
                    type: "danger",
                    sticky: false,
                });
            }
        } finally {
            this.state.refreshing = false;
        }
    }

    // =========================================================================
    // PRINT FUNCTIONALITY
    // =========================================================================

    printDashboard() {
        window.print();
    }
    
    // =========================================================================
    // EXPORT FUNCTIONALITY
    // =========================================================================

    /**
     * Export dashboard data to Excel file.
     */
    async exportToExcel() {
        try {
            this.notification.add(_t("Preparing Excel export..."), {
                type: "info",
                sticky: false,
            });
            
            // Navigate to export URL which returns the file
            window.location.href = '/ptt/dashboard/export?' + new URLSearchParams({
                user: this.currentFilters.user || '',
                customer: this.currentFilters.customer || '',
                project: this.currentFilters.project || '',
                start_date: this.currentFilters.start_date || '',
                end_date: this.currentFilters.end_date || '',
            }).toString();
        } catch (error) {
            console.error('Error exporting dashboard:', error);
            this.notification.add(_t("Export failed"), {
                type: "danger",
                sticky: false,
            });
        }
    }

    // =========================================================================
    // CHART DOWNLOAD FUNCTIONALITY
    // =========================================================================

    /**
     * Download a chart as PNG image.
     * @param {string} chartKey - Key in this.charts object (deadline, stages, project, priority)
     * @param {string} filename - Base filename for download
     */
    downloadChart(chartKey, filename) {
        const chart = this.charts[chartKey];
        if (!chart) {
            console.warn(`Chart '${chartKey}' not found`);
            return;
        }

        // Get chart as base64 image
        const imageUrl = chart.toBase64Image('image/png', 1);
        
        // Create download link
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
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
                limit: 5,
                filters: this.getFilterParams()
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
                limit: 5,
                filters: this.getFilterParams()
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
                limit: 5,
                filters: this.getFilterParams()
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
                limit: 5,
                filters: this.getFilterParams()
            });
            this.state.activities = data.activities;
            this.state.activityPage = data.page;
            this.state.activityPages = data.pages;
        }
    }

    // =========================================================================
    // FILTERS
    // =========================================================================

    /**
     * Get date range based on preset selection.
     * Supports: today, week, month, year, quarters (q1-q4), last periods, and fiscal year.
     */
    getDateRangeFromPreset(preset) {
        const today = new Date();
        const year = today.getFullYear();
        let startDate = null;
        let endDate = null;

        switch (preset) {
            case 'today':
                startDate = today.toISOString().split('T')[0];
                endDate = startDate;
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
                
            case 'year':
                startDate = new Date(year, 0, 1).toISOString().split('T')[0];
                endDate = new Date(year, 11, 31).toISOString().split('T')[0];
                break;
                
            // Fiscal Quarters (Calendar Year: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec)
            case 'q1':
                startDate = new Date(year, 0, 1).toISOString().split('T')[0];
                endDate = new Date(year, 2, 31).toISOString().split('T')[0];
                break;
                
            case 'q2':
                startDate = new Date(year, 3, 1).toISOString().split('T')[0];
                endDate = new Date(year, 5, 30).toISOString().split('T')[0];
                break;
                
            case 'q3':
                startDate = new Date(year, 6, 1).toISOString().split('T')[0];
                endDate = new Date(year, 8, 30).toISOString().split('T')[0];
                break;
                
            case 'q4':
                startDate = new Date(year, 9, 1).toISOString().split('T')[0];
                endDate = new Date(year, 11, 31).toISOString().split('T')[0];
                break;
                
            // Last periods
            case 'last_week': {
                const lastWeekEnd = new Date(today);
                lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
                const lastWeekStart = new Date(lastWeekEnd);
                lastWeekStart.setDate(lastWeekEnd.getDate() - 6);
                startDate = lastWeekStart.toISOString().split('T')[0];
                endDate = lastWeekEnd.toISOString().split('T')[0];
                break;
            }
            
            case 'last_month':
                startDate = new Date(year, today.getMonth() - 1, 1).toISOString().split('T')[0];
                endDate = new Date(year, today.getMonth(), 0).toISOString().split('T')[0];
                break;
                
            case 'last_quarter': {
                const currentQuarter = Math.floor(today.getMonth() / 3);
                const lastQuarterStart = currentQuarter === 0 ? 9 : (currentQuarter - 1) * 3;
                const lastQuarterYear = currentQuarter === 0 ? year - 1 : year;
                startDate = new Date(lastQuarterYear, lastQuarterStart, 1).toISOString().split('T')[0];
                endDate = new Date(lastQuarterYear, lastQuarterStart + 3, 0).toISOString().split('T')[0];
                break;
            }
            
            case 'last_year':
                startDate = new Date(year - 1, 0, 1).toISOString().split('T')[0];
                endDate = new Date(year - 1, 11, 31).toISOString().split('T')[0];
                break;
                
            // Custom - handled separately via date inputs
            case 'custom':
                // Return nulls; custom dates are read from input fields
                break;
                
            default:
                // Lifetime - no date filter
                break;
        }

        return { startDate, endDate };
    }

    async applyDatePreset() {
        // Clear custom date inputs when preset is selected
        const datePreset = this.datePresetRef.el ? this.datePresetRef.el.value : null;
        if (datePreset && datePreset !== 'custom') {
            if (this.startDateRef.el) this.startDateRef.el.value = '';
            if (this.endDateRef.el) this.endDateRef.el.value = '';
        }
        await this.applyFilters();
    }
    
    /**
     * Set date period from pill button click.
     * @param {string} period - 'today', 'week', 'month', or '' for all
     */
    async setDatePeriod(period) {
        this.state.activePeriod = period;
        
        // Clear custom date inputs
        if (this.startDateRef.el) this.startDateRef.el.value = '';
        if (this.endDateRef.el) this.endDateRef.el.value = '';
        
        // Get date range from preset
        const { startDate, endDate } = this.getDateRangeFromPreset(period);
        
        // Update current filters
        this.currentFilters.start_date = startDate;
        this.currentFilters.end_date = endDate;
        
        // Apply filters
        await this.applyFilters();
    }
    
    /**
     * Apply custom date range from date inputs.
     */
    async applyCustomDateRange() {
        // When custom dates are entered, clear the preset dropdown
        if (this.datePresetRef.el) {
            this.datePresetRef.el.value = 'custom';
        }
        await this.applyFilters();
    }

    async applyFilters() {
        const userId = this.userRef.el ? this.userRef.el.value : null;
        const customerId = this.customerRef.el ? this.customerRef.el.value : null;
        const projectId = this.projectRef.el ? this.projectRef.el.value : null;
        const datePreset = this.datePresetRef.el ? this.datePresetRef.el.value : null;
        
        let startDate, endDate;
        
        // Check for custom date inputs first
        const customStart = this.startDateRef.el ? this.startDateRef.el.value : null;
        const customEnd = this.endDateRef.el ? this.endDateRef.el.value : null;
        
        if (customStart || customEnd) {
            // Use custom date range
            startDate = customStart || null;
            endDate = customEnd || null;
        } else {
            // Use preset
            const presetRange = this.getDateRangeFromPreset(datePreset);
            startDate = presetRange.startDate;
            endDate = presetRange.endDate;
        }

        // Store current filters for use by other methods
        this.currentFilters = {
            user: userId || null,
            customer: customerId || null,
            project: projectId || null,
            start_date: startDate || null,
            end_date: endDate || null,
        };

        const filterParams = this.getFilterParams();

        // Fetch all filtered data in parallel
        const [tilesData, tasksData, activitiesData] = await Promise.all([
            rpc('/ptt/dashboard/filter-apply', { data: filterParams }),
            rpc('/ptt/dashboard/tasks', { page: 1, limit: 5, filters: filterParams }),
            rpc('/ptt/dashboard/activities', { page: 1, limit: 5, filters: filterParams }),
        ]);

        // Update KPI tiles
        this.state.myTasks = tilesData.my_tasks;
        this.state.myTasksIds = tilesData.my_tasks_ids;
        this.state.totalProjects = tilesData.total_projects;
        this.state.totalProjectsIds = tilesData.total_projects_ids;
        this.state.activeTasks = tilesData.active_tasks;
        this.state.activeTasksIds = tilesData.active_tasks_ids;
        this.state.myOverdueTasks = tilesData.my_overdue_tasks;
        this.state.myOverdueTasksIds = tilesData.my_overdue_tasks_ids;
        this.state.overdueTasks = tilesData.overdue_tasks;
        this.state.overdueTasksIds = tilesData.overdue_tasks_ids;
        this.state.todayTasks = tilesData.today_tasks;
        this.state.todayTasksIds = tilesData.today_tasks_ids;

        // Update task table
        this.state.tasks = tasksData.tasks;
        this.state.taskPage = tasksData.page;
        this.state.taskPages = tasksData.pages;

        // Update activities table
        this.state.activities = activitiesData.activities;
        this.state.activityPage = activitiesData.page;
        this.state.activityPages = activitiesData.pages;

        // Re-render charts with filters
        await this.renderAllCharts();
    }

    async resetFilters() {
        // Reset filter inputs
        if (this.userRef.el) this.userRef.el.value = '';
        if (this.customerRef.el) this.customerRef.el.value = '';
        if (this.projectRef.el) this.projectRef.el.value = '';
        if (this.datePresetRef.el) this.datePresetRef.el.value = '';
        if (this.startDateRef.el) this.startDateRef.el.value = '';
        if (this.endDateRef.el) this.endDateRef.el.value = '';
        if (this.presetSelectRef.el) this.presetSelectRef.el.value = '';

        // Clear stored filter state
        this.currentFilters = {
            user: null,
            customer: null,
            project: null,
            start_date: null,
            end_date: null,
        };
        
        this.state.currentPresetId = null;

        // Reload all data (unfiltered)
        await this.loadInitialData();
        await this.renderAllCharts();
    }

    // =========================================================================
    // SAVED FILTER PRESETS
    // =========================================================================

    /**
     * Save current filter combination as a preset.
     */
    async saveFilterPreset() {
        const name = prompt(_t("Enter a name for this filter preset:"));
        if (!name || !name.trim()) {
            return;
        }
        
        try {
            const result = await rpc('/ptt/dashboard/save-preset', {
                name: name.trim(),
                filters: this.currentFilters,
            });
            
            if (result.success) {
                this.notification.add(_t("Filter preset saved: ") + name, {
                    type: "success",
                    sticky: false,
                });
                // Reload presets
                const presetsData = await rpc('/ptt/dashboard/presets');
                this.state.presets = presetsData.presets || [];
            } else {
                this.notification.add(result.error || _t("Failed to save preset"), {
                    type: "danger",
                    sticky: false,
                });
            }
        } catch (error) {
            console.error('Error saving preset:', error);
            this.notification.add(_t("Failed to save preset"), {
                type: "danger",
                sticky: false,
            });
        }
    }

    /**
     * Load a saved filter preset.
     */
    async loadFilterPreset(ev) {
        const presetId = ev.target.value;
        if (!presetId) {
            return;
        }
        
        try {
            const result = await rpc('/ptt/dashboard/load-preset', {
                preset_id: parseInt(presetId),
            });
            
            if (result.success) {
                const filters = result.filters;
                
                // Apply filters to UI
                if (this.userRef.el) this.userRef.el.value = filters.user || '';
                if (this.customerRef.el) this.customerRef.el.value = filters.customer || '';
                if (this.projectRef.el) this.projectRef.el.value = filters.project || '';
                if (this.startDateRef.el) this.startDateRef.el.value = filters.start_date || '';
                if (this.endDateRef.el) this.endDateRef.el.value = filters.end_date || '';
                if (this.datePresetRef.el) this.datePresetRef.el.value = filters.start_date ? 'custom' : '';
                
                // Update stored filters and apply
                this.currentFilters = {
                    user: filters.user || null,
                    customer: filters.customer || null,
                    project: filters.project || null,
                    start_date: filters.start_date || null,
                    end_date: filters.end_date || null,
                };
                
                this.state.currentPresetId = presetId;
                await this.applyFilters();
                
                this.notification.add(_t("Preset loaded: ") + result.name, {
                    type: "success",
                    sticky: false,
                });
            }
        } catch (error) {
            console.error('Error loading preset:', error);
            this.notification.add(_t("Failed to load preset"), {
                type: "danger",
                sticky: false,
            });
        }
    }

    /**
     * Delete a saved filter preset.
     */
    async deleteFilterPreset(presetId) {
        if (!confirm(_t("Delete this filter preset?"))) {
            return;
        }
        
        try {
            const result = await rpc('/ptt/dashboard/delete-preset', {
                preset_id: presetId,
            });
            
            if (result.success) {
                this.notification.add(_t("Preset deleted"), {
                    type: "success",
                    sticky: false,
                });
                // Reload presets
                const presetsData = await rpc('/ptt/dashboard/presets');
                this.state.presets = presetsData.presets || [];
                
                if (this.state.currentPresetId === presetId) {
                    this.state.currentPresetId = null;
                    if (this.presetSelectRef.el) this.presetSelectRef.el.value = '';
                }
            }
        } catch (error) {
            console.error('Error deleting preset:', error);
            this.notification.add(_t("Failed to delete preset"), {
                type: "danger",
                sticky: false,
            });
        }
    }

    // =========================================================================
    // QUICK TASK ASSIGNMENT
    // =========================================================================

    /**
     * Quick-assign a task to a user directly from the dashboard.
     */
    async assignTask(taskId) {
        // Get available users for assignment
        const users = this.state.availableUsers;
        if (!users || users.length === 0) {
            this.notification.add(_t("No users available for assignment"), {
                type: "warning",
                sticky: false,
            });
            return;
        }
        
        // Build simple prompt with user options
        let userOptions = users.map(u => `${u.id}: ${u.name}`).join('\n');
        const userIdStr = prompt(
            _t("Enter user ID to assign task to:\n\n") + userOptions
        );
        
        if (!userIdStr || !userIdStr.trim()) {
            return;
        }
        
        const userId = parseInt(userIdStr.trim());
        if (isNaN(userId)) {
            this.notification.add(_t("Invalid user ID"), {
                type: "danger",
                sticky: false,
            });
            return;
        }
        
        try {
            const result = await rpc('/ptt/dashboard/assign-task', {
                task_id: taskId,
                user_id: userId,
            });
            
            if (result.success) {
                this.notification.add(_t("Task assigned successfully"), {
                    type: "success",
                    sticky: false,
                });
                // Refresh task list
                await this.refreshDashboard(true);
            } else {
                this.notification.add(result.error || _t("Failed to assign task"), {
                    type: "danger",
                    sticky: false,
                });
            }
        } catch (error) {
            console.error('Error assigning task:', error);
            this.notification.add(_t("Failed to assign task"), {
                type: "danger",
                sticky: false,
            });
        }
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
