-- ==========================================
-- CAR SALES DATABASE SCHEMA (ERD)
-- Auto-generated to match Django models.py logic
-- ==========================================

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------
-- 1. DROP EXISTING TABLES (IF ANY)
-- ------------------------------------------
DROP TABLE IF EXISTS `Payments`;
DROP TABLE IF EXISTS `TradeIns`;
DROP TABLE IF EXISTS `Sales`;
DROP TABLE IF EXISTS `LeadActivities`;
DROP TABLE IF EXISTS `Leads`;
DROP TABLE IF EXISTS `Vehicles`;
DROP TABLE IF EXISTS `VehicleModels`;
DROP TABLE IF EXISTS `Customers`;
DROP TABLE IF EXISTS `Employees`;
DROP TABLE IF EXISTS `PaymentMethods`;
DROP TABLE IF EXISTS `Addresses`;
DROP TABLE IF EXISTS `Roles`;

-- ------------------------------------------
-- 2. CREATE LOOKUP & CONFIGURATION TABLES
-- ------------------------------------------

-- Table Roles
CREATE TABLE `Roles` (
  `role_id` int PRIMARY KEY AUTO_INCREMENT,
  `role_name` varchar(50) UNIQUE NOT NULL
);

-- Table Addresses
CREATE TABLE `Addresses` (
  `address_id` int PRIMARY KEY AUTO_INCREMENT,
  `street_address` varchar(150) NOT NULL,
  `city` varchar(50) NOT NULL,
  `state` varchar(50) NOT NULL,
  `postal_code` varchar(20) NOT NULL
);

-- Table PaymentMethods
CREATE TABLE `PaymentMethods` (
  `method_id` int PRIMARY KEY AUTO_INCREMENT,
  `payment_method_name` varchar(50) UNIQUE NOT NULL
);

-- ------------------------------------------
-- 3. CREATE CORE ENTITY TABLES
-- ------------------------------------------

-- Table Employees
CREATE TABLE `Employees` (
  `employee_id` int PRIMARY KEY AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) UNIQUE NOT NULL,
  `phone` varchar(20) NULL,
  `date_of_birth` date NULL,
  `address_id` int NULL,
  `status` enum('ACTIVE', 'INACTIVE', 'ON_LEAVE', 'TERMINATED') NOT NULL DEFAULT 'ACTIVE',
  `hire_date` date NOT NULL DEFAULT (CURRENT_DATE),
  `terminated_date` date NULL,
  `commission_rate` decimal(5,2) NOT NULL DEFAULT 0.00,
  CONSTRAINT `chk_employee_commission` CHECK (`commission_rate` >= 0.00)
);

-- Table Customers
CREATE TABLE `Customers` (
  `customer_id` int PRIMARY KEY AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) UNIQUE NOT NULL,
  `phone` varchar(20) NOT NULL,
  `address_id` int NULL
);

-- Table VehicleModels
CREATE TABLE `VehicleModels` (
  `model_id` int PRIMARY KEY AUTO_INCREMENT,
  `make` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL,
  `trim` varchar(50) NULL,
  `body_type` varchar(30) NULL,
  `fuel_type` varchar(30) NULL
);

-- Table Vehicles
CREATE TABLE `Vehicles` (
  `vehicle_id` int PRIMARY KEY AUTO_INCREMENT,
  `model_id` int NOT NULL,
  `vin` varchar(17) UNIQUE NOT NULL,
  `year` int NOT NULL,
  `color` varchar(30) NULL,
  `mileage` int NOT NULL DEFAULT 0,
  `acquisition_cost` decimal(10,2) NOT NULL,
  `selling_price` decimal(10,2) NOT NULL,
  `condition` enum('NEW', 'USED', 'CPO') NOT NULL,
  `status` enum('AVAILABLE', 'RESERVED', 'SOLD', 'IN_SERVICE') NOT NULL DEFAULT 'AVAILABLE',
  CONSTRAINT `chk_vehicle_year` CHECK (`year` BETWEEN 1900 AND 2100),
  CONSTRAINT `chk_vehicle_mileage` CHECK (`mileage` >= 0),
  CONSTRAINT `chk_vehicle_cost` CHECK (`acquisition_cost` >= 0.00),
  CONSTRAINT `chk_vehicle_price` CHECK (`selling_price` >= 0.00)
);

-- ------------------------------------------
-- 4. CREATE TRANSACTIONAL TABLES
-- ------------------------------------------

