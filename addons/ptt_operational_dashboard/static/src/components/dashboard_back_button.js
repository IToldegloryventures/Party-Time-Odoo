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
 * 
 * IMPORTANT: This component loads early in the app lifecycle, so we must be
 * defensive about service availability.
 */
export class DashboardBackButton extends Component {
    static template = "ptt_operational_dashboard.DashboardBackButton";
    static props = {};

    setup() {
        // Use try-catch for service in case it's not ready yet
        try {
            this.action = useService("action");
        } catch (e) {
            console.warn("DashboardBackButton: action service not ready yet");
            this.action = null;
        }
        
        this.state = useState({
            visible: false,
        });

        // Only set up listeners after a delay to ensure app is fully loaded
        onMounted(() => {
            // Delay initial setup to let the app fully initialize
            setTimeout(() => {
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
                }, 1000); // Increased interval to reduce overhead
            }, 1000); // Wait 1 second for app to fully load
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
        // Safety check - don't run if component is destroyed
        if (!this.state) return;
        
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
        // Safety check for action service
        if (!this.action) {
            console.warn("DashboardBackButton: action service not available");
            // Fallback: use direct navigation
            window.location.hash = "#action=ptt_home_hub";
            return;
        }
        
        // Navigate back to dashboard - use safer options
        this.action.doAction("ptt_home_hub", {
            clearBreadcrumbs: true,
            stackPosition: "replaceCurrentAction",
        });
    }
}

