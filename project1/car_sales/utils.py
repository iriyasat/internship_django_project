from django.db import models
from .models import EmployeeHierarchy

def get_subordinate_ids(employee_id):
    """
    Returns the list of employee IDs who report directly or indirectly to the given employee_id.
    """
    if not employee_id:
        return []
    return list(EmployeeHierarchy.objects.filter(
        models.Q(supervisor_id=employee_id) |
        models.Q(supervisor2_id=employee_id) |
        models.Q(supervisor3_id=employee_id) |
        models.Q(supervisor4_id=employee_id) |
        models.Q(supervisor5_id=employee_id)
    ).values_list('employee_id', flat=True))

def is_manager(employee_id):
    """
    Checks if the employee is a manager. An employee is a manager if:
    1. They have any subordinates in the hierarchy.
    2. Or their role name contains 'manager' or 'admin'.
    """
    if not employee_id:
        return False
        
    # Check if they have subordinates in the hierarchy
    try:
        if EmployeeHierarchy.objects.exclude(models.Q(supervisor_id__isnull=True) & models.Q(supervisor_id=None)).exists():
            has_subordinates = EmployeeHierarchy.objects.filter(
                models.Q(supervisor_id=employee_id) |
                models.Q(supervisor2_id=employee_id) |
                models.Q(supervisor3_id=employee_id) |
                models.Q(supervisor4_id=employee_id) |
                models.Q(supervisor5_id=employee_id)
            ).exists()
            if has_subordinates:
                return True
    except Exception:
        pass
        
    # Check the employee's role name
    try:
        from .models import Employee
        employee = Employee.objects.select_related('employee_role').get(employee_id=employee_id)
        role_name = employee.employee_role.role_name.lower()
        return "manager" in role_name or "admin" in role_name
    except Exception:
        return False

def get_country_store_ids(country_id):
    """
    Returns a list of store_ids that belong to the given country_id.
    """
    from .models import Store
    return list(Store.objects.filter(country_id=country_id).values_list('store_id', flat=True))

def get_user_filters(request, profile):
    """
    Determines store_id and employee_id filters based on the role hierarchy.

    Role access levels:
    - Regional Sales Manager (L1): country-level → store_id = list of all stores in their country
    - Branch Manager (L2):         store-level   → store_id = their store, employee_id = None
    - Sales Manager (L3):          store-level   → store_id = their store, employee_id = None
    - Showroom Manager (L4):       store-level   → store_id = their store, employee_id = None
    - Fleet Sales Specialist (L4): store-level   → store_id = their store, employee_id = None
    - Senior Sales Executive (L5): store-level   → store_id = their store, employee_id = None
    - Finance & Insurance Officer (L5): store-level → store_id = their store, employee_id = None
    - Customer Relations Officer (L5):  store-level → store_id = their store, employee_id = None
    - Sales Executive (L6):        own data only → store_id = their store, employee_id = [self]
    - Pre-Owned Vehicle Specialist (L7): own data only → store_id = their store, employee_id = [self]
    """
    store_id = None
    employee_id = None

    if profile and not request.user.is_superuser:
        role = profile.employee_role.role_name if profile.employee_role else ""

        # L1 — Regional Sales Manager: country-level access
        if role == "Regional Sales Manager":
            country_store_ids = get_country_store_ids(profile.country_id)
            # None means "no filter" (global). A list restricts to those stores.
            # If somehow no stores found, fall back to their own store.
            store_id = country_store_ids if country_store_ids else [profile.store.store_id]
            return store_id, None

        # Roles with store-level access (can see all data within their assigned store)
        store_level_roles = [
            "Branch Manager",            # L2
            "Sales Manager",             # L3
            "Showroom Manager",          # L4
            "Fleet Sales Specialist",    # L4
            "Senior Sales Executive",    # L5
            "Finance & Insurance Officer",  # L5
            "Customer Relations Officer",   # L5 (previously global; now store-level)
        ]
        if role in store_level_roles:
            return profile.store.store_id, None

        # Roles with own-data-only access (Sales Executive L6, Pre-Owned Vehicle Specialist L7)
        # These can see only their own records within their store.
        store_id = profile.store.store_id
        employee_id = [profile.employee_id]

    return store_id, employee_id
