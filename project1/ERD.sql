CREATE TABLE `Roles` (
  `role_id` int PRIMARY KEY AUTO_INCREMENT,
  `role_name` varchar(50) UNIQUE NOT NULL
);

CREATE TABLE `Addresses` (
  `address_id` int PRIMARY KEY AUTO_INCREMENT,
  `street_address` varchar(150) NOT NULL,
  `city` varchar(50) NOT NULL,
  `state` varchar(50) NOT NULL,
  `postal_code` varchar(20) NOT NULL
);

CREATE TABLE `Employees` (
  `employee_id` int PRIMARY KEY AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) UNIQUE NOT NULL,
  `phone` varchar(20),
  `date_of_birth` date,
  `address_id` int,
  `status` enum(Active,On Leave,Terminated) DEFAULT 'Active',
  `hire_date` date NOT NULL DEFAULT (now()),
  `terminated_date` date,
  `commission_rate` decimal(5,2) NOT NULL DEFAULT 0 COMMENT 'CHECK(commission_rate >= 0)'
);

CREATE TABLE `Customers` (
  `customer_id` int PRIMARY KEY AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) UNIQUE NOT NULL,
  `phone` varchar(20) NOT NULL,
  `address_id` int
);

CREATE TABLE `VehicleModels` (
  `model_id` int PRIMARY KEY AUTO_INCREMENT,
  `make` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL,
  `trim` varchar(50),
  `body_type` varchar(30),
  `fuel_type` varchar(30)
);

CREATE TABLE `Vehicles` (
  `vehicle_id` int PRIMARY KEY AUTO_INCREMENT,
  `model_id` int NOT NULL,
  `vin` varchar(17) UNIQUE NOT NULL,
  `year` int NOT NULL COMMENT 'CHECK(year BETWEEN 1900 AND 2100)',
  `color` varchar(30),
  `mileage` int NOT NULL DEFAULT 0 COMMENT 'CHECK(mileage >= 0)',
  `acquisition_cost` decimal(10,2) NOT NULL COMMENT 'CHECK(acquisition_cost >= 0)',
  `selling_price` decimal(10,2) NOT NULL COMMENT 'CHECK(selling_price >= 0)',
  `condition` enum(New,Used,Certified Pre-Owned) NOT NULL,
  `status` enum(Available,Reserved,In Transit,Under Inspection,Sold) DEFAULT 'Available'
);

CREATE TABLE `Leads` (
  `lead_id` int PRIMARY KEY AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `vehicle_id` int,
  `employee_id` int NOT NULL,
  `source` varchar(50),
  `status` enum(New,Contacted,Qualified,Negotiating,Won,Lost) DEFAULT 'New',
  `notes` text,
  `created_at` timestamp DEFAULT (now()),
  `updated_at` timestamp DEFAULT (now()),
  `deleted_at` timestamp COMMENT 'Used for soft delete'
);

CREATE TABLE `LeadActivities` (
  `activity_id` int PRIMARY KEY AUTO_INCREMENT,
  `lead_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `activity_type` enum(Call,Email,Meeting,Test Drive,Note) NOT NULL,
  `activity_date` datetime NOT NULL DEFAULT (now()),
  `details` text,
  `created_at` timestamp DEFAULT (now())
);

CREATE TABLE `Sales` (
  `sale_id` int PRIMARY KEY AUTO_INCREMENT,
  `lead_id` int UNIQUE NOT NULL,
  `employee_id` int NOT NULL,
  `vehicle_id` int UNIQUE NOT NULL,
  `sale_date` datetime NOT NULL DEFAULT (now()),
  `base_price` decimal(10,2) NOT NULL COMMENT 'CHECK(base_price >= 0)',
  `discount_amount` decimal(10,2) DEFAULT 0 COMMENT 'CHECK(discount_amount >= 0)',
  `tax_amount` decimal(10,2) DEFAULT 0 COMMENT 'CHECK(tax_amount >= 0)',
  `commission_rate_applied` decimal(5,2) NOT NULL,
  `created_at` timestamp DEFAULT (now()),
  `updated_at` timestamp DEFAULT (now())
);

CREATE TABLE `TradeIns` (
  `trade_in_id` int PRIMARY KEY AUTO_INCREMENT,
  `sale_id` int UNIQUE,
  `vehicle_id` int UNIQUE,
  `appraised_value` decimal(10,2) COMMENT 'CHECK(appraised_value >= 0)',
  `allowance_amount` decimal(10,2) COMMENT 'CHECK(allowance_amount >= 0)',
  `notes` text
);

CREATE TABLE `Payments` (
  `payment_id` int PRIMARY KEY AUTO_INCREMENT,
  `sale_id` int NOT NULL,
  `payment_date` datetime NOT NULL DEFAULT (now()),
  `amount` decimal(10,2) NOT NULL COMMENT 'CHECK(amount > 0)',
  `payment_method` enum(Cash,Credit Card,Bank Transfer,Check,Loan),
  `status` enum(Pending,Completed,Failed,Refunded) DEFAULT 'Pending',
  `transaction_reference` varchar(100),
  `created_at` timestamp DEFAULT (now()),
  `updated_at` timestamp DEFAULT (now())
);

CREATE TABLE `Suppliers` (
  `supplier_id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `contact_person` varchar(100),
  `contact_number` varchar(20),
  `email` varchar(100),
  `address_id` int
);

