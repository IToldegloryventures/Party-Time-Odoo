/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Layout } from "@web/search/layout";
import { registry } from "@web/core/registry";

class DashboardController extends Component {
    static template = "ptt_operational_dashboard.Dashboard";
    static components = { Layout };
}

registry.category("actions").add("ptt_operational_dashboard", DashboardController);
