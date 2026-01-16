/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * OperationsDashboard Component
 * 
 * Shows operational metrics:
 * - POs Month to Date
 * - Refunds Being Issued
 * - Rain Delays
 * - Time to Collect on Invoices
 * - Average Time to Event
 * - Event Level Metrics ($ per event, services per event, line items per event)
 * 
 * Company total at top, all users broken out below.
 */
export class OperationsDashboard extends Component {
    static template = "ptt_super_dashboard.OperationsDashboard";
    static props = {};

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        
        // Get current month date range
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        
        this.state = useState({
            data: null,
            loading: true,
            startDate: this.formatDateForInput(firstDay),
            endDate: this.formatDateForInput(lastDay),
            dateRange: 'this_month', // Track active date range
        });
        
        onWillStart(async () => {
            await this.loadData();
        });
    }
    
    // Refresh data when component is mounted or tab becomes active
    async refreshData() {
        await this.loadData();
    }

    formatDateForInput(date) {
        return date.toISOString().split('T')[0];
    }

    async loadData() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call(
                "ptt.home.data",
                "get_operations_dashboard_data",
                [],
                {
                    start_date: this.state.startDate,
                    end_date: this.state.endDate,
                }
            );
        } catch (e) {
            console.error("Failed to load operations dashboard:", e);
        } finally {
            this.state.loading = false;
        }
    }

    async onDateChange() {
        this.state.dateRange = 'custom';
        await this.loadData();
    }

    setDateRange(range) {
        const now = new Date();
        let startDate, endDate;
        
        switch (range) {
            case 'today':
                startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                break;
            case 'this_week':
                const dayOfWeek = now.getDay();
                const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
                startDate = new Date(now.getFullYear(), now.getMonth(), diff);
                endDate = new Date(now.getFullYear(), now.getMonth(), diff + 6);
                break;
            case 'this_month':
                startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                break;
            case 'last_month':
                startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), 0);
                break;
            case 'this_quarter':
                const quarter = Math.floor(now.getMonth() / 3);
                startDate = new Date(now.getFullYear(), quarter * 3, 1);
                endDate = new Date(now.getFullYear(), quarter * 3 + 3, 0);
                break;
            case 'this_year':
                startDate = new Date(now.getFullYear(), 0, 1);
                endDate = new Date(now.getFullYear(), 11, 31);
                break;
            default:
                return;
        }
        
        this.state.startDate = this.formatDateForInput(startDate);
        this.state.endDate = this.formatDateForInput(endDate);
        this.state.dateRange = range;
        this.loadData();
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount || 0);
    }

    formatDays(days) {
        if (days === null || days === undefined) return "N/A";
        return `${Math.round(days)} days`;
    }

    get dateRangeLabel() {
        const start = new Date(this.state.startDate + "T00:00:00");
        const end = new Date(this.state.endDate + "T00:00:00");
        const options = { month: 'short', day: 'numeric' };
        return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
    }

    onTaskMetricClick(metricType) {
        const today = new Date().toISOString().split('T')[0];
        let domain = [["stage_id.fold", "=", false]];
        
        switch (metricType) {
            case "assigned":
                domain.push(["user_ids", "!=", false]);
                break;
            case "overdue":
                domain.push(["date_deadline", "<", today], ["date_deadline", "!=", false]);
                break;
            case "unassigned":
                domain.push(["user_ids", "=", false]);
                break;
            case "completed":
                domain = [["stage_id.fold", "=", true]];
                break;
        }
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Tasks - ${metricType}`,
            res_model: "project.task",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }
}

