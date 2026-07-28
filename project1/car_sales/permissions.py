"""
Role-Based Access Control (RBAC) & Hierarchy Management System.

Single source of truth for:
1. Hierarchy level resolution & supervisor lookups (Raw SQL)
2. Action-level CRUD permission handlers
3. Row-level record visibility handlers (Raw SQL)
4. Data scoping filters for queries
5. Navigation context processor flags
"""

from django.db import connections

# Master admin-only models reserved exclusively for Django Superusers
ADMIN_ONLY_MODELS = {'Country', 'City', 'EmployeeRole', 'EmployeeStatus', 'IndustryInfo'}


# ─────────────────────────────────────────────
# 1. Hierarchy Level Resolution & Helpers (Raw SQL)
# ─────────────────────────────────────────────

def get_employee_level(employee_id):
    """
    Returns the employee's hierarchy level (1-9) from employee_hierarchy using Raw SQL.
    Returns None if the employee has no hierarchy record (e.g. superuser).
    """
    if not employee_id:
        return None
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT level FROM employee_hierarchy WHERE employee_id = %s LIMIT 1", [employee_id])
        row = cursor.fetchone()
        return row[0] if row else None


def get_employee_store_id(employee_id):
    """Returns the store_id of the given employee using Raw SQL."""
    if not employee_id:
        return None
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT store_id FROM employee WHERE employee_id = %s LIMIT 1", [employee_id])
        row = cursor.fetchone()
        return row[0] if row else None


