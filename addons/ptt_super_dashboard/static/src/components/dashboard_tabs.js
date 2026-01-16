/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class DashboardTabs extends Component {
    static template = "ptt_super_dashboard.DashboardTabs";
    static props = {
        onTabChange: Function,
    };
    
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            activeTab: 'overview',
            salesReps: [],
        });
        
        onWillStart(async () => {
            this.state.salesReps = await this.orm.searchRead(
                'ptt.sales.rep',
                [['show_in_dashboard', '=', true], ['active', '=', true]],
                ['id', 'name', 'user_id']
            );
        });
    }
    
    selectTab(tabId) {
        this.state.activeTab = tabId;
        this.props.onTabChange(tabId);
    }
}

