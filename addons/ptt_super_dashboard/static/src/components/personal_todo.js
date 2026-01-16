/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * PersonalTodo Component
 * 
 * Personal to-do list with add/complete/delete functionality.
 * This is the only component that manages its own data (ptt.personal.todo).
 */
export class PersonalTodo extends Component {
    static template = "ptt_operational_dashboard.PersonalTodo";
    static props = {
        todos: { type: Object },
        onRefresh: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            newTodoName: "",
            loading: false,
            localTodos: [],  // Local state for immediate UI feedback
        });
    }

    get allTodos() {
        const todos = this.props.todos || {};
        // Combine with any locally added todos for immediate feedback
        const serverTodos = [
            ...(todos.overdue || []),
            ...(todos.today || []),
            ...(todos.upcoming || []),
            ...(todos.unscheduled || []),
        ];
        // Add local todos that aren't yet from server
        const serverIds = new Set(serverTodos.map(t => t.id));
        const localOnly = this.state.localTodos.filter(t => !serverIds.has(t.id));
        return [...localOnly, ...serverTodos];
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    isTempId(id) {
        return String(id).startsWith('temp_');
    }

    async onToggleTodo(todo) {
        if (this.state.loading) return;
        this.state.loading = true;
        try {
            await this.orm.call("ptt.personal.todo", "action_toggle_done", [[todo.id]]);
            await this.props.onRefresh();
        } catch (e) {
            console.error("Failed to toggle todo:", e);
            this.notification.add("Failed to update to-do", { type: "warning" });
        } finally {
            this.state.loading = false;
        }
    }

    async onDeleteTodo(ev, todo) {
        ev.stopPropagation();
        if (this.state.loading) return;
        this.state.loading = true;
        try {
            await this.orm.unlink("ptt.personal.todo", [todo.id]);
            // Remove from local state immediately
            this.state.localTodos = this.state.localTodos.filter(t => t.id !== todo.id);
            await this.props.onRefresh();
        } catch (e) {
            console.error("Failed to delete todo:", e);
            this.notification.add("Failed to delete to-do", { type: "warning" });
        } finally {
            this.state.loading = false;
        }
    }

    async onAddTodo() {
        const name = this.state.newTodoName.trim();
        if (!name || this.state.loading) return;
        
        this.state.loading = true;
        const tempId = `temp_${Date.now()}`;
        
        // Add to local state immediately for UI feedback
        this.state.localTodos.push({
            id: tempId,
            name: name,
            due_date: false,
            priority: "1",
        });
        this.state.newTodoName = "";
        
        try {
            const ids = await this.orm.create("ptt.personal.todo", [{ name, priority: "1" }]);
            // Replace temp ID with real ID
            const todoIndex = this.state.localTodos.findIndex(t => t.id === tempId);
            if (todoIndex !== -1) {
                this.state.localTodos[todoIndex].id = ids[0];
            }
            this.notification.add(`To-do "${name}" added!`, { type: "success" });
            // Refresh in background without blocking UI
            this.props.onRefresh().catch(() => {});
        } catch (e) {
            console.error("Failed to create todo:", e);
            // Remove the temp item on failure
            this.state.localTodos = this.state.localTodos.filter(t => t.id !== tempId);
            this.state.newTodoName = name;  // Restore the input
            this.notification.add("Failed to create to-do. Please try again.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    onKeyPress(ev) {
        if (ev.key === "Enter") {
            this.onAddTodo();
        }
    }

    onInputChange(ev) {
        this.state.newTodoName = ev.target.value;
    }
}

