/** @odoo-module **/
import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "ptt_operational_dashboard.KpiCard";
    static props = {
        title: String,
        value: [String, Number],
        icon: { type: String, optional: true },
        color: { type: String, optional: true },
        trend: { type: Number, optional: true }, // Percentage change (e.g., 15 for +15%, -10 for -10%)
        trendPeriod: { type: String, optional: true }, // e.g., "vs last month"
        subtitle: { type: String, optional: true }, // Additional info below value
        tooltip: { type: String, optional: true }, // Custom tooltip text
        clickable: { type: Boolean, optional: true }, // Make card clickable
        onClick: { type: Function, optional: true }, // Click handler
        badge: { type: String, optional: true }, // Badge text (e.g., "New", "Alert")
        badgeClass: { type: String, optional: true }, // Badge CSS class (e.g., "bg-danger", "bg-success")
    };
}

