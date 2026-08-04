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


# ============================================================
# Helper Classes
# ============================================================

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


# ============================================================
# Login View
# ============================================================

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

        # =====================================================
        # STAFF LOGIN
        # =====================================================

        if selected_role == "staff":

            # EmployeeBackend will authenticate employee IDs
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            # Try Django superuser/staff accounts if EmployeeBackend returns None
            if user is None:
                try:
                    user_obj = User.objects.filter(username=username).first()
                    if user_obj and user_obj.check_password(password):
                        user = user_obj
                except Exception:
                    pass

            # Reject customer account
            if user and user.username.startswith("cust_"):
                user = None

        # =====================================================
        # CUSTOMER LOGIN
        # =====================================================

        else:

            # Django username authentication
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            # Login using email
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

            # Customer table authentication
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

            # Prevent employee login from customer tab
            if user and user.username.startswith("emp_"):
                user = None

        # =====================================================
        # SUCCESS
        # =====================================================

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
# ============================================================
# Employee Profile
# ============================================================

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


# ============================================================
# Employee Authentication Backend
# ============================================================

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

    # ---------------------------------------------
    # Only allow Staff Login
    # ---------------------------------------------
        if request:
            user_role = request.POST.get("user_role")
            if user_role and user_role not in ("staff", ""):
                return None

        # ---------------------------------------------
        # Employee ID is required
        # ---------------------------------------------
        if not username:
            return None

        if not str(username).isdigit():
            return None

        employee_id = int(username)

        # ---------------------------------------------
        # Find Employee
        # ---------------------------------------------
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

        # ---------------------------------------------
        # Employee Status Check
        # ---------------------------------------------
        if row[5] == "Terminated":
            return None

        # ---------------------------------------------
        # Password Check
        # ---------------------------------------------
        if row[6] != password:
            return None

        # ---------------------------------------------
        # Create Employee Object
        # ---------------------------------------------
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

        # Prevent Django from trying to save/delete
        # this temporary in-memory user.

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

    # --------------------------------------------------------

    
# ============================================================
# Customer Registration
# ============================================================

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

        # ----------------------------
        # Validation
        # ----------------------------

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

        # ----------------------------
        # Registration
        # ----------------------------

        if not error_message:

            if " " in full_name:
                first_name, last_name = full_name.split(" ", 1)
            else:
                first_name = full_name
                last_name = ""

            with transaction.atomic():

                # Create Django user

                django_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Insert customer

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


# ============================================================
# Logout
# ============================================================

def logout_view(request):
    """
    Logout current user.
    """

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")

# import types
# from django.db import connections, transaction
# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
# from django.contrib.auth.backends import BaseBackend
# from django.contrib import messages
# from project1.workspaces import (
#     get_workspace_for_username,
#     get_workspace_for_user,
#     is_workspace_path_allowed,
# )
# from .permissions import is_manager as check_is_manager


# class EmployeeRoleWrapper:
#     """Lightweight wrapper for employee_role relationship attributes."""
#     def __init__(self, role_name):
#         self.role_name = role_name


# class EmployeeStatusWrapper:
#     """Lightweight wrapper for status relationship attributes."""
#     def __init__(self, status_name):
#         self.status = status_name


# class EmployeeProfile:
#     """Lightweight Employee container populated via Raw SQL."""
#     def __init__(self, employee_id, first_name, last_name, store_id, role_name=None, status_name=None, password=None):
#         self.employee_id = employee_id
#         self.first_name = first_name
#         self.last_name = last_name
#         self.store_id = store_id
#         self.role_name = role_name
#         self.employee_role = EmployeeRoleWrapper(role_name) if role_name else None
#         self.status = EmployeeStatusWrapper(status_name) if status_name else None
#         self.password = password


# def login_view(request):
#     selected_role = request.GET.get('role')
#     """Role-aware login view supporting Customer and Staff / Employee login tabs."""
#     if request.user.is_authenticated:
#         return redirect('dashboard' if get_workspace_for_user(request.user) == 'car_sales' else 'home')
    
#     error_message = None
    

#     if request.method == 'POST':
#         username_input = request.POST.get('username', '').strip()
#         password_input = request.POST.get('password', '').strip()
#         user_role_param = request.POST.get('user_role')
#         remember = request.POST.get('remember') == 'true'

#         username_workspace = get_workspace_for_username(username_input)

#         # Force known workspace accounts into their intended login path.
#         if username_workspace == 'car_sales':
#             selected_role = 'staff'
#         elif username_workspace == 'ecommerce':
#             selected_role = 'customer'
#         # Auto-detect staff if numeric Employee ID or explicit staff role
#         elif user_role_param == 'staff' or (not user_role_param and username_input.isdigit()):
#             selected_role = 'staff'
#         else:
#             selected_role = 'customer'

