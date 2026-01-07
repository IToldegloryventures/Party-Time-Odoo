/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * DashboardBackButton Component
 * 
 * Floating action button that appears when users navigate to standard Odoo apps
 * from the dashboard. Provides quick navigation back to the dashboard.
 * 
 * Registered via main_components registry to be rendered within the main Owl app.
 */
export class DashboardBackButton extends Component {
    static template = "ptt_operational_dashboard.DashboardBackButton";
    static props = {};

    setup() {
        this.action = useService("action");
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
            window.addEventListener("hashchange", this.routeChangeHandler);
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
                window.removeEventListener("hashchange", this.routeChangeHandler);
            }
        });
    }

    checkVisibility() {
        // Check if current URL/action is NOT the dashboard
        const currentUrl = window.location.href;
        const hash = window.location.hash || "";
        
        const isDashboard = currentUrl.includes("ptt_home_hub") || 
                           hash.includes("action=ptt_home_hub") ||
                           hash.includes("ptt_operational_dashboard");
        
        // Also check if we're in the main menu (shouldn't show button there)
        const isMainMenu = hash === "" || hash === "#" || hash.includes("action=menu");
        
        // Show button if we're NOT on the dashboard and NOT in main menu
        // and we're actually in an Odoo action
        const hasAction = hash.includes("action=");
        this.state.visible = hasAction && !isDashboard && !isMainMenu;
    }

    onBackClick() {
        // Navigate back to dashboard
        this.action.doAction("ptt_home_hub", {
            clearBreadcrumbs: true,
        });
    }
}

