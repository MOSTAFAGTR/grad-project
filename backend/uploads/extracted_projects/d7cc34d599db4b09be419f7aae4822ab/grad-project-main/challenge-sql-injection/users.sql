-- Drop the table if it exists to ensure a clean state for each run
DROP TABLE IF EXISTS users;

-- Create the users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Insert a sample user
INSERT INTO users (username, password) VALUES ('admin', 'password123');