def get_regional_manager_store_ids(employee_id):
    """
    For a Regional Sales Manager (Level 7): finds all Branch Managers (Level 6)
    who list this employee as their supervisor in employee_hierarchy, then returns
    a list of all their store_ids using Raw SQL.
    """
    if not employee_id:
        return []
    with connections['default'].cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT e.store_id
            FROM employee_hierarchy eh
            JOIN employee e ON eh.employee_id = e.employee_id
            WHERE eh.supervisor_id = %s AND e.store_id IS NOT NULL
        """, [employee_id])
        return [row[0] for row in cursor.fetchall()]


def is_manager(employee_id):
    """
    Returns True if the employee is a supervisor (Level 1–8).
    Level 9 employees (Sales Exec / Senior Sales Exec) are not managers.
    """
    level = get_employee_level(employee_id)
    if level is None:
        return False
    return 1 <= level <= 8


def can_delete(level):
    """Returns True if the given level is authorised to delete records (Levels 1–4)."""
    return level is not None and 1 <= level <= 4


def get_country_store_ids(country_id):
    """Returns a list of store_ids that belong to the given country_id using Raw SQL."""
    if not country_id:
        return []
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT store_id FROM store WHERE country_id = %s", [country_id])
        return [row[0] for row in cursor.fetchall()]


# ─────────────────────────────────────────────
# 2. Level-Specific Data Scoping Filters
# ─────────────────────────────────────────────

def get_level_9_user_filters(profile):
    """Level 9 Data Scoping: Personal sales data only."""
    return None, [profile.employee_id]


def get_level_6_8_user_filters(profile):
    """Levels 6 & 8 Data Scoping: Assigned store branch only."""
    store_id = get_employee_store_id(profile.employee_id)
    return ([store_id] if store_id else None), None


def get_level_7_user_filters(profile):
    """Level 7 Data Scoping: Regional stores under supervision."""
    store_ids = get_regional_manager_store_ids(profile.employee_id)
    return (store_ids if store_ids else None), None


def get_level_1_5_user_filters(profile):
    """Levels 1–5 Data Scoping: Global unrestricted access across all stores."""
    return None, None


LEVEL_FILTER_DISPATCH = {
    1: get_level_1_5_user_filters,
    2: get_level_1_5_user_filters,
    3: get_level_1_5_user_filters,
    4: get_level_1_5_user_filters,
    5: get_level_1_5_user_filters,
    6: get_level_6_8_user_filters,
    7: get_level_7_user_filters,
    8: get_level_6_8_user_filters,
    9: get_level_9_user_filters,
}


def get_user_filters(request, profile):
    """
    Main dispatcher for retrieving (store_ids, employee_ids) filter tuples.
    """
    if not profile:
        return None, None

    level = get_employee_level(profile.employee_id)
    if not level:
        return None, None

    handler = LEVEL_FILTER_DISPATCH.get(level, get_level_1_5_user_filters)
    return handler(profile)


# ─────────────────────────────────────────────
# 3. Action-Level CRUD Permission Handlers
# ─────────────────────────────────────────────

def check_level_1_4_crud_permission(model_name, action, data=None):
    """
    Levels 1–4 (Senior Management / Executive Tier):
    - Full CRUD access across all operational models.
    - Master system configurations (Admin models) require Superuser.
    """
    if model_name in ADMIN_ONLY_MODELS:
        return False, f"Permission denied. Only system administrators can modify {model_name}."
    return True, None


def check_level_5_8_crud_permission(model_name, action, data=None):
    """
    Levels 5–8 (Store & Regional Managers, Supervisors, Team Leads):
    - GET (Read): Scoped by assigned store/region.
    - POST (Create): Can create Sales, Invoices, Inventory items, Budgets, and Employee records.
    - PUT (Update): Can update Inventory, Budgets, and Employee profiles within scope.
    - DELETE (Remove): Strictly forbidden (restricted to Levels 1–4).
    """
    if model_name in ADMIN_ONLY_MODELS:
        return False, f"Permission denied. Only system administrators can modify {model_name}."

    if action == 'DELETE':
        return False, f"Permission denied. Only senior management (Levels 1–4) can delete {model_name} records."

    if action == 'PUT':
        if model_name in ('SellingInfo', 'Invoice'):
            return False, f"Permission denied. Once created, {model_name} records can only be modified by senior management (Levels 1–4)."
        if model_name == 'Store':
            return False, "Permission denied. Only senior management (Levels 1–4) can modify store structures."

    return True, None


def check_level_9_crud_permission(model_name, action, data=None):
    """
    Level 9 (Sales Executives / Front-Line Sales Representatives):
    - GET (Read): Scoped to personal sales transactions and targets.
    - POST (Create): Allowed to create Sales contracts, Invoices, and Inventory intake items.
    - PUT (Update): Forbidden from editing existing Sales contracts, Invoices, Inventory items, Budgets, or Employees.
    - DELETE (Remove): Strictly forbidden.
    """
    if model_name in ADMIN_ONLY_MODELS:
        return False, f"Permission denied. Only system administrators can modify {model_name}."

    if action == 'DELETE':
        return False, f"Permission denied. Only senior management (Levels 1–4) can delete {model_name} records."

    if action == 'PUT':
        if model_name == 'SellingInfo':
            return False, "Permission denied. Sales Executives cannot edit existing sales records."
        if model_name == 'Invoice':
            return False, "Permission denied. Once created, invoices can only be modified by senior management (Levels 1–4)."
        if model_name == 'Inventory':
            return False, "Permission denied. Inventory updates require Manager status."
        if model_name in ('Employee', 'EmployeeBudget', 'Store'):
            return False, f"Permission denied. Sales Executives cannot edit {model_name} records."

    return True, None


LEVEL_CRUD_DISPATCH = {
    1: check_level_1_4_crud_permission,
    2: check_level_1_4_crud_permission,
    3: check_level_1_4_crud_permission,
    4: check_level_1_4_crud_permission,
    5: check_level_5_8_crud_permission,
    6: check_level_5_8_crud_permission,
    7: check_level_5_8_crud_permission,
    8: check_level_5_8_crud_permission,
    9: check_level_9_crud_permission,
}


# ─────────────────────────────────────────────
# 4. Row-Level Record Visibility Handlers (Raw SQL)
# ─────────────────────────────────────────────

def check_level_9_record_permission(model_name, record, profile):
    """Row-level permission check for Level 9 (Personal Scope)."""
    if model_name == 'SellingInfo':
        return record.get('employee') == profile.employee_id
    if model_name == 'CustomerInfo':
        customer_id = record.get('customer_id') or record.get('customer')
        if not customer_id:
            return False
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1 FROM selling_info WHERE customer_id = %s AND employee_id = %s LIMIT 1", [customer_id, profile.employee_id])
            return cursor.fetchone() is not None
    if model_name == 'EmployeeBudget':
        return record.get('employee') == profile.employee_id
    if model_name == 'Invoice':
        emp_val = record.get('employee_id') or record.get('employee')
        return emp_val == profile.employee_id
    return True


def check_level_6_8_record_permission(model_name, record, profile):
    """Row-level permission check for Levels 6 & 8 (Own Store Scope)."""
    own_store = get_employee_store_id(profile.employee_id)
    store_val = record.get('store') or record.get('store_id')
    if store_val is not None and own_store is not None:
        return int(store_val) == int(own_store)
    return True


def check_level_7_record_permission(model_name, record, profile):
    """Row-level permission check for Level 7 (Regional Stores Scope)."""
    allowed_stores = get_regional_manager_store_ids(profile.employee_id)
    store_val = record.get('store') or record.get('store_id')
    if store_val is not None and allowed_stores:
        return int(store_val) in [int(s) for s in allowed_stores]
    return True


LEVEL_RECORD_DISPATCH = {
    6: check_level_6_8_record_permission,
    7: check_level_7_record_permission,
    8: check_level_6_8_record_permission,
    9: check_level_9_record_permission,
}


# ─────────────────────────────────────────────
# 5. Navbar & Template Context Processor
# ─────────────────────────────────────────────

def employee_context(request):
    """
    Context processor populating employee_profile, access_level,
    is_manager, is_admin, and can_delete flags for templates.
    """
    if not request.user.is_authenticated:
        return {}

    from .auth import get_employee_profile
    profile = get_employee_profile(request)

    if request.user.is_superuser:
        return {
            'employee_profile': profile,
            'access_level': 'global',
            'is_manager': True,
            'is_admin': True,
            'can_delete': True,
        }

    if not profile:
        return {}

    level = get_employee_level(profile.employee_id)
    is_lvl9 = (level == 9)
    is_supervisor = (level is not None and 1 <= level <= 8)

    return {
        'employee_profile': profile,
        'access_level': 'personal' if is_lvl9 else 'global',
        'is_manager': is_supervisor,
        'is_admin': False,
        'can_delete': can_delete(level),
    }
