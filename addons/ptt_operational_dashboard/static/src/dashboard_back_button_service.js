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
        let mountRetries = 0;
        const MAX_RETRIES = 10;
        
        const mountButton = () => {
            if (mounted) return;
            
            // Find or create container
            let container = document.getElementById("ptt-back-button-container");
            if (!container) {
                container = document.createElement("div");
                container.id = "ptt-back-button-container";
                document.body.appendChild(container);
            }
            
            try {
                // Mount component
                // Template should be available due to asset ordering (XML loads before this service)
                component = mount(DashboardBackButton, container, {
                    env,
                });
                mounted = true;
                mountRetries = 0;
            } catch (error) {
                // If template not found, retry a few times
                if (error.message && error.message.includes("Missing template") && mountRetries < MAX_RETRIES) {
                    mountRetries++;
                    console.warn(`Template not yet available, retrying (${mountRetries}/${MAX_RETRIES})...`);
                    setTimeout(mountButton, 200);
                    return;
                }
                console.error("Failed to mount DashboardBackButton:", error);
                mounted = false;
            }
        };
        
        const unmountButton = () => {
            if (component) {
                try {
                    component.destroy();
                } catch (error) {
                    console.warn("Error unmounting DashboardBackButton:", error);
                }
                component = null;
                mounted = false;
            }
        };
        
        // Mount after DOM is ready and templates should be loaded
        // Asset ordering ensures XML template loads before this service
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", () => {
                setTimeout(mountButton, 100);
            });
        } else {
            setTimeout(mountButton, 100);
        }
        
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