-- Table Leads
CREATE TABLE `Leads` (
  `lead_id` int PRIMARY KEY AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `vehicle_id` int NULL,
  `employee_id` int NOT NULL,
  `source` varchar(50) NULL,
  `status` enum('NEW', 'CONTACTED', 'QUALIFIED', 'NEGOTIATING', 'WON', 'LOST') NOT NULL DEFAULT 'NEW',
  `notes` text NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` timestamp NULL
);

-- Table LeadActivities
CREATE TABLE `LeadActivities` (
  `activity_id` int PRIMARY KEY AUTO_INCREMENT,
  `lead_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `activity_type` enum('CALL', 'EMAIL', 'TEST_DRIVE', 'MEETING', 'FOLLOW_UP', 'NOTE') NOT NULL,
  `activity_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `details` text NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table Sales
CREATE TABLE `Sales` (
  `sale_id` int PRIMARY KEY AUTO_INCREMENT,
  `lead_id` int UNIQUE NULL,
  `employee_id` int NOT NULL,
  `vehicle_id` int UNIQUE NOT NULL,
  `sale_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `base_price` decimal(10,2) NOT NULL,
  `discount_amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `tax_amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `commission_rate_applied` decimal(5,2) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `chk_sale_base_price` CHECK (`base_price` >= 0.00),
  CONSTRAINT `chk_sale_discount` CHECK (`discount_amount` >= 0.00),
  CONSTRAINT `chk_sale_tax` CHECK (`tax_amount` >= 0.00),
  CONSTRAINT `chk_sale_commission` CHECK (`commission_rate_applied` >= 0.00)
);

-- Table TradeIns
CREATE TABLE `TradeIns` (
  `trade_in_id` int PRIMARY KEY AUTO_INCREMENT,
  `sale_id` int UNIQUE NULL,
  `vehicle_id` int UNIQUE NOT NULL,
  `appraised_value` decimal(10,2) NULL,
  `allowance_amount` decimal(10,2) NULL,
  `notes` text NULL,
  CONSTRAINT `chk_tradein_appraised` CHECK (`appraised_value` >= 0.00),
  CONSTRAINT `chk_tradein_allowance` CHECK (`allowance_amount` >= 0.00)
);

-- Table Payments
CREATE TABLE `Payments` (
  `payment_id` int PRIMARY KEY AUTO_INCREMENT,
  `sale_id` int NOT NULL,
  `payment_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `amount` decimal(10,2) NOT NULL,
  `method_id` int NULL,
  `status` enum('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED') NOT NULL DEFAULT 'PENDING',
  `transaction_reference` varchar(100) NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `chk_payment_amount` CHECK (`amount` > 0.00)
);

-- ------------------------------------------
-- 5. CREATE OPTIMIZED INDEXES
-- ------------------------------------------
-- These match the explicit indexes defined in the Meta.indexes blocks in Django models

CREATE INDEX `Employees_status_idx` ON `Employees` (`status`);
CREATE INDEX `Customers_lastname_idx` ON `Customers` (`last_name`);
CREATE INDEX `Vehicles_status_idx` ON `Vehicles` (`status`);
CREATE INDEX `Vehicles_year_idx` ON `Vehicles` (`year`);
CREATE INDEX `Leads_status_idx` ON `Leads` (`status`);
CREATE INDEX `Leads_created_idx` ON `Leads` (`created_at`);
CREATE INDEX `Sales_date_idx` ON `Sales` (`sale_date`);

-- ------------------------------------------
-- 6. ADD FOREIGN KEY CONSTRAINTS
-- ------------------------------------------

ALTER TABLE `Employees` ADD FOREIGN KEY (`role_id`) REFERENCES `Roles` (`role_id`) ON DELETE RESTRICT;
ALTER TABLE `Employees` ADD FOREIGN KEY (`address_id`) REFERENCES `Addresses` (`address_id`) ON DELETE SET NULL;

ALTER TABLE `Customers` ADD FOREIGN KEY (`address_id`) REFERENCES `Addresses` (`address_id`) ON DELETE SET NULL;

ALTER TABLE `Vehicles` ADD FOREIGN KEY (`model_id`) REFERENCES `VehicleModels` (`model_id`) ON DELETE RESTRICT;

ALTER TABLE `Leads` ADD FOREIGN KEY (`customer_id`) REFERENCES `Customers` (`customer_id`) ON DELETE RESTRICT;
ALTER TABLE `Leads` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`) ON DELETE SET NULL;
ALTER TABLE `Leads` ADD FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`employee_id`) ON DELETE RESTRICT;

ALTER TABLE `LeadActivities` ADD FOREIGN KEY (`lead_id`) REFERENCES `Leads` (`lead_id`) ON DELETE CASCADE;
ALTER TABLE `LeadActivities` ADD FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`employee_id`) ON DELETE RESTRICT;

