-- aquaguru.sql
-- Database schema for AquaGuru - Smart Shrimp Farm Management System

-- Create database
CREATE DATABASE IF NOT EXISTS aquaguru;
USE aquaguru;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    farm_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Ponds table
CREATE TABLE IF NOT EXISTS ponds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pond_name VARCHAR(100) NOT NULL,
    area DECIMAL(10,2) NOT NULL,
    seed_count INT NOT NULL,
    species VARCHAR(50) NOT NULL,
    stocking_date DATE NOT NULL,
    status ENUM('active', 'harvested', 'preparing') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Feed records table
CREATE TABLE IF NOT EXISTS feed_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pond_id INT,
    date DATE NOT NULL,
    doc INT NOT NULL,
    abw DECIMAL(10,2) NOT NULL,
    survival DECIMAL(5,2) NOT NULL,
    feed_percentage DECIMAL(5,2) NOT NULL,
    biomass DECIMAL(10,2) NOT NULL,
    daily_feed DECIMAL(10,2) NOT NULL,
    feed_per_session DECIMAL(10,2) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    feed_type VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
);

-- Growth records table
CREATE TABLE IF NOT EXISTS growth_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pond_id INT,
    date DATE NOT NULL,
    doc INT NOT NULL,
    abw DECIMAL(10,2) NOT NULL,
    adg DECIMAL(10,2) NOT NULL,
    survival DECIMAL(5,2) NOT NULL,
    biomass DECIMAL(10,2) NOT NULL,
    fcr DECIMAL(10,2) NOT NULL,
    length_cm DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
);

-- Water quality table
CREATE TABLE IF NOT EXISTS water_quality (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pond_id INT,
    date DATETIME NOT NULL,
    ph DECIMAL(4,2) NOT NULL,
    do DECIMAL(5,2) NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    salinity DECIMAL(5,2),
    ammonia DECIMAL(6,3),
    nitrite DECIMAL(6,3),
    alkalinity DECIMAL(6,2),
    transparency DECIMAL(5,2),
    notes TEXT,
    status ENUM('good', 'moderate', 'poor') DEFAULT 'good',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
);

-- Expenses table (FIXED ENUM ERROR)
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pond_id INT,
    category VARCHAR(50) NOT NULL, /* CHANGED FROM ENUM TO VARCHAR TO PREVENT CRASH */
    amount DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    receipt_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
);

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    category ENUM('Feed', 'Medicine', 'Minerals', 'Probiotics', 'Lime', 'Chemicals', 'Other') NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    min_quantity DECIMAL(10,2) NOT NULL,
    current_quantity DECIMAL(10,2) NOT NULL,
    price_per_unit DECIMAL(10,2),
    supplier VARCHAR(100),
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Harvest table
CREATE TABLE IF NOT EXISTS harvest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pond_id INT,
    harvest_date DATE NOT NULL,
    production DECIMAL(10,2) NOT NULL,
    average_weight DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    income DECIMAL(10,2) NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    profit DECIMAL(10,2) NOT NULL,
    survival_rate DECIMAL(5,2),
    fcr DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('feed_reminder', 'water_test', 'harvest_reminder', 'low_stock', 'general') NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    scheduled_date DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- AI conversation history (optional)
CREATE TABLE IF NOT EXISTS ai_conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert sample data for testing
INSERT INTO users (username, email, password, full_name, farm_name) VALUES
('admin', 'admin@aquaguru.com', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Admin User', 'AquaGuru Farm');

-- Sample pond
INSERT INTO ponds (user_id, pond_name, area, seed_count, species, stocking_date) VALUES
(1, 'Pond A1', 2.5, 10000, 'Vannamei', CURDATE());

-- Sample feed record
INSERT INTO feed_records (user_id, pond_id, date, doc, abw, survival, feed_percentage, biomass, daily_feed, feed_per_session, amount) VALUES
(1, 1, CURDATE(), 30, 5.5, 85.5, 4.0, 468.75, 18.75, 6.25, 18.75);

-- Sample growth record
INSERT INTO growth_records (user_id, pond_id, date, doc, abw, adg, survival, biomass, fcr) VALUES
(1, 1, CURDATE(), 30, 5.5, 0.15, 85.5, 468.75, 1.2);

-- Sample water quality
INSERT INTO water_quality (user_id, pond_id, date, ph, do, temperature, salinity, ammonia, nitrite, alkalinity, transparency, status) VALUES
(1, 1, NOW(), 7.8, 5.2, 28.5, 15.0, 0.05, 0.02, 120.0, 30.0, 'good');

-- Sample expense
INSERT INTO expenses (user_id, pond_id, category, amount, date, description) VALUES
(1, 1, 'Feed', 1250.00, CURDATE(), 'Monthly feed purchase');

-- Sample inventory
INSERT INTO inventory (user_id, item_name, category, quantity, unit, min_quantity, current_quantity, price_per_unit) VALUES
(1, 'Shrimp Feed Pellets', 'Feed', 500, 'kg', 100, 350, 25.00);

-- Sample harvest
INSERT INTO harvest (user_id, pond_id, harvest_date, production, average_weight, price, income, total_cost, profit) VALUES
(1, 1, CURDATE(), 850.0, 15.2, 280.00, 238000.00, 185000.00, 53000.00);

-- Sample notification
INSERT INTO notifications (user_id, title, message, type, scheduled_date) VALUES
(1, 'Feed Reminder', 'Pond A1 needs feeding at 6:00 AM', 'feed_reminder', NOW());

-- Create indexes for better performance
CREATE INDEX idx_ponds_user_id ON ponds(user_id);
CREATE INDEX idx_feed_records_user_id ON feed_records(user_id);
CREATE INDEX idx_growth_records_user_id ON growth_records(user_id);
CREATE INDEX idx_water_quality_user_id ON water_quality(user_id);
CREATE INDEX idx_expenses_user_id ON expenses(user_id);
CREATE INDEX idx_inventory_user_id ON inventory(user_id);
CREATE INDEX idx_harvest_user_id ON harvest(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);