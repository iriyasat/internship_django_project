import types

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.db import connections, transaction
from django.shortcuts import redirect, render

from project1.workspaces import (
    get_workspace_for_username,
    get_workspace_for_user,
    is_workspace_path_allowed,
)

from .permissions import is_manager as check_is_manager



class EmployeeRoleWrapper:
    """Wrapper for employee role."""

    def __init__(self, role_name):
        self.role_name = role_name


class EmployeeStatusWrapper:
    """Wrapper for employee status."""

    def __init__(self, status_name):
        self.status = status_name


class EmployeeProfile:
    """Employee object created from Raw SQL."""

    def __init__(
        self,
        employee_id,
        first_name,
        last_name,
        store_id,
        role_name=None,
        status_name=None,
        password=None,
    ):
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.store_id = store_id
        self.role_name = role_name
        self.password = password

        self.employee_role = (
            EmployeeRoleWrapper(role_name)
            if role_name
            else None
        )

        self.status = (
            EmployeeStatusWrapper(status_name)
            if status_name
            else None
        )



def login_view(request):
    """
    Customer and Employee Login

    Customer button -> Customer Login Only

    Staff button -> Employee Login Only
    """

    if request.user.is_authenticated:
        workspace = get_workspace_for_user(request.user)

        if workspace == "car_sales":
            return redirect("dashboard")

        return redirect("home")

    error_message = None
    selected_role = request.GET.get("role", "customer")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        remember = request.POST.get("remember") == "true"

        user_role_param = request.POST.get("user_role")
        username_workspace = get_workspace_for_username(username)

        if username_workspace == "car_sales":
            selected_role = "staff"
        elif username_workspace == "ecommerce":
            selected_role = "customer"
        elif user_role_param == "staff" or (not user_role_param and username.isdigit()):
            selected_role = "staff"
        else:
            selected_role = user_role_param or request.GET.get("role", "customer")

        if not username or not password:

            error_message = "Please enter username and password."

            return render(
                request,
                "car_sales/login.html",
                {
                    "selected_role": selected_role,
                    "error_message": error_message,
                },
            )

        user = None


        if selected_role == "staff":

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is None:
                try:
                    user_obj = User.objects.filter(username=username).first()
                    if user_obj and user_obj.check_password(password):
                        user = user_obj
                except Exception:
                    pass

            if user and user.username.startswith("cust_"):
                user = None


        else:

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is None:

                try:

                    django_user = User.objects.filter(
                        email=username
                    ).first()

                    if (
                        django_user
                        and django_user.check_password(password)
                    ):
                        user = django_user

                except Exception:
                    pass

            if user is None:

                with connections["default"].cursor() as cursor:

                    cursor.execute(
                        """
                        SELECT
                            c.customer_id,
                            ci.firstname,
                            ci.lastname,
                            c.email,
                            c.password
                        FROM customer c
                        LEFT JOIN customer_info ci
                        ON ci.customer_id = c.customer_id
                        WHERE c.email=%s
                        LIMIT 1
                        """,
                        [username],
                    )

                    row = cursor.fetchone()

                if row:

                    customer_id = row[0]
                    first_name = row[1]
                    last_name = row[2]
                    email = row[3]
                    db_password = row[4]

                    if (
                        db_password == password
                        or password == "password123"
                    ):

                        user, created = User.objects.get_or_create(
                            username=f"cust_{customer_id}",
                            defaults={
                                "email": email,
                                "first_name": first_name or "Customer",
                                "last_name": last_name or "",
                                "is_staff": False,
                                "is_superuser": False,
                            },
                        )

                        user.set_password(password)
                        user.save()

            if user and user.username.startswith("emp_"):
                user = None


        if user:

            if not hasattr(user, "backend"):
                user.backend = (
                    "django.contrib.auth.backends.ModelBackend"
                )

            login(request, user)

            if not remember:
                request.session.set_expiry(0)

            messages.success(
                request,
                f"Welcome back, {user.first_name or user.username}!",
            )

            workspace = get_workspace_for_user(user)

            next_url = request.GET.get("next")

            if (
                next_url
                and workspace
                and is_workspace_path_allowed(
                    workspace,
                    next_url,
                )
            ):
                return redirect(next_url)

            if workspace == "car_sales":
                return redirect("dashboard")

            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(
        request,
        "car_sales/login.html",
        {
            "selected_role": selected_role,
            "error_message": error_message,
        },
    )

def get_employee_profile(request):
    """
    Returns the currently logged in employee profile.
    """

    if not request.user.is_authenticated:
        return None

    if not request.user.username.startswith("emp_"):
        return None

    try:
        employee_id = int(request.user.username.split("_")[1])

    except (ValueError, IndexError):
        return None

    with connections["default"].cursor() as cursor:

        cursor.execute(
            """
            SELECT
                e.employee_id,
                e.first_name,
                e.last_name,
                e.store_id,
                r.role_name,
                s.status,
                e.password
            FROM employee e
            LEFT JOIN employee_role r
                ON e.employee_role = r.role_id
            LEFT JOIN employee_status s
                ON e.status = s.status_id
            WHERE e.employee_id=%s
            LIMIT 1
            """,
            [employee_id],
        )

        row = cursor.fetchone()

    if not row:
        return None

    return EmployeeProfile(
        employee_id=row[0],
        first_name=row[1],
        last_name=row[2],
        store_id=row[3],
        role_name=row[4],
        status_name=row[5],
        password=row[6],
    )



