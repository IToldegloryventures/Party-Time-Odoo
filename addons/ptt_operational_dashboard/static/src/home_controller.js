/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Import components
import { HomeNavigation } from "./components/home_navigation";
import { MyWorkSection } from "./components/my_work_section";
import { AssignedTasks } from "./components/assigned_tasks";
import { PersonalTodo } from "./components/personal_todo";
import { AssignedComments } from "./components/assigned_comments";
import { AgendaCalendar } from "./components/agenda_calendar";
import { EventCalendarFull } from "./components/event_calendar_full";
import { SalesDashboard } from "./components/sales_dashboard";

/**
 * HomeController
 * 
 * Main entry point for the PTT Home Hub.
 * Aggregates all home components and handles tab navigation.
 */
export class HomeController extends Component {
    static template = "ptt_operational_dashboard.HomeController";
    static components = {
        HomeNavigation,
        MyWorkSection,
        AssignedTasks,
        PersonalTodo,
        AssignedComments,
        AgendaCalendar,
        EventCalendarFull,
        SalesDashboard,
    };

    setup() {
        this.homeService = useService("ptt_home");
        this.action = useService("action");
        
        this.state = useState({
            activeTab: "home",
            loading: true,
            refreshing: false,
            homeData: null,
            error: null,
        });
        
        onWillStart(async () => {
            await this.loadHomeData();
        });
    }

    async loadHomeData() {
        this.state.loading = true;
        this.state.error = null;
        try {
            this.state.homeData = await this.homeService.getHomeSummary();
        } catch (error) {
            console.error("Error loading home data:", error);
            this.state.error = "Failed to load dashboard data. Please try refreshing.";
        } finally {
            this.state.loading = false;
        }
    }

    async onRefresh() {
        this.state.refreshing = true;
        this.homeService.invalidateCache();
        await this.loadHomeData();
        this.state.refreshing = false;
    }

    onTabChange(tabId) {
        this.state.activeTab = tabId;
    }

    // Getters for template
    get myWorkTasks() {
        return this.state.homeData?.my_work || {
            today: [],
            overdue: [],
            upcoming: [],
            unscheduled: [],
        };
    }

    get assignedTasks() {
        return this.state.homeData?.assigned_tasks || [];
    }

    get personalTodos() {
        return this.state.homeData?.personal_todos || {
            today: [],
            overdue: [],
            upcoming: [],
            unscheduled: [],
        };
    }

    get assignedComments() {
        return this.state.homeData?.assigned_comments || [];
    }

    get agendaEvents() {
        return this.state.homeData?.agenda_events || [];
    }

    openCommissionReports() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Sales Commissions",
            res_model: "ptt.sales.commission",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

// Register the action
registry.category("actions").add("ptt_home_hub", HomeController);