CREATE TABLE `ServiceRequests` (
  `request_id` int PRIMARY KEY AUTO_INCREMENT,
  `vehicle_id` int NOT NULL,
  `supplier_id` int,
  `request_date` datetime NOT NULL DEFAULT (now()),
  `issue_description` text,
  `status` enum(Pending,In Progress,Completed,Cancelled) DEFAULT 'Pending',
  `created_at` timestamp DEFAULT (now()),
  `updated_at` timestamp DEFAULT (now())
);

CREATE TABLE `MaintenanceSchedules` (
  `schedule_id` int PRIMARY KEY AUTO_INCREMENT,
  `vehicle_id` int NOT NULL,
  `maintenance_type` varchar(50) NOT NULL,
  `schedule_date` datetime NOT NULL,
  `status` enum(Scheduled,In Progress,Completed,Missed,Cancelled) DEFAULT 'Scheduled',
  `created_at` timestamp DEFAULT (now()),
  `updated_at` timestamp DEFAULT (now())
);

CREATE INDEX `Employees_index_0` ON `Employees` (`status`);

CREATE INDEX `Employees_index_1` ON `Employees` (`email`);

CREATE INDEX `Customers_index_2` ON `Customers` (`email`);

CREATE INDEX `Customers_index_3` ON `Customers` (`last_name`);

CREATE INDEX `Vehicles_index_4` ON `Vehicles` (`status`);

CREATE INDEX `Vehicles_index_5` ON `Vehicles` (`year`);

CREATE INDEX `Vehicles_index_6` ON `Vehicles` (`vin`);

CREATE INDEX `Leads_index_7` ON `Leads` (`status`);

CREATE INDEX `Leads_index_8` ON `Leads` (`created_at`);

CREATE INDEX `Sales_index_9` ON `Sales` (`sale_date`);

CREATE INDEX `Payments_index_10` ON `Payments` (`sale_id`);

ALTER TABLE `Employees` ADD FOREIGN KEY (`role_id`) REFERENCES `Roles` (`role_id`);

ALTER TABLE `Employees` ADD FOREIGN KEY (`address_id`) REFERENCES `Addresses` (`address_id`);

ALTER TABLE `Customers` ADD FOREIGN KEY (`address_id`) REFERENCES `Addresses` (`address_id`);

ALTER TABLE `Vehicles` ADD FOREIGN KEY (`model_id`) REFERENCES `VehicleModels` (`model_id`);

ALTER TABLE `Leads` ADD FOREIGN KEY (`customer_id`) REFERENCES `Customers` (`customer_id`);

ALTER TABLE `Leads` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`);

ALTER TABLE `Leads` ADD FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`employee_id`);

ALTER TABLE `LeadActivities` ADD FOREIGN KEY (`lead_id`) REFERENCES `Leads` (`lead_id`);

ALTER TABLE `LeadActivities` ADD FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`employee_id`);

ALTER TABLE `Sales` ADD FOREIGN KEY (`lead_id`) REFERENCES `Leads` (`lead_id`);

ALTER TABLE `Sales` ADD FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`employee_id`);

ALTER TABLE `Sales` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`);

ALTER TABLE `TradeIns` ADD FOREIGN KEY (`sale_id`) REFERENCES `Sales` (`sale_id`);

ALTER TABLE `TradeIns` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`);

ALTER TABLE `Payments` ADD FOREIGN KEY (`sale_id`) REFERENCES `Sales` (`sale_id`);

ALTER TABLE `Suppliers` ADD FOREIGN KEY (`address_id`) REFERENCES `Addresses` (`address_id`);

ALTER TABLE `ServiceRequests` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`);

ALTER TABLE `ServiceRequests` ADD FOREIGN KEY (`supplier_id`) REFERENCES `Suppliers` (`supplier_id`);

ALTER TABLE `MaintenanceSchedules` ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicles` (`vehicle_id`);
