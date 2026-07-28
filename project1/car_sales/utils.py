from django.db import models


def is_manager(employee_id):
    """
    Checks if the employee is a manager.
    Currently bypassed to return True for any authenticated employee to remove navigation and feature restrictions.
    """
    if not employee_id:
        return False
    return True

def get_country_store_ids(country_id):
    """
    Returns a list of store_ids that belong to the given country_id.
    """
    from .models import Store
    return list(Store.objects.filter(country_id=country_id).values_list('store_id', flat=True))

def get_user_filters(request, profile):
    """
    Determines store_id and employee_id filters dynamically.
    Currently returns (None, None) to remove data scoping restrictions, allowing full cross-data visibility.
    """
    return None, None

def employee_context(request):
    if not request.user.is_authenticated:
        return {}
        
    from .auth import get_employee_profile
    profile = get_employee_profile(request)
    
    return {
        'employee_profile': profile,
        'access_level': 'global',
        'is_manager': True,
        'is_admin': True,
    }
