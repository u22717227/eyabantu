DROP DATABASE IF EXISTS eyabantu;
CREATE DATABASE eyabantu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eyabantu;

CREATE TABLE associations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    region VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(160) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('commuter', 'driver', 'association') NOT NULL,
    association_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (association_id) REFERENCES associations(id)
);

CREATE TABLE routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    association_id INT NOT NULL,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    fare_zar DECIMAL(10, 2) NOT NULL CHECK (fare_zar > 0),
    avg_speed_kmh DECIMAL(10, 2) NOT NULL,
    in_open_dataset BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (association_id) REFERENCES associations(id)
);

CREATE TABLE stops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lat DOUBLE NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lng DOUBLE NOT NULL CHECK (lng BETWEEN -180 AND 180),
    is_rank BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE route_stops (
    route_id INT NOT NULL,
    seq SMALLINT NOT NULL,
    stop_id INT NOT NULL,
    km_from_start DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (route_id, seq),
    FOREIGN KEY (route_id) REFERENCES routes(id),
    FOREIGN KEY (stop_id) REFERENCES stops(id),
    UNIQUE KEY uk_route_stop (route_id, stop_id)
);

CREATE TABLE taxis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration VARCHAR(20) UNIQUE NOT NULL,
    driver_id INT UNIQUE,
    route_id INT,
    sharing_gps BOOLEAN DEFAULT FALSE,
    status ENUM('off_duty', 'loading', 'en_route') DEFAULT 'off_duty',
    capacity INT NOT NULL CHECK (capacity BETWEEN 4 AND 22),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES users(id),
    FOREIGN KEY (route_id) REFERENCES routes(id)
);

CREATE TABLE gps_pings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    taxi_id INT NOT NULL,
    lat DOUBLE NOT NULL,
    lng DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (taxi_id) REFERENCES taxis(id)
);

CREATE TABLE demand_pins (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    route_id INT NOT NULL,
    stop_id INT NOT NULL,
    pin_type ENUM('pickup', 'dropoff') DEFAULT 'pickup',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (route_id, stop_id) REFERENCES route_stops(route_id, stop_id)
);

CREATE TABLE safety_confirmations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    stop_id INT NOT NULL,
    taxi_id INT DEFAULT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (stop_id) REFERENCES stops(id),
    FOREIGN KEY (taxi_id) REFERENCES taxis(id)
);

CREATE TABLE favourite_routes (
    user_id INT NOT NULL,
    route_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, route_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (route_id) REFERENCES routes(id)
);

CREATE INDEX idx_gps_latest ON gps_pings(taxi_id, created_at);
CREATE INDEX idx_demand_window ON demand_pins(route_id, created_at);
CREATE INDEX idx_demand_heat ON demand_pins(created_at, stop_id);
CREATE INDEX idx_safety_avg ON safety_confirmations(stop_id, created_at);
CREATE INDEX idx_taxi_active ON taxis(route_id, status);