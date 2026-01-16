/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Dashboard Back Button Service
 * 
 * Provides navigation utility for returning to the PTT Dashboard.
 * 
 * NOTE: The DashboardBackButton main_component has been DISABLED because
 * main_components load very early in the app lifecycle and can cause
 * "Cannot read properties of undefined (reading 'applyState')" errors
 * when the action service isn't fully ready.
 * 
 * TODO: Re-enable once we find a safe way to register main_components
 * that doesn't break app initialization.
 */

// DISABLED: main_components registration - causes startup errors
// import { DashboardBackButton } from "./components/dashboard_back_button";
// registry.category("main_components").add("DashboardBackButton", {
//     Component: DashboardBackButton,
//     props: {},
// });

// Simple service to provide navigation utility
const dashboardBackButtonService = {
    dependencies: ["action"],
    
    start(env, { action }) {
        return {
            navigateToDashboard() {
                if (action && action.doAction) {
                    action.doAction("ptt_home_hub", {
                        clearBreadcrumbs: true,
                    });
                } else {
                    // Fallback: use direct hash navigation
                    window.location.hash = "#action=ptt_home_hub";
                }
            },
        };
    },
};

registry.category("services").add("ptt_dashboard_back_button", dashboardBackButtonService);

