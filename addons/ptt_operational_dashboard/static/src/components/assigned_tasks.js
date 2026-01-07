/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * AssignedTasks Component (Other Tasks)
 * 
 * Displays one-off/miscellaneous tasks that are NOT from event projects.
 * Includes quick "Add Task" functionality for bosses to assign tasks to staff.
 */
export class AssignedTasks extends Component {
    static template = "ptt_operational_dashboard.AssignedTasks";
    static props = {
        tasks: { type: Array },
    };

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            showAddForm: false,
            newTaskName: "",
            newTaskUserId: "",
            newTaskDueDate: "",
            users: [],
            creating: false,
        });
        
        onWillStart(async () => {
            await this.loadUsers();
        });
    }

    async loadUsers() {
        try {
            this.state.users = await this.orm.call(
                "ptt.home.data",
                "get_assignable_users",
                []
            );
        } catch (e) {
            console.error("Failed to load users:", e);
        }
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

    onAddTaskClick() {
        this.state.showAddForm = true;
        this.state.newTaskName = "";
        this.state.newTaskUserId = "";
        this.state.newTaskDueDate = "";
    }

    onCancelAdd() {
        this.state.showAddForm = false;
    }

    onTaskNameKeyup(ev) {
        if (ev.key === "Enter" && this.state.newTaskName.trim()) {
            this.onCreateTask();
        }
        if (ev.key === "Escape") {
            this.onCancelAdd();
        }
    }

    async onCreateTask() {
        if (!this.state.newTaskName.trim()) {
            this.notification.add("Please enter a task name", { type: "warning" });
            return;
        }
        
        this.state.creating = true;
        try {
            const result = await this.orm.call(
                "ptt.home.data",
                "create_quick_task",
                [],
                {
                    name: this.state.newTaskName.trim(),
                    user_id: this.state.newTaskUserId ? parseInt(this.state.newTaskUserId) : null,
                    date_deadline: this.state.newTaskDueDate || null,
                }
            );
            
            this.notification.add(`Task "${result.name}" created!`, { type: "success" });
            this.state.showAddForm = false;
            
            // Trigger refresh of parent
            window.location.reload(); // Simple refresh for now
        } catch (e) {
            console.error("Failed to create task:", e);
            this.notification.add("Failed to create task", { type: "danger" });
        } finally {
            this.state.creating = false;
        }
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
        if (task.project_action) {
            this.action.doAction(task.project_action);
        }
    }

    onViewAllClick() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Other Tasks",
            res_model: "project.task",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: [["stage_id.fold", "=", false]],
            context: { search_default_my_tasks: 1 },
            target: "current",
        });
    }
}
