# Car Sales Enterprise Resource Planning & Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14%2B-red.svg)](https://www.django-rest-framework.org/)
[![Database](https://img.shields.io/badge/Database-MySQL%2FMariaDB-orange.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-21%2F21%20Passing-brightgreen.svg)]()

An enterprise-grade Automotive Sales, Inventory Management, and Analytical Reporting Platform built with **Django**, **Django REST Framework**, and **Optimized Raw SQL Execution**. Features fine-grained Role-Based Access Control (RBAC), interactive analytical dashboards, inventory management, automated invoice generation, and comprehensive unit/integration test coverage.

---

## 🛠️ Setup & Execution Guide

### Step 1: Clone & Navigate
```bash
git clone <repository_url>
cd internship_django_project
```

### Step 2: Virtual Environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Database Setup
Ensure MariaDB or MySQL is running on port `33007` (or adjust `project1/project1/settings.py`):
```sql
CREATE DATABASE car_sales CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

Import dataset:
```bash
unzip project1/dataset/car_sales_final.zip -d project1/dataset/
/opt/homebrew/bin/mysql -h 127.0.0.1 -P 33007 -u root car_sales < project1/dataset/car_sales_final.sql
```

### Step 4: Run Server
Use the provided script runner:
```bash
./run.sh
```
Or run directly via Django manage.py:
```bash
cd project1
python manage.py runserver
```

---

## 🏛️ System Architecture & Key Modules

### 1. Role-Based Access Control (RBAC)
- **Access Level Scoping**:
  - **Country Level (`country`)**: Full management & reporting scope across all stores in the assigned country.
  - **Store Level (`store`)**: Restricted access to sales, employees, and inventory within the assigned store branch.
  - **Own Data Only (`own`)**: Sales reps access only their own individual sales records and targets.
- **Custom Authentication Backend (`EmployeeBackend`)**: Authenticates employees directly via numeric `employee_id` with in-memory Django user wrapping and automatic manager privilege computation.

### 2. High-Performance Raw SQL Analytics Engine
Optimized raw SQL queries bypassing ORM overhead for large analytical datasets:
- **Employee Sales Performance** (`/api/employee_sales/`)
- **Store Sales Summary** (`/api/store_sales/`)
- **Store & Vehicle Product Mix** (`/api/store_vehicle_sales/`)
- **Customer Vehicle Purchase Breakdown** (`/api/customer_vehicle_sales/`)
- **Customer Store Lifetime Spending** (`/api/customer_store_spending/`)
- **Budget vs. Realized Sales Metrics** (`/api/budget-vs-sales/`)

### 3. Inventory & Invoice Automation
- **Inventory State Machine**: Automated state transitions (`Available (4)` -> `Sold (1)` -> `Pre-order (2)` -> `Unavailable (0)`).
- **Automated Invoice Generation**: Creating a sale automatically calculates MMR vs. selling price, applies discount rules, and links inventory items within atomic transactions.

---

## 🧪 Testing Suite Execution

Run the comprehensive unit and integration test suite via `run.sh` or Django test runner:

```bash
# Via helper script
./run.sh test car_sales

# Or via python directly
./venv/bin/python project1/manage.py test car_sales
```

---

## 📡 REST API Directory Reference

| Endpoint | Supported Methods | Description |
| :--- | :--- | :--- |
| `/api/countries/` | `GET`, `POST`, `PUT`, `DELETE` | Country master data management |
| `/api/cities/` | `GET`, `POST`, `PUT`, `DELETE` | City directory management |
| `/api/stores/` | `GET`, `POST`, `PUT`, `DELETE` | Store branch locations |
| `/api/emproles/` | `GET`, `POST`, `PUT`, `DELETE` | Employee roles & access levels |
| `/api/statuses/` | `GET`, `POST`, `PUT`, `DELETE` | Employee employment status choices |
| `/api/industry/` | `GET`, `POST`, `PUT`, `DELETE` | Vehicle make / manufacturer directory |
| `/api/vehicles/` | `GET`, `POST`, `PUT`, `DELETE` | Vehicle inventory & MMR pricing catalog |
| `/api/customers/` | `GET`, `POST`, `PUT`, `DELETE` | Customer profiles directory |
| `/api/sales/` | `GET`, `POST`, `PUT`, `DELETE` | Sales transactions (auto-triggers invoice creation) |
| `/api/budgets/` | `GET`, `POST`, `PUT`, `DELETE` | Monthly employee target budgets |
| `/api/employees/` | `GET`, `POST`, `PUT`, `DELETE` | Employee records directory |
| `/api/inventory/` | `GET`, `POST`, `PUT`, `DELETE` | Showroom vehicle inventory management |
| `/api/invoices/` | `GET`, `POST`, `PUT`, `DELETE` | Invoicing, discounts & payment processing |

---

## 📄 License & Maintainer Information
Maintained as part of the Enterprise Django Internship Project.
