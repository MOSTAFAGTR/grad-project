-- This script will be run automatically by the MySQL container on first startup.

-- Switch to our application's database
USE scale_db;

-- Create the dedicated table for the challenge
CREATE TABLE IF NOT EXISTS challenge_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);

-- Insert the 15 prepared users into the table
INSERT INTO challenge_users (username, password) VALUES
('user1', 'password1'),
('user2', 'password2'),
('user3', 'password3'),
('user4', 'password4'),
('user5', 'password5'),
('user6', 'password6'),
('user7', 'password7'),
('user8', 'password8'),
('user9', 'password9'),
('user10', 'password10'),
('user11', 'password11'),
('user12', 'password12'),
('user13', 'password13'),
('user14', 'password14'),
('user15', 'admin_challenge'); -- Added a different one for variety