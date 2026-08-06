# 🚗 Enterprise Automotive Sales ERP & E-Commerce Platform

> **Internship Final Project Release — Completed with Pride & Dedication**  
> *A state-of-the-art Enterprise Resource Planning (ERP), Customer Portal, and High-Performance Analytics Platform built with Django, Django REST Framework, and Raw SQL.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0%2B-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14%2B-red.svg)](https://www.django-rest-framework.org/)
[![Database](https://img.shields.io/badge/Database-MySQL%2FMariaDB-orange.svg)](https://www.mysql.com/)
[![Codebase Status](https://img.shields.io/badge/Codebase-100%25%20Clean-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-21%2F21%20Passing-brightgreen.svg)]()

---

## 🎓 Reflection & Internship Journey

> *"Every line of code in this repository represents countless hours of learning, problem-solving, architectural iteration, and continuous refinement. From designing complex 9-Level RBAC permission hierarchies to optimizing raw SQL analytical engines and crafting ultra-responsive e-commerce user interfaces, this project marks the capstone of my internship journey."*

---

## 🌟 Executive Features & Technical Achievements

### 🏢 1. Dealership ERP & Management Portal (`car_sales`)
- **9-Level Role-Based Access Control (RBAC)**: Fine-grained permissions spanning Executive Management (Levels 1–5), Regional Supervision (Level 7), Branch Management (Levels 6 & 8), and Individual Sales Executives (Level 9).
- **Custom Authentication Engine**: Direct numeric ID authentication (`EmployeeBackend`) with automatic manager status resolution.
- **Raw SQL High-Performance Analytics Engine**: Ultra-fast analytical aggregations bypassing ORM overhead for target vs. actual budgets, store performance mix, and customer lifetime value.
- **Automated Sales & Invoicing Pipeline**: Atomic database transaction mapping vehicle sales to automatic invoice creation, MMR pricing calculations, and inventory state transitions (`Available (4)` ➔ `Sold (1)`).

### 🛒 2. Customer E-Commerce Experience (`ecommerce`)
- **Responsive Vehicle Catalog**: Advanced filtering by Make, Model, Body Style, Transmission, Exterior Color, Price Range slider, and Showroom Location.
- **Dynamic Wishlist System**: Real-time asynchronous wishlist saving & removal with smooth card fade-out animations, header counter updates, and floating toast notifications.
- **Shopping Cart & Checkout**: Interactive hold reservations, total calculation, and seamless order checkout.
- **Vehicle Comparison Engine**: Side-by-side spec comparison supporting up to 4 vehicles simultaneously.
- **Test Drive & Direct Store Messaging**: Schedule showroom trial bookings and converse directly with dealership branch staff.

### 🧹 3. Codebase Optimization & Cleanliness
- **100% Dead Code Purge**: All unused legacy functions, unused helper scripts, dead endpoints, and unreferenced theme demo templates were systematically stripped.
- **Comment-Free Production Code**: Tokenization and syntax-aware stripping removed temporary notes while retaining critical string literals and data integrity.
- **Unified UI Design Tokens**: Harmonized empty state cards, modal dialogs, and responsive grid layouts across all viewport sizes.

---

## ⚙️ Quick Start & Setup Guide

### 1. Repository Setup & Dependencies
```bash
git clone <repository_url>
cd internship_django_project

# Activate Python Virtual Environment
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Initialization (MySQL / MariaDB)
```sql
CREATE DATABASE car_sales CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

Import dataset:
```bash
unzip project1/dataset/car_sales_final.zip -d project1/dataset/
mysql -h 127.0.0.1 -P 33007 -u root car_sales < project1/dataset/car_sales_final.sql
```

### 3. Launch Application
```bash
cd project1
python manage.py runserver
```
Visit the Customer Portal at `http://127.0.0.1:8000/` or Staff ERP Portal at `http://127.0.0.1:8000/admin/`.

---

## 🧪 Comprehensive Test Suite Verification

Run the unit and integration testing suite:

```bash
./venv/bin/python project1/manage.py test car_sales ecommerce
```

```
----------------------------------------------------------------------
Ran 21 tests in 12.853s

OK
System check identified no issues (0 silenced).
```

---

## 📡 REST API Directory Reference

| Endpoint | Supported Methods | Description |
| :--- | :--- | :--- |
| `/api/countries/` | `GET`, `POST`, `PUT`, `DELETE` | Country master data management |
| `/api/cities/` | `GET`, `POST`, `PUT`, `DELETE` | City directory management |
| `/api/stores/` | `GET`, `POST`, `PUT`, `DELETE` | Store branch locations |
| `/api/emproles/` | `GET`, `POST`, `PUT`, `DELETE` | Employee roles & access levels |
| `/api/vehicles/` | `GET`, `POST`, `PUT`, `DELETE` | Vehicle inventory & MMR pricing catalog |
| `/api/customers/` | `GET`, `POST`, `PUT`, `DELETE` | Customer profiles directory |
| `/api/sales/` | `GET`, `POST`, `PUT`, `DELETE` | Sales transactions & automatic invoicing |
| `/api/wishlist/toggle/` | `POST`, `DELETE` | Asynchronous wishlist item toggle/remove |
| `/api/cart/add/` | `POST` | Cart item addition |
| `/api/cart/remove/` | `POST` | Cart item removal |

---

## ❤️ Final Internship Acknowledgments

Thank you to my mentors and supervisors for their invaluable support throughout this internship journey. This project stands fully completed, thoroughly tested, and ready for production deployment.

*Finished with heart & pride.* ✨
