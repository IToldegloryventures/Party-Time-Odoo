# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System
# Models must be loaded in order - comodels before One2many parents
# NOTE: Constants are in ptt_business_core/constants.py (addon root)

from . import mail_mail  # Email kill switch - MUST BE FIRST
from . import res_partner  # Partner extensions
from . import ptt_crm_vendor_estimate  # CRM vendor estimates (before crm_lead)
from . import ptt_crm_service_line  # CRM service lines (before crm_lead)
from . import ptt_project_vendor_assignment  # Project vendor assignments (before project)
from . import crm_stage  # CRM stage extensions
from . import crm_lead  # CRM lead extensions
from . import project_project  # Project extensions
from . import project_task  # Task event tracking
from . import product_product  # Product variant extensions (ptt_min_hours, pricing guides)
from . import sale_order  # Sale order CRM automation
from . import sale_order_line  # Sale order line min hours validation
from . import purchase_order  # Purchase order event tracking


