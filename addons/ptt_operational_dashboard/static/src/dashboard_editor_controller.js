/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { DashboardEditor } from "./components/dashboard_editor";

/**
 * DashboardEditorController
 * 
 * Controller for the dashboard editor action.
 */
export class DashboardEditorController extends Component {
    static template = "ptt_operational_dashboard.DashboardEditorController";
    static components = {
        DashboardEditor,
    };
}

// Register the action
registry.category("actions").add("ptt_dashboard_editor", DashboardEditorController);

