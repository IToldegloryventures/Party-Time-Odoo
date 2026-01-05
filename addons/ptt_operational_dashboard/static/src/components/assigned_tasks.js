/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * AssignedTasks Component
 * 
 * Displays all tasks assigned to the current user with:
 * - Deep links to task form
 * - Deep links to parent project
 * - Deep links to related CRM lead
 */
export class AssignedTasks extends Component {
    static template = "ptt_operational_dashboard.AssignedTasks";
    static props = {
        tasks: { type: Array },
    };

    setup() {
        this.action = useService("action");
    }

    formatDate(dateStr) {
        if (!dateStr) return "No due date";
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return "Today";
        if (diffDays === 1) return "Tomorrow";
        if (diffDays === -1) return "Yesterday";
        if (diffDays < -1) return `${Math.abs(diffDays)} days overdue`;
        if (diffDays < 7) return `In ${diffDays} days`;
        
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    onTaskClick(task) {
        if (task.action) {
            this.action.doAction(task.action);
        }
    }

    onProjectClick(ev, task) {
        ev.stopPropagation();
        if (task.project_action) {
            this.action.doAction(task.project_action);
        }
    }

    onLeadClick(ev, task) {
        ev.stopPropagation();
        if (task.crm_lead_action) {
            this.action.doAction(task.crm_lead_action);
        }
    }

    onViewAllClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "My Tasks",
            res_model: "project.task",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: [["stage_id.fold", "=", false]],
            context: { search_default_my_tasks: 1 },
            target: "current",
        });
    }
}

