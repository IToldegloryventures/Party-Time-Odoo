/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { DashboardTabs } from "./components/dashboard_tabs";
import { KpiCard } from "./components/kpi_card";
import "./dashboard_statistics_service";

export class PttDashboardController extends Component {
    static template = "ptt_operational_dashboard.Dashboard";
    static components = { Layout, DashboardTabs, KpiCard };
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.statisticsService = useService("ptt_dashboard_statistics");
        
        // Subscribe to reactive statistics object (step 7: Real life update)
        // This allows automatic updates when statistics change
        this.statisticsState = useState(this.statisticsService.statistics);
        
        this.state = useState({
            activeTab: 'overview',
            kpis: {},
            loading: true,
            lastUpdated: null,
            refreshing: false,
            showExportMenu: false,
            error: null,
            isEmpty: false,
        });
        
        onWillStart(async () => {
            await this.loadKpis('overview');
        });
    }
    
    async refreshData() {
        this.state.refreshing = true;
        this.statisticsService.invalidateCache();
        await this.loadKpis(this.state.activeTab);
        this.state.refreshing = false;
    }
    
    get display() {
        return {
            controlPanel: {},
        };
    }
    
    async loadKpis(tabId) {
        this.state.loading = true;
        this.state.error = null;
        this.state.isEmpty = false;
        
        try {
            let kpis = {};
        if (tabId === 'overview') {
                // Use cached statistics service (step 5: Cache network calls)
                kpis = await this.statisticsService.loadStatistics();
                // Update state from reactive object
                this.state.kpis = this.statisticsState.overview || kpis;
            } else {
                const repId = parseInt(tabId.replace('rep_', ''));
                // Use cached rep statistics service (step 5: Cache network calls)
                kpis = await this.statisticsService.loadRepStatistics(repId);
                // Update state from reactive object
                this.state.kpis = this.statisticsState.reps[repId] || kpis;
            }
            
            // Check if data is empty
            const hasData = Object.keys(kpis).length > 0 && (
                (tabId === 'overview' && (kpis.total_leads > 0 || kpis.total_quotes > 0 || kpis.total_events_week > 0)) ||
                (tabId !== 'overview' && (kpis.leads_count > 0 || kpis.quotes_count > 0 || kpis.events_count > 0))
            );
            this.state.isEmpty = !hasData;
            
            this.state.lastUpdated = new Date();
        } catch (error) {
            console.error("Error loading KPIs:", error);
            const errorMessage = error.message || "Failed to load dashboard data.";
            this.state.error = `${errorMessage} Please try refreshing.`;
        } finally {
            this.state.loading = false;
        }
    }
    
    async retryLoad() {
        this.state.error = null;
        await this.loadKpis(this.state.activeTab);
    }
    
    formatLastUpdated() {
        if (!this.state.lastUpdated) return "";
        const now = new Date();
        const diff = Math.floor((now - this.state.lastUpdated) / 1000);
        if (diff < 60) return "Just now";
        if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hr ago`;
        return this.state.lastUpdated.toLocaleTimeString();
        }
        
    toggleExportMenu() {
        this.state.showExportMenu = !this.state.showExportMenu;
    }
    
    onTabChange(tabId) {
        this.state.activeTab = tabId;
        this.loadKpis(tabId);
    }
    
    async executeQuickAction(actionName) {
        let widget = await this.orm.searchRead('ptt.dashboard.widget', [], ['id'], { limit: 1 });
        if (!widget.length) {
            // Create widget if it doesn't exist
            const widgetId = await this.orm.call('ptt.dashboard.widget', '_get_or_create_widget', []);
            widget = await this.orm.searchRead('ptt.dashboard.widget', [['id', '=', widgetId]], ['id'], { limit: 1 });
        }
        if (widget.length) {
            const action = await this.orm.call('ptt.dashboard.widget', actionName, [widget[0].id]);
            this.action.doAction(action);
        }
    }
    
}

registry.category("actions").add("ptt_operational_dashboard", PttDashboardController);

