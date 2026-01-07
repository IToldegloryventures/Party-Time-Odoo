/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * DashboardEditor Component
 * 
 * Full drag-and-drop editor for customizing the dashboard.
 * Three-panel layout: Library (left), Canvas (center), Properties (right).
 */
export class DashboardEditor extends Component {
    static template = "ptt_operational_dashboard.DashboardEditor";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            loading: true,
            metrics: [],
            layout: [],
            selectedItem: null,
            editMode: false,
            draggedItem: null,
        });
        
        onWillStart(async () => {
            await this.loadConfiguration();
        });
    }

    async loadConfiguration() {
        this.state.loading = true;
        try {
            // Load metric configurations
            const metrics = await this.orm.searchRead(
                "ptt.dashboard.metric.config",
                [],
                ["metric_name", "metric_label", "visible", "sequence", "kpi_size", "tab_assignment", "threshold_green_min", "threshold_yellow_min", "threshold_red_max", "target_value"]
            );
            this.state.metrics = metrics;
            
            // Load layout configurations
            const layouts = await this.orm.searchRead(
                "ptt.dashboard.layout.config",
                [],
                ["section_name", "section_label", "visible", "sequence", "tab_assignment", "grid_columns", "card_size"]
            );
            this.state.layout = layouts;
        } catch (e) {
            console.error("Failed to load dashboard configuration:", e);
        } finally {
            this.state.loading = false;
        }
    }

    onDragStart(ev, item) {
        this.state.draggedItem = item;
        ev.dataTransfer.effectAllowed = "move";
    }

    onDragOver(ev) {
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
    }

    onDrop(ev, targetIndex) {
        ev.preventDefault();
        if (this.state.draggedItem) {
            // Reorder items
            const items = this.state.metrics.filter(m => m.tab_assignment === this.state.draggedItem.tab_assignment);
            const draggedIndex = items.findIndex(m => m.id === this.state.draggedItem.id);
            
            if (draggedIndex !== -1 && targetIndex !== draggedIndex) {
                // Update sequence
                const newSequence = targetIndex * 10;
                this.updateMetricSequence(this.state.draggedItem.id, newSequence);
            }
        }
        this.state.draggedItem = null;
    }

    async updateMetricSequence(metricId, newSequence) {
        try {
            await this.orm.write("ptt.dashboard.metric.config", [metricId], {
                sequence: newSequence,
            });
            await this.loadConfiguration();
        } catch (e) {
            console.error("Failed to update sequence:", e);
        }
    }

    onItemClick(item) {
        this.state.selectedItem = item;
    }

    async toggleVisibility(metricId, currentVisible) {
        try {
            await this.orm.write("ptt.dashboard.metric.config", [metricId], {
                visible: !currentVisible,
            });
            await this.loadConfiguration();
        } catch (e) {
            console.error("Failed to toggle visibility:", e);
        }
    }

    async saveChanges() {
        try {
            this.notification.add("Dashboard configuration saved", { type: "success" });
            // Reload to reflect changes
            await this.loadConfiguration();
        } catch (e) {
            console.error("Failed to save changes:", e);
            this.notification.add("Failed to save changes", { type: "danger" });
        }
    }

    getMetricsByTab(tab) {
        return this.state.metrics
            .filter(m => m.tab_assignment === tab)
            .sort((a, b) => a.sequence - b.sequence);
    }
}

