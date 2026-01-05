{
    "name": "PTT Operational Dashboard",
    "version": "19.0.1.0.0",
    "summary": "Party Time Texas operational dashboard with KPIs and quick actions",
    "category": "Customizations",
    "author": "Party Time Texas",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ptt_dashboard_views.xml",
        "views/ptt_dashboard_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ptt_operational_dashboard/static/src/dashboard_controller.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}

