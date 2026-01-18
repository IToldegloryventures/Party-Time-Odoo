# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System
# Models must be loaded in order - comodels before One2many parents

from . import res_partner  # Partner extensions
from . import ptt_crm_vendor_estimate  # CRM vendor estimates (before crm_lead)
from . import ptt_crm_service_line  # CRM service lines (before crm_lead)
from . import ptt_project_vendor_assignment  # Project vendor assignments (before project)
from . import crm_lead  # CRM lead extensions
from . import project_project  # Project extensions
from . import product_product  # Product variant extensions (ptt_min_hours, pricing guides)
from . import sale_order_line  # Sale order line min hours validation


