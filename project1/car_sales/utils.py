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
    3. Or their role is explicitly marked as a manager in the database.
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
        
    # Check the employee's role name and db settings
    try:
        from .models import Employee
        employee = Employee.objects.select_related('employee_role').get(employee_id=employee_id)
        if employee.employee_role:
            if employee.employee_role.access_level in ('country', 'store'):
                return True
            role_name = employee.employee_role.role_name.lower()
            return "manager" in role_name or "admin" in role_name
    except Exception:
        pass
    return False

def get_country_store_ids(country_id):
    """
    Returns a list of store_ids that belong to the given country_id.
    """
    from .models import Store
    return list(Store.objects.filter(country_id=country_id).values_list('store_id', flat=True))

def get_user_filters(request, profile):
    """
    Determines store_id and employee_id filters based on the role hierarchy dynamically.
    """
    store_id = None
    employee_id = None

    # Superusers and Django staff are the Country Head / administrator accounts.
    # We do not let employee-based users who have in-memory is_staff=True bypass
    # these filters, keeping them restricted to their dynamic role configuration.
    is_admin = request.user.is_superuser or (request.user.is_staff and not request.user.username.startswith('emp_'))

    if profile and not is_admin:
        role = profile.employee_role
        if not role:
            # If an employee has no role, restrict to empty scope
            return [], []

        access_level = role.access_level

        # Country-level access
        if access_level == 'country':
            country_store_ids = get_country_store_ids(profile.country_id)
            # If somehow no stores found, fall back to their own store.
            store_id = country_store_ids if country_store_ids else [profile.store.store_id]
            return store_id, None

        # Store-level access
        elif access_level == 'store':
            return profile.store.store_id, None

        # Own-data-only access
        elif access_level == 'own':
            store_id = profile.store.store_id
            employee_id = [profile.employee_id]
            return store_id, employee_id

        # Unknown access level
        return [], []

    if not is_admin:
        return [], []
    return store_id, employee_id
