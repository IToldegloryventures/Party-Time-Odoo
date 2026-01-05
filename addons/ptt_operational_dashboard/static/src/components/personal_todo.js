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
        this.homeService = useService("ptt_home");
        this.state = useState({
            newTodoName: "",
            loading: false,
        });
    }

    get allTodos() {
        const todos = this.props.todos || {};
        return [
            ...(todos.overdue || []),
            ...(todos.today || []),
            ...(todos.upcoming || []),
            ...(todos.unscheduled || []),
        ];
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    async onToggleTodo(todo) {
        this.state.loading = true;
        try {
            await this.homeService.togglePersonalTodo(todo.id);
            this.props.onRefresh();
        } finally {
            this.state.loading = false;
        }
    }

    async onDeleteTodo(ev, todo) {
        ev.stopPropagation();
        this.state.loading = true;
        try {
            await this.homeService.deletePersonalTodo(todo.id);
            this.props.onRefresh();
        } finally {
            this.state.loading = false;
        }
    }

    async onAddTodo() {
        const name = this.state.newTodoName.trim();
        if (!name) return;
        
        this.state.loading = true;
        try {
            await this.homeService.createPersonalTodo(name);
            this.state.newTodoName = "";
            this.props.onRefresh();
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

