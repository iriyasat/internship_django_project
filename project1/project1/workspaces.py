"""Workspace helpers for separating car sales and ecommerce access."""

CAR_SALES_ADMIN_USERNAME = "admin"
ECOMMERCE_ADMIN_USERNAME = "ihriyasat"

CAR_SALES_USERNAME_PREFIXES = ("emp_", "car_sales_")
ECOMMERCE_USERNAME_PREFIXES = ("cust_", "ecomm_")


def _resolve_username(user_or_username):
    if user_or_username is None:
        return ""
    if isinstance(user_or_username, str):
        return user_or_username.strip().lower()
    return str(getattr(user_or_username, "username", "") or "").strip().lower()


def get_workspace_for_username(username):
    username = _resolve_username(username)
    if not username:
        return None
    if username == ECOMMERCE_ADMIN_USERNAME or username.startswith(ECOMMERCE_USERNAME_PREFIXES):
        return "ecommerce"
    if username == CAR_SALES_ADMIN_USERNAME or username.startswith(CAR_SALES_USERNAME_PREFIXES):
        return "car_sales"
    return None


def get_workspace_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return None
    workspace = get_workspace_for_username(user)
    if workspace:
        return workspace
    if getattr(user, "is_staff", False):
        return "car_sales"
    return "ecommerce"


def is_car_sales_workspace_user(user):
    return get_workspace_for_user(user) == "car_sales"


def is_customer_workspace_user(user):
    return get_workspace_for_user(user) == "ecommerce"


def is_car_sales_admin_user(user):
    username = _resolve_username(user)
    return get_workspace_for_user(user) == "car_sales" and (
        username == CAR_SALES_ADMIN_USERNAME or username.startswith("car_sales_")
    )


def is_ecommerce_admin_user(user):
    username = _resolve_username(user)
    return get_workspace_for_user(user) == "ecommerce" and (
        username == ECOMMERCE_ADMIN_USERNAME or username.startswith("ecomm_")
    )


def is_workspace_path_allowed(workspace, path):
    path = path or ""
    if not path.startswith("/"):
        return False
    if workspace == "car_sales":
        return path.startswith((
            "/dashboard/",
            "/employees/",
            "/countries/",
            "/cities/",
            "/stores/",
            "/emproles/",
            "/hierarchy/",
            "/statuses/",
            "/industry/",
            "/vehicles/",
            "/inventory/",
            "/customers/",
            "/sales/",
            "/budgets/",
            "/admin-panel/",
            "/api/",
            "/api-page/",
        ))
    if workspace == "ecommerce":
        return path.startswith((
            "/catalog/",
            "/category/",
            "/vehicle/",
            "/compare/",
            "/wishlist/",
            "/cart/",
            "/test-drive/",
            "/checkout/",
            "/orders/",
            "/profile/",
            "/api/",
            "/ecommerce/",
        ))
    return False
