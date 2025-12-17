/** @odoo-module **/

import { mount, whenReady } from "@odoo/owl";
import { Playground } from "./playground/playground";

/**
 * Entry point for the Awesome Owl playground.
 *
 * This script runs on frontend pages and mounts the Playground
 * component only when the dedicated root element is present.
 */
whenReady(() => {
    const root = document.getElementById("awesome_owl_root");
    if (!root) {
        return;
    }
    const env = {};
    mount(Playground, root, { env });
});


