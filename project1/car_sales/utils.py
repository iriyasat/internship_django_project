"""
Utility helpers for Car Sales application.

Hierarchy, scoping, and permission functions have been consolidated
into permissions.py and are imported here for clean re-export.
"""

from .permissions import (
    get_employee_level,
    get_employee_store_id,
    get_regional_manager_store_ids,
    is_manager,
    can_delete,
    get_country_store_ids,
    get_user_filters,
    employee_context,
)
