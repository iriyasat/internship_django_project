import types
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.contrib import messages
from .models import Employee
from .utils import is_manager as check_is_manager

def get_employee_profile(request):
    if not request.user.is_authenticated:
        return None
    username = request.user.username
    if username.startswith('emp_'):
        try:
            emp_id = int(username.split('_')[1])
            return Employee.objects.select_related('employee_role', 'status', 'store').filter(employee_id=emp_id).first()
        except (ValueError, IndexError):
            return None
    return None

class EmployeeBackend(BaseBackend):
    def _create_in_memory_user(self, employee, uid):
        is_manager_user = check_is_manager(employee.employee_id)
        user = User(id=uid, username=f"emp_{employee.employee_id}", first_name=employee.first_name, last_name=employee.last_name, is_staff=is_manager_user, is_superuser=False, is_active=True, password=employee.password)
        user.save = types.MethodType(lambda self, *args, **kwargs: None, user)
        user.delete = types.MethodType(lambda self, *args, **kwargs: (0, {}), user)
        return user

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not str(username).isdigit():
            return None
        try:
            employee = Employee.objects.select_related('status').filter(employee_id=int(username)).first()
        except (ValueError, TypeError):
            return None
        if employee and employee.status and employee.status.status == 'Terminated':
            return None
        if employee and employee.password == password:
            return self._create_in_memory_user(employee, -employee.employee_id)
        return None

    def get_user(self, user_id):
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None
        if uid < 0:
            employee = Employee.objects.select_related('employee_role', 'status', 'store').filter(employee_id=-uid).first()
            if not employee or (employee.status and employee.status.status == 'Terminated'):
                return None
            return self._create_in_memory_user(employee, uid)
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
        elif User.objects.filter(username=username).exists():
            error_message = "Username already exists."
        elif User.objects.filter(email=email).exists():
            error_message = "Email already registered."
        else:
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
