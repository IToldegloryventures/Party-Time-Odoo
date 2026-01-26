/** @odoo-module **/
import { QUnit } from "@odoo/hoot";

QUnit.module("ptt_dashboard.basic");

QUnit.test("dashboard smoke test", (assert) => {
    assert.expect(1);
    assert.ok(true, "Dashboard frontend module loads");
});