ALTER TABLE `Sales` ADD FOREIGN KEY (`lead_id`) REFERENCES `Leads` (`lead_id`) ON DELETE SET NULL;
ALTER TABLE `Sales` ADD FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`employee_id`) ON DELETE RESTRICT;
ALTER TABLE `Sales` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`) ON DELETE RESTRICT;

ALTER TABLE `TradeIns` ADD FOREIGN KEY (`sale_id`) REFERENCES `Sales` (`sale_id`) ON DELETE SET NULL;
ALTER TABLE `TradeIns` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`) ON DELETE RESTRICT;

ALTER TABLE `Payments` ADD FOREIGN KEY (`sale_id`) REFERENCES `Sales` (`sale_id`) ON DELETE RESTRICT;
ALTER TABLE `Payments` ADD FOREIGN KEY (`method_id`) REFERENCES `PaymentMethods` (`method_id`) ON DELETE SET NULL;

SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 7. DBDiagram.io CODE (DBML Syntax)
-- Copy and paste the comment block below into dbdiagram.io
-- ==========================================
/*
Enum EmployeeStatus {
  ACTIVE
  INACTIVE
  ON_LEAVE
  TERMINATED
}

Enum VehicleCondition {
  NEW
  USED
  CPO
}

Enum VehicleStatus {
  AVAILABLE
  RESERVED
  SOLD
  IN_SERVICE
}

Enum LeadStatus {
  NEW
  CONTACTED
  QUALIFIED
  NEGOTIATING
  WON
  LOST
}

Enum ActivityType {
  CALL
  EMAIL
  TEST_DRIVE
  MEETING
  FOLLOW_UP
  NOTE
}

Enum PaymentStatus {
  PENDING
  COMPLETED
  FAILED
  REFUNDED
}

Table Roles {
  role_id int [pk, increment]
  role_name varchar(50) [unique, not null]
}

Table Addresses {
  address_id int [pk, increment]
  street_address varchar(150) [not null]
  city varchar(50) [not null]
  state varchar(50) [not null]
  postal_code varchar(20) [not null]
}

Table PaymentMethods {
  method_id int [pk, increment]
  payment_method_name varchar(50) [unique, not null]
}

Table Employees {
  employee_id int [pk, increment]
  role_id int [not null]
  first_name varchar(50) [not null]
  last_name varchar(50) [not null]
  email varchar(100) [unique, not null]
  phone varchar(20)
  date_of_birth date
  address_id int
  status EmployeeStatus [default: 'ACTIVE', not null]
  hire_date date [default: `now()`, not null]
  terminated_date date
  commission_rate decimal(5,2) [default: 0.00, not null]
}

Table Customers {
  customer_id int [pk, increment]
  first_name varchar(50) [not null]
  last_name varchar(50) [not null]
  email varchar(100) [unique, not null]
  phone varchar(20) [not null]
  address_id int
}

Table VehicleModels {
  model_id int [pk, increment]
  make varchar(50) [not null]
  model varchar(50) [not null]
  trim varchar(50)
  body_type varchar(30)
  fuel_type varchar(30)
}

Table Vehicles {
  vehicle_id int [pk, increment]
  model_id int [not null]
  vin varchar(17) [unique, not null]
  year int [not null]
  color varchar(30)
  mileage int [default: 0, not null]
  acquisition_cost decimal(10,2) [not null]
  selling_price decimal(10,2) [not null]
  condition VehicleCondition [not null]
  status VehicleStatus [default: 'AVAILABLE', not null]
}

Table Leads {
  lead_id int [pk, increment]
  customer_id int [not null]
  vehicle_id int
  employee_id int [not null]
  source varchar(50)
  status LeadStatus [default: 'NEW', not null]
  notes text
  created_at timestamp [default: `now()`, not null]
  updated_at timestamp [default: `now()`, not null]
  deleted_at timestamp
}

Table LeadActivities {
  activity_id int [pk, increment]
  lead_id int [not null]
  employee_id int [not null]
  activity_type ActivityType [not null]
  activity_date datetime [default: `now()`, not null]
  details text
  created_at timestamp [default: `now()`, not null]
}

Table Sales {
  sale_id int [pk, increment]
  lead_id int [unique]
  employee_id int [not null]
  vehicle_id int [unique, not null]
  sale_date datetime [default: `now()`, not null]
  base_price decimal(10,2) [not null]
  discount_amount decimal(10,2) [default: 0.00, not null]
  tax_amount decimal(10,2) [default: 0.00, not null]
  commission_rate_applied decimal(5,2) [not null]
  created_at timestamp [default: `now()`, not null]
  updated_at timestamp [default: `now()`, not null]
}

Table TradeIns {
  trade_in_id int [pk, increment]
  sale_id int [unique]
  vehicle_id int [unique, not null]
  appraised_value decimal(10,2)
  allowance_amount decimal(10,2)
  notes text
}

Table Payments {
  payment_id int [pk, increment]
  sale_id int [not null]
  payment_date datetime [default: `now()`, not null]
  amount decimal(10,2) [not null]
  method_id int
  status PaymentStatus [default: 'PENDING', not null]
  transaction_reference varchar(100)
  created_at timestamp [default: `now()`, not null]
  updated_at timestamp [default: `now()`, not null]
}

Ref: Employees.role_id > Roles.role_id [delete: restrict]
Ref: Employees.address_id > Addresses.address_id [delete: set null]
Ref: Customers.address_id > Addresses.address_id [delete: set null]
Ref: Vehicles.model_id > VehicleModels.model_id [delete: restrict]
Ref: Leads.customer_id > Customers.customer_id [delete: restrict]
Ref: Leads.vehicle_id > Vehicles.vehicle_id [delete: set null]
Ref: Leads.employee_id > Employees.employee_id [delete: restrict]
Ref: LeadActivities.lead_id > Leads.lead_id [delete: cascade]
Ref: LeadActivities.employee_id > Employees.employee_id [delete: restrict]
Ref: Sales.lead_id - Leads.lead_id [delete: set null]
Ref: Sales.employee_id > Employees.employee_id [delete: restrict]
Ref: Sales.vehicle_id - Vehicles.vehicle_id [delete: restrict]
Ref: TradeIns.sale_id - Sales.sale_id [delete: set null]
Ref: TradeIns.vehicle_id - Vehicles.vehicle_id [delete: restrict]
Ref: Payments.sale_id > Sales.sale_id [delete: restrict]
Ref: Payments.method_id > PaymentMethods.method_id [delete: set null]
*/

