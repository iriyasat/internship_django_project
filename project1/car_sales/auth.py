import types
from django.db import connections
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.contrib import messages
from .permissions import is_manager as check_is_manager


class EmployeeRoleWrapper:
    """Lightweight wrapper for employee_role relationship attributes."""
    def __init__(self, role_name):
        self.role_name = role_name


class EmployeeStatusWrapper:
    """Lightweight wrapper for status relationship attributes."""
    def __init__(self, status_name):
        self.status = status_name


class EmployeeProfile:
    """Lightweight Employee container populated via Raw SQL."""
    def __init__(self, employee_id, first_name, last_name, store_id, role_name=None, status_name=None, password=None):
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.store_id = store_id
        self.role_name = role_name
        self.employee_role = EmployeeRoleWrapper(role_name) if role_name else None
        self.status = EmployeeStatusWrapper(status_name) if status_name else None
        self.password = password


def get_employee_profile(request):
    """Retrieves current employee profile using Raw SQL queries."""
    if not request.user.is_authenticated:
        return None
    username = request.user.username
    if username.startswith('emp_'):
        try:
            emp_id = int(username.split('_')[1])
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT e.employee_id, e.first_name, e.last_name, e.store_id, r.role_name, s.status, e.password
                    FROM employee e
                    LEFT JOIN employee_role r ON e.employee_role = r.role_id
                    LEFT JOIN employee_status s ON e.status = s.status_id
                    WHERE e.employee_id = %s
                    LIMIT 1
                """, [emp_id])
                row = cursor.fetchone()
                if row:
                    return EmployeeProfile(
                        employee_id=row[0],
                        first_name=row[1],
                        last_name=row[2],
                        store_id=row[3],
                        role_name=row[4],
                        status_name=row[5],
                        password=row[6]
                    )
        except (ValueError, IndexError):
            return None
    return None


class EmployeeBackend(BaseBackend):
    """Custom authentication backend using Raw SQL queries."""
    def _create_in_memory_user(self, profile, uid):
        is_manager_user = check_is_manager(profile.employee_id)
        user = User(
            id=uid,
            username=f"emp_{profile.employee_id}",
            first_name=profile.first_name,
            last_name=profile.last_name,
            is_staff=is_manager_user,
            is_superuser=False,
            is_active=True,
            password=profile.password
        )
        user.save = types.MethodType(lambda self, *args, **kwargs: None, user)
        user.delete = types.MethodType(lambda self, *args, **kwargs: (0, {}), user)
        return user

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not str(username).isdigit():
            return None
        emp_id = int(username)
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT e.employee_id, e.first_name, e.last_name, e.store_id, r.role_name, s.status, e.password
                FROM employee e
                LEFT JOIN employee_role r ON e.employee_role = r.role_id
                LEFT JOIN employee_status s ON e.status = s.status_id
                WHERE e.employee_id = %s
                LIMIT 1
            """, [emp_id])
            row = cursor.fetchone()
            if not row:
                return None
            status_name = row[5]
            emp_password = row[6]
            if status_name == 'Terminated':
                return None
            if emp_password == password:
                profile = EmployeeProfile(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                return self._create_in_memory_user(profile, -profile.employee_id)
        return None

    def get_user(self, user_id):
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None
        if uid < 0:
            emp_id = -uid
            with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT e.employee_id, e.first_name, e.last_name, e.store_id, r.role_name, s.status, e.password
                    FROM employee e
                    LEFT JOIN employee_role r ON e.employee_role = r.role_id
                    LEFT JOIN employee_status s ON e.status = s.status_id
                    WHERE e.employee_id = %s
                    LIMIT 1
                """, [emp_id])
                row = cursor.fetchone()
                if not row or row[5] == 'Terminated':
                    return None
                profile = EmployeeProfile(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                return self._create_in_memory_user(profile, uid)
        try:
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            return None


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember') == 'true'
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.GET.get('next') or 'home')
        else:
            error_message = "Invalid username or password."
            messages.error(request, error_message)
    return render(request, 'car_sales/login.html', {'error_message': error_message})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error_message = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        terms = request.POST.get('terms')
        if not terms:
            error_message = "You must agree to the terms and conditions."
        elif not name or not email or not username or not password:
            error_message = "All fields are required."
        else:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1 FROM auth_user WHERE username = %s LIMIT 1", [username])
                if cursor.fetchone():
                    error_message = "Username already exists."
                else:
                    cursor.execute("SELECT 1 FROM auth_user WHERE email = %s LIMIT 1", [email])
                    if cursor.fetchone():
                        error_message = "Email already registered."

        if not error_message:
            first_name, last_name = name.split(' ', 1) if ' ' in name else (name, '')
            user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, f"Registration successful. Welcome, {user.username}!")
            return redirect('home')
        if error_message:
            messages.error(request, error_message)
    return render(request, 'car_sales/register.html', {'error_message': error_message})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
