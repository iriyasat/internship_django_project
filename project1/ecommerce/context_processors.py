from types import SimpleNamespace
from django.db import connection
from .views import get_customer_from_request


def customer_context(request):
    """
    Global template context processor to supply authenticated customer info
    (including profile picture) across all pages and views.
    """
    if not (hasattr(request, 'user') and request.user.is_authenticated):
        return {}

    try:
        customer = get_customer_from_request(request)
        if not customer:
            return {}

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.profile_picture,
                       c.city_id, c.city_name, co.country_id, co.country_name
                FROM customer_info ci
                LEFT JOIN city c ON ci.city_id = c.city_id
                LEFT JOIN country co ON ci.country_id = co.country_name
                WHERE ci.customer_id = %s
            """, [customer.customer_id])
            ci_row = cursor.fetchone()

        if not ci_row:
            return {}

        profile_picture = ci_row[4] if ci_row and ci_row[4] else None
        profile_picture_url = f"/media/{profile_picture}" if profile_picture else None

        customer_info = SimpleNamespace(
            firstname=ci_row[0] or '',
            lastname=ci_row[1] or '',
            customer_status=ci_row[2] or 'Active',
            customer_address=ci_row[3] or '',
            profile_picture=profile_picture,
            profile_picture_url=profile_picture_url,
            city=SimpleNamespace(city_id=ci_row[5], city_name=ci_row[6]) if ci_row[5] else None,
            country=SimpleNamespace(country_id=ci_row[7], country_name=ci_row[8]) if ci_row[7] else None,
        )

        return {
            'customer_info': customer_info,
        }
    except Exception:
        return {}
