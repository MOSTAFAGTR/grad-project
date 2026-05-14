-- Drop table if exists
DROP TABLE IF EXISTS accounts;

-- Create the accounts table
CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    balance INT DEFAULT 100
);

-- Insert Alice (Victim) and Bob (Attacker)
INSERT INTO accounts (username, balance) VALUES ('Alice', 1000);
INSERT INTO accounts (username, balance) VALUES ('Bob', 0);