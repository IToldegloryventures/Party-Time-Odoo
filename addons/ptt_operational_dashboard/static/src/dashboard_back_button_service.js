/** @odoo-module **/

import { registry } from "@web/core/registry";
import { DashboardBackButton } from "./components/dashboard_back_button";

/**
 * Dashboard Back Button Service
 * 
 * Registers the DashboardBackButton component via Odoo's main_components registry.
 * This is the proper way to add floating components in Odoo 19 - they get rendered
 * within the main Owl app and have access to all registered templates.
 */

// Register the component in main_components registry
// This is how Odoo 19 handles floating/overlay components like notifications, dialogs, etc.
registry.category("main_components").add("DashboardBackButton", {
    Component: DashboardBackButton,
    props: {},
});

// Simple service to provide navigation utility (optional, for future expansion)
const dashboardBackButtonService = {
    dependencies: ["action"],
    
    start(env, { action }) {
        return {
            navigateToDashboard() {
                action.doAction("ptt_home_hub", {
                    clearBreadcrumbs: true,
                });
            },
        };
    },
};

registry.category("services").add("ptt_dashboard_back_button", dashboardBackButtonService);

