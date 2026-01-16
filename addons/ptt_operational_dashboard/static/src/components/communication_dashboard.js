/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * CommunicationDashboard Component
 * 
 * Shows communication metrics:
 * - Calls per Rep
 * - Emails per Rep
 * - Response Time (Email)
 * - Response Time (Call)
 * 
 * Company total at top, all users broken out below.
 */
export class CommunicationDashboard extends Component {
    static template = "ptt_operational_dashboard.CommunicationDashboard";
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
                "get_communication_dashboard_data",
                [],
                {
                    start_date: this.state.startDate,
                    end_date: this.state.endDate,
                }
            );
        } catch (e) {
            console.error("Failed to load communication dashboard:", e);
        } finally {
            this.state.loading = false;
        }
    }

    async onDateChange() {
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
        this.loadData();
    }

    formatTime(hours) {
        if (hours === null || hours === undefined) return "N/A";
        if (hours < 1) {
            return `${Math.round(hours * 60)} min`;
        }
        return `${Math.round(hours * 10) / 10} hrs`;
    }

    getResponseTimeColor(avgHours, thresholds) {
        if (!thresholds) return 'default';
        if (avgHours <= thresholds.green) return 'success';
        if (avgHours <= thresholds.yellow) return 'warning';
        return 'danger';
    }

    get dateRangeLabel() {
        const start = new Date(this.state.startDate + "T00:00:00");
        const end = new Date(this.state.endDate + "T00:00:00");
        const options = { month: 'short', day: 'numeric' };
        return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
    }
}

