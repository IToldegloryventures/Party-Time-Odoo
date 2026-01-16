/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

/**
 * DashboardTasksSection Component
 * 
 * Displays all required task sections:
 * - Assigned Tasks (Current User)
 * - Unassigned Tasks
 * - Due Today
 * - Overdue
 * - No Due Date
 * - All Service + Event + CRM Tasks Combined
 */
export class DashboardTasksSection extends Component {
    static template = "ptt_super_dashboard.DashboardTasksSection";
    static props = {
        tasks: { type: Object },
    };

    setup() {
        this.action = useService("action");
        this.userId = user.userId;
    }

    formatDate(dateStr) {
        if (!dateStr) return "No due date";
        const date = new Date(dateStr + "T00:00:00");
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

    onViewAllClick(sectionType) {
        const today = new Date().toISOString().split('T')[0];
        let domain = [["stage_id.fold", "=", false]];
        
        switch (sectionType) {
            case "assigned":
                domain.push(["user_ids", "in", [this.userId]]);
                break;
            case "unassigned":
                domain.push(["user_ids", "=", false]);
                break;
            case "due_today":
                domain.push(["date_deadline", "=", today]);
                break;
            case "overdue":
                domain.push(["date_deadline", "<", today], ["date_deadline", "!=", false]);
                break;
            case "no_due_date":
                domain.push(["date_deadline", "=", false]);
                break;
            case "all_combined":
                // Show all tasks (service, event, CRM)
                break;
        }
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Tasks - ${sectionType}`,
            res_model: "project.task",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    getSectionTasks(sectionKey) {
        return this.props.tasks?.[sectionKey] || [];
    }

    getSectionCount(sectionKey) {
        return this.getSectionTasks(sectionKey).length;
    }
}

