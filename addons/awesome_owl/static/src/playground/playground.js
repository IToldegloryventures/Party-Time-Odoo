/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

/**
 * Playground component for the Awesome Owl training module.
 *
 * For lesson 1, it behaves as a simple counter, matching the
 * example from the Odoo 19 Owl tutorial.
 */
export class Playground extends Component {
    static template = "awesome_owl.Playground";

    setup() {
        this.state = useState({ value: 0 });
    }

    increment() {
        this.state.value++;
    }
}


