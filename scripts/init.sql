# ================================
# scripts/init.sql
# ================================

-- Script d'initialisation pour MariaDB
CREATE DATABASE IF NOT EXISTS creative_cocktail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE creative_cocktail;

-- Utilisateur pour l'application
CREATE USER IF NOT EXISTS 'creative_user'@'%' IDENTIFIED BY 'creative_password';
GRANT ALL PRIVILEGES ON creative_cocktail.* TO 'creative_user'@'%';
FLUSH PRIVILEGES;

-- Configuration optimisée pour MariaDB
SET GLOBAL innodb_buffer_pool_size = 268435456; -- 256MB
SET GLOBAL max_connections = 200;
SET GLOBAL query_cache_size = 67108864; -- 64MB