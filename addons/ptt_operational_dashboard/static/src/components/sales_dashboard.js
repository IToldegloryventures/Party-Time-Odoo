/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * SalesDashboard Component
 * 
 * Sales KPIs with click-through to native Odoo views.
 */
export class SalesDashboard extends Component {
    static template = "ptt_operational_dashboard.SalesDashboard";
    static props = {};

    setup() {
        this.action = useService("action");
        this.homeService = useService("ptt_home");
        
        this.state = useState({
            kpis: null,
            loading: true,
        });
        
        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            this.state.kpis = await this.homeService.getSalesKpis();
        } finally {
            this.state.loading = false;
        }
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount || 0);
    }

    onLeadsClick() {
        if (this.state.kpis?.leads_action) {
            this.action.doAction(this.state.kpis.leads_action);
        }
    }

    onQuotesClick() {
        if (this.state.kpis?.quotes_action) {
            this.action.doAction(this.state.kpis.quotes_action);
        }
    }

    onOutstandingClick() {
        if (this.state.kpis?.outstanding_action) {
            this.action.doAction(this.state.kpis.outstanding_action);
        }
    }

    onQuoteClick(quote) {
        if (quote.action) {
            this.action.doAction(quote.action);
        }
    }

    onNewLeadClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "New Lead",
            res_model: "crm.lead",
            views: [[false, "form"]],
            target: "current",
            context: { default_type: "lead" },
        });
    }

    onNewQuoteClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "New Quote",
            res_model: "sale.order",
            views: [[false, "form"]],
            target: "current",
        });
    }
}