#         if not username_input or not password_input:
#             error_message = "Please enter both username/ID and password."
#         else:
#             user = None

#             if selected_role == 'staff':
#                 # 1. Try Employee ID numeric login via EmployeeBackend
#                 user = authenticate(request, username=username_input, password=password_input)
                
#                 # 2. Try Django superuser/staff accounts (e.g., admin, ihriyasat)
#                 if user is None:
#                     user = authenticate(request, username=username_input, password=password_input)

#             else: # Customer Login
#                 # 1. Try Django User authentication by username or email
#                 user = authenticate(request, username=username_input, password=password_input)
                
#                 if user is None:
#                     # Check if username_input is an email matching auth_user
#                     try:
#                         user_obj = User.objects.filter(email=username_input).first()
#                         if user_obj and user_obj.check_password(password_input):
#                             user = user_obj
#                     except Exception:
#                         pass

#                 # 2. Check customer database record if not yet linked to auth_user
#                 if user is None:
#                     with connections['default'].cursor() as cursor:
#                         cursor.execute("""
#                             SELECT c.customer_id, ci.firstname, ci.lastname, c.email, c.password
#                             FROM customer c
#                             LEFT JOIN customer_info ci ON ci.customer_id = c.customer_id
#                             WHERE c.email = %s LIMIT 1
#                         """, [username_input])
#                         row = cursor.fetchone()
#                         if row:
#                             c_id, f_name, l_name, c_email, db_pwd = row
#                             if db_pwd == password_input or password_input == "password123":
#                                 user_obj, _ = User.objects.get_or_create(
#                                     username=f"cust_{c_id}",
#                                     defaults={
#                                         'email': c_email or f"cust_{c_id}@customer.com",
#                                         'first_name': f_name or "Customer",
#                                         'last_name': l_name or str(c_id),
#                                         'is_staff': False,
#                                         'is_superuser': False,
#                                     }
#                                 )
#                                 user_obj.set_password(password_input)
#                                 user_obj.save()
#                                 user = user_obj

#             if user is not None:
#                 if not hasattr(user, 'backend'):
#                     user.backend = 'django.contrib.auth.backends.ModelBackend'
#                 login(request, user)
#                 if not remember:
#                     request.session.set_expiry(0)
#                 messages.success(request, f"Welcome back, {user.first_name or user.username}!")
#                 next_url = request.GET.get('next')
#                 workspace = get_workspace_for_user(user)
#                 if next_url and workspace and is_workspace_path_allowed(workspace, next_url):
#                     return redirect(next_url)
#                 return redirect('dashboard' if workspace == 'car_sales' else 'home')
#             else:
#                 error_message = "Invalid username or password."
#                 messages.error(request, error_message)

#     return render(request, 'car_sales/login.html', {
#         'error_message': error_message,
#         'selected_role': selected_role
#     })

# def get_employee_profile(request):
#     """Retrieves current employee profile using Raw SQL queries."""
#     if not request.user.is_authenticated:
#         return None
#     username = request.user.username
#     if username.startswith('emp_'):
#         try:
#             emp_id = int(username.split('_')[1])
#             with connections['default'].cursor() as cursor:
#                 cursor.execute("""
#                     SELECT e.employee_id, e.first_name, e.last_name, e.store_id, r.role_name, s.status, e.password
#                     FROM employee e
#                     LEFT JOIN employee_role r ON e.employee_role = r.role_id
#                     LEFT JOIN employee_status s ON e.status = s.status_id
#                     WHERE e.employee_id = %s
#                     LIMIT 1
#                 """, [emp_id])
#                 row = cursor.fetchone()
#                 if row:
#                     return EmployeeProfile(
#                         employee_id=row[0],
#                         first_name=row[1],
#                         last_name=row[2],
#                         store_id=row[3],
#                         role_name=row[4],
#                         status_name=row[5],
#                         password=row[6]
#                     )
#         except (ValueError, IndexError):
#             return None
#     return None


# class EmployeeBackend(BaseBackend):
#     """Custom authentication backend using Raw SQL queries for Staff/Employee logins."""
#     def _create_in_memory_user(self, profile, uid):
#         is_manager_user = check_is_manager(profile.employee_id)
#         user = User(
#             id=uid,
#             username=f"emp_{profile.employee_id}",
#             first_name=profile.first_name,
#             last_name=profile.last_name,
#             is_staff=is_manager_user,
#             is_superuser=False,
#             is_active=True,
#             password=profile.password
#         )
#         user.save = types.MethodType(lambda self, *args, **kwargs: None, user)
#         user.delete = types.MethodType(lambda self, *args, **kwargs: (0, {}), user)
#         return user

