/** @odoo-module **/

import { registry } from "@web/core/registry";
import { mount } from "@odoo/owl";
import { DashboardBackButton } from "./components/dashboard_back_button";

/**
 * Dashboard Back Button Service
 * 
 * Service that manages the global "Back to Dashboard" floating button.
 * Mounts the component to appear on all pages (except the dashboard itself).
 */
const dashboardBackButtonService = {
    dependencies: ["action"],
    
    start(env, { action }) {
        let component = null;
        let mounted = false;
        
        const mountButton = () => {
            if (mounted) return;
            
            // Find or create container
            let container = document.getElementById("ptt-back-button-container");
            if (!container) {
                container = document.createElement("div");
                container.id = "ptt-back-button-container";
                document.body.appendChild(container);
            }
            
            // Mount component
            component = mount(DashboardBackButton, container, {
                env,
            });
            mounted = true;
        };
        
        const unmountButton = () => {
            if (component) {
                component.destroy();
                component = null;
                mounted = false;
            }
        };
        
        // Mount on service start
        mountButton();
        
        // Listen for navigation changes
        const checkAndUpdate = () => {
            const currentUrl = window.location.href;
            const isDashboard = currentUrl.includes("ptt_home_hub") || 
                               currentUrl.includes("#action=ptt_home_hub");
            const isMainMenu = currentUrl.includes("#action=menu");
            
            if (isDashboard || isMainMenu) {
                unmountButton();
            } else {
                mountButton();
            }
        };
        
        // Check on route changes
        window.addEventListener("popstate", checkAndUpdate);
        setInterval(checkAndUpdate, 500);
        
        return {
            mount: mountButton,
            unmount: unmountButton,
        };
    },
};

registry.category("services").add("ptt_dashboard_back_button", dashboardBackButtonService);

