/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * ExportMenu Component
 * 
 * Provides export functionality for dashboard views:
 * - Export to Excel
 * - Export to PDF
 */
export class ExportMenu extends Component {
    static template = "ptt_super_dashboard.ExportMenu";
    static props = {
        data: { type: Object },
        title: { type: String },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async exportToExcel() {
        try {
            // Call backend method to generate Excel
            const result = await this.orm.call(
                "ptt.home.data",
                "export_dashboard_to_excel",
                [],
                {
                    data: this.props.data,
                    title: this.props.title || "Dashboard Export",
                }
            );
            
            if (result && result.file_url) {
                // Download the file
                window.open(result.file_url, '_blank');
                this.notification.add("Excel file generated successfully", { type: "success" });
            }
        } catch (e) {
            console.error("Failed to export to Excel:", e);
            this.notification.add("Failed to export to Excel", { type: "danger" });
        }
    }

    async exportToPDF() {
        try {
            // Call backend method to generate PDF
            const result = await this.orm.call(
                "ptt.home.data",
                "export_dashboard_to_pdf",
                [],
                {
                    data: this.props.data,
                    title: this.props.title || "Dashboard Export",
                }
            );
            
            if (result && result.file_url) {
                // Download the file
                window.open(result.file_url, '_blank');
                this.notification.add("PDF file generated successfully", { type: "success" });
            }
        } catch (e) {
            console.error("Failed to export to PDF:", e);
            this.notification.add("Failed to export to PDF", { type: "danger" });
        }
    }
}

