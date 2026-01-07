/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * DashboardBackButton Component
 * 
 * Floating action button that appears when users navigate to standard Odoo apps
 * from the dashboard. Provides quick navigation back to the dashboard.
 */
export class DashboardBackButton extends Component {
    static template = "ptt_operational_dashboard.DashboardBackButton";

    setup() {
        this.action = useService("action");
        this.router = useService("router");
        this.state = useState({
            visible: false,
        });

        // Check if we're in a standard Odoo app (not the dashboard)
        onMounted(() => {
            this.checkVisibility();
            // Listen for route changes
            this.routeChangeHandler = () => {
                setTimeout(() => this.checkVisibility(), 100);
            };
            window.addEventListener("popstate", this.routeChangeHandler);
            // Check periodically in case user navigates via action service
            this.visibilityInterval = setInterval(() => {
                this.checkVisibility();
            }, 500);
        });

        onWillUnmount(() => {
            if (this.visibilityInterval) {
                clearInterval(this.visibilityInterval);
            }
            if (this.routeChangeHandler) {
                window.removeEventListener("popstate", this.routeChangeHandler);
            }
        });
    }

    checkVisibility() {
        // Check if current URL/action is NOT the dashboard
        const currentUrl = window.location.href;
        const isDashboard = currentUrl.includes("ptt_home_hub") || 
                           currentUrl.includes("#action=ptt_home_hub");
        
        // Also check if we're in the main menu (shouldn't show button there)
        const isMainMenu = currentUrl.includes("#action=menu");
        
        // Show button if we're NOT on the dashboard and NOT in main menu
        this.state.visible = !isDashboard && !isMainMenu;
    }

    onBackClick() {
        // Navigate back to dashboard
        this.action.doAction("ptt_home_hub", {
            clearBreadcrumbs: true,
        });
    }
}

