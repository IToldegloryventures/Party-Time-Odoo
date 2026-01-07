/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";

/**
 * MetricChart Component
 * 
 * Generic chart component using Chart.js for visualizing metrics.
 * Supports bar, line, pie/donut charts, and data tables.
 */
export class MetricChart extends Component {
    static template = "ptt_operational_dashboard.MetricChart";
    static props = {
        type: { type: String }, // 'bar', 'line', 'pie', 'donut', 'table'
        data: { type: Object },
        options: { type: Object, optional: true },
    };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
    }

    onMounted() {
        if (this.props.type === 'table') {
            // Table doesn't need Chart.js
            return;
        }
        
        // Load Chart.js dynamically
        this.loadChartJS().then(() => {
            this.renderChart();
        });
    }

    onWillUnmount() {
        if (this.chart) {
            this.chart.destroy();
        }
    }

    async loadChartJS() {
        // Check if Chart.js is already loaded
        if (window.Chart) {
            return;
        }
        
        // Load Chart.js from CDN
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
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

