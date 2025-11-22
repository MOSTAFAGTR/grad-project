-- Drop old tables if they exist
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS posts;

-- Posts table (stores the main post content)
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL
);

-- Comments table (vulnerable to stored XSS)
CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    comment TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Insert a sample post
INSERT INTO posts (title, content)
VALUES ('Welcome Post', 'This is the first post — try adding a comment below!');

-- Example comment (optional)
-- INSERT INTO comments (post_id, comment)
-- VALUES (1, '<script>alert("XSS")</script>');
