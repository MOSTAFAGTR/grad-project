USE scale_db;

-- security_logs: add missing telemetry columns safely
SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'security_logs'
        AND COLUMN_NAME = 'geo_bucket'
    ),
    'SELECT 1',
    'ALTER TABLE security_logs ADD COLUMN geo_bucket VARCHAR(50) NULL'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'security_logs'
        AND COLUMN_NAME = 'session_id'
    ),
    'SELECT 1',
    'ALTER TABLE security_logs ADD COLUMN session_id VARCHAR(100) NULL'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'security_logs'
        AND COLUMN_NAME = 'correlation_id'
    ),
    'SELECT 1',
    'ALTER TABLE security_logs ADD COLUMN correlation_id VARCHAR(100) NULL'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'security_logs'
        AND COLUMN_NAME = 'context_type'
    ),
    'SELECT 1',
    'ALTER TABLE security_logs ADD COLUMN context_type VARCHAR(50) DEFAULT ''real'''
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- user_learning_progress: add missing learning analytics columns safely
SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'user_learning_progress'
        AND COLUMN_NAME = 'streak_days'
    ),
    'SELECT 1',
    'ALTER TABLE user_learning_progress ADD COLUMN streak_days INT DEFAULT 0'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'user_learning_progress'
        AND COLUMN_NAME = 'learning_speed'
    ),
    'SELECT 1',
    'ALTER TABLE user_learning_progress ADD COLUMN learning_speed FLOAT DEFAULT 0'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS(
      SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'user_learning_progress'
        AND COLUMN_NAME = 'retention_score'
    ),
    'SELECT 1',
    'ALTER TABLE user_learning_progress ADD COLUMN retention_score FLOAT DEFAULT 0'
  )
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