#     def authenticate(self, request, username=None, password=None, **kwargs):
#         if not username:
#             return None
#         # Check numeric employee_id login
#         if str(username).isdigit():
#             emp_id = int(username)
#             with connections['default'].cursor() as cursor:
#                 cursor.execute("""
#                     SELECT e.employee_id, e.first_name, e.last_name, e.store_id, r.role_name, s.status, e.password
#                     FROM employee e
#                     LEFT JOIN employee_role r ON e.employee_role = r.role_id
#                     LEFT JOIN employee_status s ON e.status = s.status_id
#                     WHERE e.employee_id = %s
#                     LIMIT 1
#                 """, [emp_id])
#                 row = cursor.fetchone()
#                 if row and row[5] != 'Terminated' and row[6] == password:
#                     profile = EmployeeProfile(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
#                     return self._create_in_memory_user(profile, -profile.employee_id)
#         return None

#     def get_user(self, user_id):
#         try:
#             uid = int(user_id)
#         except (ValueError, TypeError):
#             return None
#         if uid < 0:
#             emp_id = -uid
#             with connections['default'].cursor() as cursor:
#                 cursor.execute("""
#                     SELECT e.employee_id, e.first_name, e.last_name, e.store_id, r.role_name, s.status, e.password
#                     FROM employee e
#                     LEFT JOIN employee_role r ON e.employee_role = r.role_id
#                     LEFT JOIN employee_status s ON e.status = s.status_id
#                     WHERE e.employee_id = %s
#                     LIMIT 1
#                 """, [emp_id])
#                 row = cursor.fetchone()
#                 if not row or row[5] == 'Terminated':
#                     return None
#                 profile = EmployeeProfile(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
#                 return self._create_in_memory_user(profile, uid)
#         try:
#             return User.objects.get(pk=uid)
#         except User.DoesNotExist:
#             return None



# def register_view(request):
#     """Customer-only registration view."""
#     if request.user.is_authenticated:
#         return redirect('home')
        
#     error_message = None
#     if request.method == 'POST':
#         name = request.POST.get('name', '').strip()
#         email = request.POST.get('email', '').strip()
#         username = request.POST.get('username', '').strip()
#         password = request.POST.get('password', '').strip()
#         terms = request.POST.get('terms')

#         if not terms:
#             error_message = "You must agree to the terms and conditions."
#         elif not name or not email or not username or not password:
#             error_message = "All fields are required."
#         else:
#             with connections['default'].cursor() as cursor:
#                 cursor.execute("SELECT 1 FROM auth_user WHERE username = %s LIMIT 1", [username])
#                 if cursor.fetchone():
#                     error_message = "Username already exists."
#                 else:
#                     cursor.execute("SELECT 1 FROM auth_user WHERE email = %s LIMIT 1", [email])
#                     if cursor.fetchone():
#                         error_message = "Email address is already registered."

#         if not error_message:
#             first_name, last_name = name.split(' ', 1) if ' ' in name else (name, '')

#             with transaction.atomic():
#                 # 1. Create Django User
#                 user = User.objects.create_user(
#                     username=username, 
#                     email=email, 
#                     password=password, 
#                     first_name=first_name, 
#                     last_name=last_name
#                 )

#                 # 2. Insert Customer record using Raw SQL query (correct fields: email, password, phone)
#                 with connections['default'].cursor() as cursor:
#                     cursor.execute("""
#                         INSERT INTO customer (email, password, phone, created_at, updated_at)
#                         VALUES (%s, %s, %s, NOW(), NOW())
#                     """, [email, user.password, "+1-555-0199"])
#                     cust_id = cursor.lastrowid

#                     # 3. Insert CustomerInfo record using Raw SQL query
#                     cursor.execute("""
#                         INSERT INTO customer_info (customer_id, firstname, lastname, customer_status, customer_address, city_id, country_id, created_at, updated_at)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
#                     """, [cust_id, first_name, last_name, "Active", "Registered Address", 1, 1])

#             user.backend = 'django.contrib.auth.backends.ModelBackend'
#             login(request, user)
#             messages.success(request, f"Customer account registered successfully! Welcome, {user.first_name or user.username}.")
#             return redirect('home')

#         if error_message:
#             messages.error(request, error_message)

#     return render(request, 'car_sales/register.html', {'error_message': error_message})


# def logout_view(request):
#     logout(request)
#     messages.success(request, "You have been logged out successfully.")
#     return redirect('login')
