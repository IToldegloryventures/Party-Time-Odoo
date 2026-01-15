/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * AssignedComments Component
 * 
 * Displays comments/messages where the current user is mentioned.
 * Each comment is clickable and opens the source record (any model).
 */
export class AssignedComments extends Component {
    static template = "ptt_operational_dashboard.AssignedComments";
    static props = {
        comments: { type: Array },
    };

    setup() {
        this.action = useService("action");
    }

    getAuthorInitials(authorName) {
        if (!authorName) return "?";
        const parts = authorName.split(" ");
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return authorName.substring(0, 2).toUpperCase();
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    getModelLabel(model) {
        const labels = {
            "project.task": "Task",
            "project.project": "Project",
            "crm.lead": "Lead",
            "sale.order": "Quote",
            "account.move": "Invoice",
            "res.partner": "Contact",
        };
        return labels[model] || model;
    }

    stripHtml(html) {
        if (!html) return "";
        // Create a temporary element to parse HTML
        const tmp = document.createElement("div");
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || "";
    }

    truncateText(text, maxLength = 100) {
        if (!text) return "";
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + "...";
    }

    onCommentClick(comment) {
        if (comment.action) {
            this.action.doAction(comment.action);
        }
    }
}

