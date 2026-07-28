from django.db import models


# ─────────────────────────────────────────────
# Level resolution helpers
# ─────────────────────────────────────────────

def get_employee_level(employee_id):
    """
    Returns the employee's hierarchy level (1-9) from EmployeeHierarchy.
    Returns None if the employee has no hierarchy record (e.g. superuser).
    """
    if not employee_id:
        return None
    from .models import EmployeeHierarchy
    try:
        eh = EmployeeHierarchy.objects.get(employee_id=employee_id)
        return eh.level_id
    except EmployeeHierarchy.DoesNotExist:
        return None


def get_employee_store_id(employee_id):
    """Returns the store_id of the given employee."""
    from .models import Employee
    try:
        return Employee.objects.get(pk=employee_id).store_id
    except Employee.DoesNotExist:
        return None


def get_regional_manager_store_ids(employee_id):
    """
    For a Regional Sales Manager (Level 7): finds all Branch Managers (Level 6)
    who list this employee as their supervisor in EmployeeHierarchy, then returns
    a list of all their store_ids.
    """
    from .models import EmployeeHierarchy, Employee
    # Find all hierarchy entries where this person is the direct supervisor
    subordinate_ids = EmployeeHierarchy.objects.filter(
        supervisor_id=employee_id
    ).values_list('employee_id', flat=True)
    # Collect unique store_ids from those subordinates
    store_ids = list(
        Employee.objects.filter(employee_id__in=subordinate_ids)
        .values_list('store_id', flat=True)
        .distinct()
    )
    return store_ids


def is_manager(employee_id):
    """
    Returns True if the employee is a supervisor (Level 1–8).
    Level 9 employees (Sales Exec / Senior Sales Exec) are not managers.
    Superuser status is handled separately via request.user.is_superuser.
    """
    level = get_employee_level(employee_id)
    if level is None:
        return False
    return 1 <= level <= 8


def can_delete(level):
    """Returns True if the given level is authorised to delete records (Levels 1–4)."""
    return level is not None and 1 <= level <= 4


def get_country_store_ids(country_id):
    """Returns a list of store_ids that belong to the given country_id."""
    from .models import Store
    return list(Store.objects.filter(country_id=country_id).values_list('store_id', flat=True))


# ─────────────────────────────────────────────
# Data scoping
# ─────────────────────────────────────────────

def get_user_filters(request, profile):
    """
    Returns (store_ids, employee_ids) filter tuples based on the employee's level.

    Scoping rules:
      Level 9  → personal only    : employee_id filter = [own id]
      Level 8  → own store        : store_id filter = [own store]
      Level 7  → stores under them: store_id filter = [subordinate stores]
      Level 6  → own store        : store_id filter = [own store]
      Level 1–5→ global           : no filter
      Superuser→ global           : no filter (handled before this is called)
    """
    if not profile:
        return None, None

    level = get_employee_level(profile.employee_id)

    if level == 9:
        return None, [profile.employee_id]

    if level in (6, 8):
        store_id = get_employee_store_id(profile.employee_id)
        return ([store_id] if store_id else None), None

    if level == 7:
        store_ids = get_regional_manager_store_ids(profile.employee_id)
        return (store_ids if store_ids else None), None

    # Levels 1–5 and anything else: global access
    return None, None


# ─────────────────────────────────────────────
# Context processor (navbar / template flags)
# ─────────────────────────────────────────────

def employee_context(request):
    if not request.user.is_authenticated:
        return {}

    # Superuser gets full unrestricted access regardless of employee profile
    if request.user.is_superuser:
        from .auth import get_employee_profile
        profile = get_employee_profile(request)
        return {
            'employee_profile': profile,
            'access_level': 'global',
            'is_manager': True,
            'is_admin': True,
        }

    from .auth import get_employee_profile
    profile = get_employee_profile(request)
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
    }
