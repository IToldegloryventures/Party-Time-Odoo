# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


def post_init_hook(env):
    """Rename legacy templates to match the simplified event types.
    
    Odoo 19 signature: post_init_hook(env)
    """

    rename_map = {
        "ptt_project_management.template_corporate_conference": "Corporate Template",
        "ptt_project_management.template_casino_night": "Social Template",
    }

    for xmlid, new_name in rename_map.items():
        record = env.ref(xmlid, raise_if_not_found=False)
        if record and record.name != new_name:
            record.write({"name": new_name})
