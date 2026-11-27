-- Superstore Sales and Profit Analysis - Database Schema
-- This script creates the table structure for the Superstore dataset

-- Drop table if it exists (for clean reloads)
DROP TABLE IF EXISTS superstore;

-- Create the main superstore table
CREATE TABLE superstore (
    row_id          INTEGER PRIMARY KEY,
    order_id        VARCHAR(20) NOT NULL,
    order_date      DATE NOT NULL,
    ship_date       DATE NOT NULL,
    ship_mode       VARCHAR(20) NOT NULL,
    customer_id     VARCHAR(20) NOT NULL,
    customer_name   VARCHAR(100) NOT NULL,
    segment         VARCHAR(20) NOT NULL,
    country         VARCHAR(50) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    state           VARCHAR(50) NOT NULL,
    postal_code     VARCHAR(20),
    region          VARCHAR(20) NOT NULL,
    product_id      VARCHAR(20) NOT NULL,
    category        VARCHAR(20) NOT NULL,
    sub_category    VARCHAR(30) NOT NULL,
    product_name    VARCHAR(200) NOT NULL,
    sales           NUMERIC(12,4) NOT NULL,
    quantity        INTEGER NOT NULL,
    discount        NUMERIC(4,2) NOT NULL,
    profit          NUMERIC(12,4) NOT NULL
);

-- Create indexes for common query patterns
CREATE INDEX idx_order_date ON superstore(order_date);
CREATE INDEX idx_category ON superstore(category);
CREATE INDEX idx_sub_category ON superstore(sub_category);
CREATE INDEX idx_region ON superstore(region);
CREATE INDEX idx_state ON superstore(state);
CREATE INDEX idx_customer_id ON superstore(customer_id);
CREATE INDEX idx_ship_mode ON superstore(ship_mode);
CREATE INDEX idx_discount ON superstore(discount);