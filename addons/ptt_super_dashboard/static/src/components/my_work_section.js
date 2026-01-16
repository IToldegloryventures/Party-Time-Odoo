/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * MyWorkSection Component
 * 
 * Displays tasks categorized by due date:
 * - Today
 * - Overdue
 * - Upcoming
 * - Unscheduled
 * 
 * Each task is clickable and opens the project.task form in the Project app.
 */
export class MyWorkSection extends Component {
    static template = "ptt_operational_dashboard.MyWorkSection";
    static props = {
        tasks: { type: Object },
    };

    setup() {
        this.action = useService("action");
    }

    get categories() {
        return [
            { id: "overdue", label: "Overdue", icon: "fa-exclamation-circle" },
            { id: "today", label: "Today", icon: "fa-clock-o" },
            { id: "upcoming", label: "Upcoming", icon: "fa-calendar" },
            { id: "unscheduled", label: "Unscheduled", icon: "fa-inbox" },
        ];
    }

    getCategoryTasks(categoryId) {
        return this.props.tasks[categoryId] || [];
    }

    getCategoryCount(categoryId) {
        return this.getCategoryTasks(categoryId).length;
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return "Today";
        if (diffDays === 1) return "Tomorrow";
        if (diffDays === -1) return "Yesterday";
        if (diffDays < -1) return `${Math.abs(diffDays)} days ago`;
        if (diffDays < 7) return `In ${diffDays} days`;
        
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    isOverdue(dateStr) {
        if (!dateStr) return false;
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return date < today;
    }

    onTaskClick(task) {
        // Deep link to project.task form with return context
        if (task.action) {
            // Add breadcrumb context to show this came from dashboard
            const actionWithContext = {
                ...task.action,
                context: {
                    ...(task.action.context || {}),
                    active_id: task.id,
                    from_dashboard: true,
                    return_action: "ptt_home_hub",
                },
            };
            this.action.doAction(actionWithContext);
        }
    }

    onProjectClick(ev, task) {
        ev.stopPropagation();
        // Deep link to project.project form
        if (task.project_action) {
            this.action.doAction(task.project_action);
        }
    }

    onViewAllClick(categoryId) {
        // Open filtered list of tasks in Project app
        const today = new Date().toISOString().split('T')[0];
        let domain = [];
        
        switch (categoryId) {
            case "overdue":
                domain = [["date_deadline", "<", today], ["stage_id.fold", "=", false]];
                break;
            case "today":
                domain = [["date_deadline", "=", today], ["stage_id.fold", "=", false]];
                break;
            case "upcoming":
                domain = [["date_deadline", ">", today], ["stage_id.fold", "=", false]];
                break;
            case "unscheduled":
                domain = [["date_deadline", "=", false], ["stage_id.fold", "=", false]];
                break;
        }
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `My ${categoryId.charAt(0).toUpperCase() + categoryId.slice(1)} Tasks`,
            res_model: "project.task",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: { search_default_my_tasks: 1 },
            target: "current",
        });
    }
}

