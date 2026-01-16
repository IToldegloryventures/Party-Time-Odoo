/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * SalesDashboard Component
 * 
 * Shows company-wide sales KPIs:
 * - Total Booked Amount (all booked events)
 * - Total Paid (paid invoices)
 * - Outstanding/Overdue Amount
 * - Per-Rep breakdown cards
 * 
 * Filtered by date range (default: current month)
 */
export class SalesDashboard extends Component {
    static template = "ptt_operational_dashboard.SalesDashboard";
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
                "get_sales_dashboard_data",
                [],
                {
                    start_date: this.state.startDate,
                    end_date: this.state.endDate,
                }
            );
        } catch (e) {
            console.error("Failed to load sales dashboard:", e);
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
            case 'this_week':
                const dayOfWeek = now.getDay();
                const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Monday
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
            case 'ytd':
                startDate = new Date(now.getFullYear(), 0, 1);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                break;
            default:
                return;
        }
        
        this.state.startDate = this.formatDateForInput(startDate);
        this.state.endDate = this.formatDateForInput(endDate);
        this.state.dateRange = range;
        this.loadData();
    }
    
    formatPercentage(value) {
        return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
    }
    
    getThresholdColor(value, thresholds) {
        if (!thresholds) return 'default';
        if (value >= thresholds.green) return 'success';
        if (value >= thresholds.yellow) return 'warning';
        return 'danger';
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount || 0);
    }

    get dateRangeLabel() {
        const start = new Date(this.state.startDate + "T00:00:00");
        const end = new Date(this.state.endDate + "T00:00:00");
        const options = { month: 'short', day: 'numeric' };
        return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
    }

    onBookedClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Booked Events",
            res_model: "crm.lead",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: [
                ["stage_id.name", "=", "Booked"],
                ["ptt_event_date", ">=", this.state.startDate],
                ["ptt_event_date", "<=", this.state.endDate],
            ],
            target: "current",
        });
    }

    onPaidClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Paid Invoices",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["move_type", "=", "out_invoice"],
                ["payment_state", "=", "paid"],
                ["invoice_date", ">=", this.state.startDate],
                ["invoice_date", "<=", this.state.endDate],
            ],
            target: "current",
        });
    }

    onOutstandingClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Outstanding Invoices",
            res_model: "account.move",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["move_type", "=", "out_invoice"],
                ["payment_state", "in", ["not_paid", "partial"]],
                ["invoice_date", ">=", this.state.startDate],
                ["invoice_date", "<=", this.state.endDate],
            ],
            target: "current",
        });
    }

    onRepClick(rep) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `${rep.name}'s Sales`,
            res_model: "crm.lead",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: [
                ["user_id", "=", rep.id],
                ["ptt_event_date", ">=", this.state.startDate],
                ["ptt_event_date", "<=", this.state.endDate],
            ],
            target: "current",
        });
    }
}
