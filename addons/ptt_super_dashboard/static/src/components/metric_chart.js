/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

/**
 * MetricChart Component
 * 
 * Generic chart component using Chart.js for visualizing metrics.
 * Supports bar, line, pie/donut charts, and data tables.
 */
export class MetricChart extends Component {
    static template = "ptt_super_dashboard.MetricChart";
    static props = {
        type: { type: String }, // 'bar', 'line', 'pie', 'donut', 'table'
        data: { type: Object },
        options: { type: Object, optional: true },
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        // Owl 2 lifecycle hooks
        onMounted(async () => {
            if (this.props.type === "table") {
                return; // table doesn't need Chart.js
            }
            try {
                await this.loadChartJS();
                this.renderChart();
            } catch (e) {
                // Never crash OWL runtime if Chart.js isn't available in this environment.
                console.warn("Chart.js unavailable; MetricChart skipped rendering:", e);
            }
        });

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    async loadChartJS() {
        // Check if Chart.js is already loaded
        if (window.Chart) {
            return;
        }
        
        // Load Chart.js from Odoo's bundled web assets (Odoo.sh-safe; no external URLs)
        // Try common paths across Odoo versions.
        try {
            await loadJS("/web/static/lib/Chart/Chart.js");
        } catch {
            await loadJS("/web/static/lib/Chart/Chart.min.js");
        }
        if (!window.Chart) {
            throw new Error("Chart.js did not load from Odoo web assets");
        }
    }

    renderChart() {
        if (!this.canvasRef.el || !window.Chart) {
            return;
        }

        const ctx = this.canvasRef.el.getContext('2d');
        
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    enabled: true,
                },
            },
        };

        const chartOptions = {
            ...defaultOptions,
            ...(this.props.options || {}),
        };

        // Handle donut chart (pie with cutout)
        if (this.props.type === 'donut') {
            chartOptions.plugins = {
                ...chartOptions.plugins,
                ...{
                    cutout: '60%',
                },
            };
            this.chart = new window.Chart(ctx, {
                type: 'pie',
                data: this.props.data,
                options: chartOptions,
            });
        } else {
            this.chart = new window.Chart(ctx, {
                type: this.props.type,
                data: this.props.data,
                options: chartOptions,
            });
        }
    }

    get isTable() {
        return this.props.type === 'table';
    }
}