-- ==========================================
-- 8. Mermaid.live Flowchart Diagram
-- Copy and paste the comment block below into mermaid.live
-- ==========================================

```mermaid
---
config:
  layout: elk
---
erDiagram
    ROLES {
        int role_id PK
        string role_name
    }
    ADDRESSES {
        int address_id PK
        string city
        string country
    }
    PAYMENT_METHODS {
        int method_id PK
        string method_name
    }
    EMPLOYEES {
        int employee_id PK
        int role_id FK
        int address_id FK
        string name
    }
    CUSTOMERS {
        int customer_id PK
        int address_id FK
        string name
    }
    VEHICLE_MODELS {
        int model_id PK
        string make
        string model_name
    }
    VEHICLES {
        int vehicle_id PK
        int model_id FK
        string vin
        string status
    }
    LEADS {
        int lead_id PK
        int customer_id FK
        int employee_id FK
        int vehicle_id FK
        string status
    }
    LEAD_ACTIVITIES {
        int activity_id PK
        int lead_id FK
        int employee_id FK
        string activity_type
    }
    SALES {
        int sale_id PK
        int lead_id FK
        int employee_id FK
        int vehicle_id FK
        decimal sale_price
    }
    TRADE_INS {
        int trade_in_id PK
        int sale_id FK
        int vehicle_id FK
        decimal trade_value
    }
    PAYMENTS {
        int payment_id PK
        int sale_id FK
        int method_id FK
        decimal amount
    }

    ROLES           ||--o{ EMPLOYEES       : has
    ADDRESSES       o|--o{ EMPLOYEES       : has
    ADDRESSES       o|--o{ CUSTOMERS       : has
    VEHICLE_MODELS  ||--o{ VEHICLES        : has

    CUSTOMERS       ||--o{ LEADS           : submits
    EMPLOYEES       ||--o{ LEADS           : manages
    VEHICLES        o|--o{ LEADS           : interests

    LEADS           ||--o{ LEAD_ACTIVITIES : has
    EMPLOYEES       ||--o{ LEAD_ACTIVITIES : logs

    LEADS           o|--o| SALES           : converts_to
    EMPLOYEES       ||--o{ SALES           : closes
    VEHICLES        ||--||  SALES          : sold_in

    SALES           o|--o| TRADE_INS       : includes
    VEHICLES        ||--||  TRADE_INS      : traded_in_as

    SALES           ||--o{ PAYMENTS        : paid_via
    PAYMENT_METHODS o|--o{ PAYMENTS        : uses
```

If mermaid.live throws an error on the `elk` config block 
(older versions sometimes don't support it), just drop the 
`--- config: layout: elk ---` frontmatter and use the plain version
 from before — the default routing is already fairly straight for ER diagrams.