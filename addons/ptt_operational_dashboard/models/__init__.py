# PTT Operational Dashboard Models

# New Home Hub models
from . import ptt_personal_todo
from . import ptt_home_data
from . import project_task_inherit
from . import ptt_dashboard_config
# NOTE: Dashboard Editor models (ptt_dashboard_metric_config, ptt_dashboard_layout_config) 
# removed in v19.0.1.0.3 - Phase 2 feature, will be reintroduced later

# Existing dashboard models
from . import ptt_dashboard_widget
from . import ptt_sales_rep
from . import ptt_sales_commission

# Model inheritance
from . import account_move_inherit
from . import crm_lead_inherit
from . import project_project_inherit
from . import sale_order_inherit
