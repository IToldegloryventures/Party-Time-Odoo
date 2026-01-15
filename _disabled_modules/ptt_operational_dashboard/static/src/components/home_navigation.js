/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

/**
 * HomeNavigation Component
 * 
 * Top navigation bar with tabs for switching between:
 * - Home (default)
 * - Sales Dashboard
 * - Commission Dashboard
 * - Event Calendar
 * 
 * Also includes a button to go back to Odoo's main apps menu.
 */
export class HomeNavigation extends Component {
    static template = "ptt_operational_dashboard.HomeNavigation";
    static props = {
        activeTab: { type: String },
        onTabChange: { type: Function },
        onRefresh: { type: Function },
        refreshing: { type: Boolean, optional: true },
    };

    setup() {
        this.action = useService("action");
        this.state = useState({
            userName: user.name || "User",
        });
    }

    get tabs() {
        return [
            { id: "home", label: "Home", icon: "fa-home" },
            { id: "sales", label: "Sales", icon: "fa-chart-bar" },
            { id: "operations", label: "Operations", icon: "fa-cogs" },
            { id: "calendar", label: "Calendar", icon: "fa-calendar" },
        ];
    }

    onTabClick(tabId) {
        this.props.onTabChange(tabId);
    }

    onRefreshClick() {
        this.props.onRefresh();
    }

    onAppsClick() {
        // Navigate back to Odoo's main apps menu
        this.action.doAction("menu");
    }
}
