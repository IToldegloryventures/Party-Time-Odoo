/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { user } from "@web/core/user";

/**
 * HomeNavigation Component
 * 
 * Top navigation bar with tabs for switching between:
 * - Home (default)
 * - Sales Dashboard
 * - Commission Dashboard
 * - Event Calendar
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
        this.state = useState({
            userName: user.name || "User",
        });
    }

    get tabs() {
        return [
            { id: "home", label: "Home", icon: "fa-home" },
            { id: "sales", label: "Sales Dashboard", icon: "fa-chart-bar" },
            { id: "commission", label: "Commission", icon: "fa-dollar" },
            { id: "calendar", label: "Event Calendar", icon: "fa-calendar" },
        ];
    }

    onTabClick(tabId) {
        this.props.onTabChange(tabId);
    }

    onRefreshClick() {
        this.props.onRefresh();
    }
}