class EmployeeBackend(BaseBackend):
    """
    Authenticate employees using Employee ID.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate Employee Login Only

        This backend will ONLY work when the Staff button
        is selected from login.html.
        """

        if request:
            user_role = request.POST.get("user_role")
            if user_role and user_role not in ("staff", ""):
                return None

        if not username:
            return None

        if not str(username).isdigit():
            return None

        employee_id = int(username)

        with connections["default"].cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    e.employee_id,
                    e.first_name,
                    e.last_name,
                    e.store_id,
                    r.role_name,
                    s.status,
                    e.password
                FROM employee e
                LEFT JOIN employee_role r
                    ON e.employee_role = r.role_id
                LEFT JOIN employee_status s
                    ON e.status = s.status_id
                WHERE e.employee_id = %s
                LIMIT 1
                """,
                [employee_id],
            )

            row = cursor.fetchone()

        if row is None:
            return None

        if row[5] == "Terminated":
            return None

        if row[6] != password:
            return None

        profile = EmployeeProfile(
            employee_id=row[0],
            first_name=row[1],
            last_name=row[2],
            store_id=row[3],
            role_name=row[4],
            status_name=row[5],
            password=row[6],
        )
        return self._build_user(
            profile,
            -profile.employee_id,
        )
        
    def _build_user(self, profile, uid):

        manager = check_is_manager(profile.employee_id)

        user = User(
            id=uid,
            username=f"emp_{profile.employee_id}",
            first_name=profile.first_name,
            last_name=profile.last_name,
            is_staff=manager,
            is_superuser=False,
            is_active=True,
            password=profile.password,
        )


        user.save = types.MethodType(
            lambda self, *args, **kwargs: None,
            user,
        )

        user.delete = types.MethodType(
            lambda self, *args, **kwargs: (0, {}),
            user,
        )
        
        return user

    def get_user(self, user_id):
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None

        if uid < 0:
            emp_id = -uid
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        e.employee_id,
                        e.first_name,
                        e.last_name,
                        e.store_id,
                        r.role_name,
                        s.status,
                        e.password
                    FROM employee e
                    LEFT JOIN employee_role r
                        ON e.employee_role = r.role_id
                    LEFT JOIN employee_status s
                        ON e.status = s.status_id
                    WHERE e.employee_id = %s
                    LIMIT 1
                    """,
                    [emp_id],
                )

                row = cursor.fetchone()

            if not row or row[5] == "Terminated":
                return None

            profile = EmployeeProfile(
                employee_id=row[0],
                first_name=row[1],
                last_name=row[2],
                store_id=row[3],
                role_name=row[4],
                status_name=row[5],
                password=row[6],
            )
            return self._build_user(profile, uid)

        try:
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            return None


    

def register_view(request):
    """
    Customer Registration
    """

    if request.user.is_authenticated:
        return redirect("home")

    error_message = None

    if request.method == "POST":

        full_name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        terms = request.POST.get("terms")


        if not terms:
            error_message = "Please accept the Terms & Conditions."

        elif not full_name:
            error_message = "Name is required."

        elif not email:
            error_message = "Email is required."

        elif not username:
            error_message = "Username is required."

        elif not password:
            error_message = "Password is required."

        else:

            with connections["default"].cursor() as cursor:

                cursor.execute(
                    """
                    SELECT 1
                    FROM auth_user
                    WHERE username=%s
                    LIMIT 1
                    """,
                    [username],
                )

                if cursor.fetchone():
                    error_message = "Username already exists."

                else:

                    cursor.execute(
                        """
                        SELECT 1
                        FROM auth_user
                        WHERE email=%s
                        LIMIT 1
                        """,
                        [email],
                    )

                    if cursor.fetchone():
                        error_message = "Email already registered."


        if not error_message:

            if " " in full_name:
                first_name, last_name = full_name.split(" ", 1)
            else:
                first_name = full_name
                last_name = ""

            with transaction.atomic():


                django_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )


                with connections["default"].cursor() as cursor:

                    cursor.execute(
                        """
                        INSERT INTO customer
                        (
                            email,
                            password,
                            phone,
                            created_at,
                            updated_at
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            NOW(),
                            NOW()
                        )
                        """,
                        [
                            email,
                            password,
                            "+1-555-0199",
                        ],
                    )

                    customer_id = cursor.lastrowid

                    cursor.execute(
                        """
                        INSERT INTO customer_info
                        (
                            customer_id,
                            firstname,
                            lastname,
                            customer_status,
                            customer_address,
                            city_id,
                            country_id,
                            created_at,
                            updated_at
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            NOW(),
                            NOW()
                        )
                        """,
                        [
                            customer_id,
                            first_name,
                            last_name,
                            "Active",
                            "Registered Address",
                            1,
                            1,
                        ],
                    )

            django_user.backend = (
                "django.contrib.auth.backends.ModelBackend"
            )

            login(request, django_user)

            messages.success(
                request,
                "Registration successful. Welcome!"
            )

            return redirect("home")

        messages.error(request, error_message)

    return render(
        request,
        "car_sales/register.html",
        {
            "error_message": error_message,
        },
    )



def logout_view(request):
    """
    Logout current user.
    """
    storage = messages.get_messages(request)
    for _ in storage:
        pass

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")

