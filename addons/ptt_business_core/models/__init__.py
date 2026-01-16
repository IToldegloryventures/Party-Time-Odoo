# IMPORTANT: Import order matters!
# Models with One2many fields must be loaded AFTER their comodels
# Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html

# 1. Base models (no dependencies on other PTT models)
from . import res_partner
from . import crm_stage
from . import product_product

# 2. CRM models
from . import crm_lead
from . import ptt_crm_service_line
from . import ptt_crm_vendor_assignment

# 3. Vendor assignment model (MUST load BEFORE project_project which has One2many to it)
from . import ptt_project_vendor_assignment

# 4. Project models (depends on ptt_project_vendor_assignment for One2many)
from . import project_project
from . import project_task

# 5. Sale models
from . import sale_order
from . import sale_order_line

# 6. Purchase models
from . import purchase_order

# 7. Wizards/Transient models
from . import ptt_variant_pricing_config


