/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * TaskLeaderboard Component
 * 
 * Displays task performance leaderboard by user.
 * Shows total tasks, completed tasks, overdue count, and completion rate.
 */
export class TaskLeaderboard extends Component {
    static template = "ptt_super_dashboard.TaskLeaderboard";
    static props = {
        leaderboard: { type: Array },
    };

    setup() {
        this.action = useService("action");
    }

    onUserClick(user) {
        if (user.action) {
            this.action.doAction(user.action);
        }
    }

    formatPercentage(value) {
        return `${value.toFixed(1)}%`;
    }
}

