-- KrishiVeda MySQL schema (MySQL 8.0+, utf8mb4 for Hindi text).
-- The backend creates these tables automatically on startup (SQLAlchemy create_all);
-- this file documents the same schema and can be run manually:
--   mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS krishiveda CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE krishiveda;

CREATE TABLE IF NOT EXISTS farmers (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  name               VARCHAR(100) NOT NULL,
  phone              VARCHAR(15) NULL,
  preferred_language VARCHAR(5)   NOT NULL DEFAULT 'en',
  state              VARCHAR(60)  NULL,
  district           VARCHAR(60)  NULL,
  village            VARCHAR(100) NULL,
  created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         DATETIME     NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS farms (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id       INT          NOT NULL,
  name            VARCHAR(100) NOT NULL DEFAULT 'My Farm',
  location_name   VARCHAR(120) NULL,
  latitude        DOUBLE       NULL,
  longitude       DOUBLE       NULL,
  area_acres      DOUBLE       NULL,
  soil_type       VARCHAR(40)  NULL,
  irrigation_type VARCHAR(40)  NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_farms_farmer_id (farmer_id),
  CONSTRAINT fk_farms_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS farm_crops (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  farm_id     INT         NOT NULL,
  crop_name   VARCHAR(40) NOT NULL,
  season      VARCHAR(20) NULL,          -- kharif / rabi / zaid
  sowing_date DATE        NULL,
  created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_farm_crops_farm_id (farm_id),
  CONSTRAINT fk_farm_crops_farm FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS disease_analyses (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id       INT          NULL,
  image_name      VARCHAR(255) NULL,
  image_sha256    CHAR(64)     NOT NULL,     -- the image itself is not stored
  status          VARCHAR(20)  NOT NULL,     -- healthy / diseased / uncertain / no_leaf
  predicted_class VARCHAR(80)  NOT NULL,
  crop            VARCHAR(40)  NULL,
  disease         VARCHAR(80)  NULL,
  confidence      DOUBLE       NOT NULL,
  top_predictions JSON         NOT NULL,
  model_version   VARCHAR(40)  NOT NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_disease_farmer_created (farmer_id, created_at),
  CONSTRAINT fk_disease_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS crop_recommendations (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id        INT         NULL,
  inputs           JSON        NOT NULL,     -- N, P, K, temperature, humidity, ph, rainfall
  recommended_crop VARCHAR(40) NOT NULL,
  confidence       DOUBLE      NOT NULL,
  alternatives     JSON        NOT NULL,
  model_version    VARCHAR(40) NOT NULL,
  created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_croprec_farmer_created (farmer_id, created_at),
  CONSTRAINT fk_croprec_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS weather_records (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  location_name VARCHAR(120) NOT NULL,
  latitude      DOUBLE       NOT NULL,
  longitude     DOUBLE       NOT NULL,
  temperature_c DOUBLE       NULL,
  humidity_pct  DOUBLE       NULL,
  rain_mm       DOUBLE       NULL,
  `condition`   VARCHAR(80)  NULL,
  source        VARCHAR(40)  NOT NULL,       -- open-meteo / openweather
  observed_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_weather_location_observed (location_name, observed_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS market_prices (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  commodity   VARCHAR(60)  NOT NULL,
  variety     VARCHAR(60)  NULL,
  market      VARCHAR(100) NOT NULL,
  district    VARCHAR(60)  NULL,
  state       VARCHAR(60)  NULL,
  min_price   DOUBLE       NULL,
  max_price   DOUBLE       NULL,
  modal_price DOUBLE       NULL,
  unit        VARCHAR(20)  NOT NULL DEFAULT 'Rs/quintal',
  price_date  DATE         NOT NULL,
  source      VARCHAR(120) NOT NULL,
  is_demo     BOOLEAN      NOT NULL DEFAULT FALSE,
  fetched_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_market_commodity_date (commodity, price_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expert_questions (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id    INT          NULL,
  farmer_name  VARCHAR(100) NOT NULL,
  phone        VARCHAR(15)  NULL,           -- visible only in the Expert Panel, for call-back
  crop         VARCHAR(40)  NULL,
  category     VARCHAR(20)  NOT NULL,       -- disease / pest / irrigation / soil / weather / market / other
  question     TEXT         NOT NULL,
  language     VARCHAR(5)   NOT NULL DEFAULT 'en',
  status       VARCHAR(10)  NOT NULL DEFAULT 'open',   -- open / answered
  answer       TEXT         NULL,
  expert_name  VARCHAR(100) NULL,
  answered_at  DATETIME     NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_expert_status_created (status, created_at),
  INDEX ix_expert_farmer_created (farmer_id, created_at),
  CONSTRAINT fk_expert_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS advisory_messages (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id  INT         NULL,
  question   TEXT        NOT NULL,
  answer     TEXT        NOT NULL,
  provider   VARCHAR(40) NOT NULL,           -- anthropic / knowledge_base
  language   VARCHAR(5)  NOT NULL DEFAULT 'en',
  created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_advisory_farmer_created (farmer_id, created_at),
  CONSTRAINT fk_advisory_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Optional: a dedicated application user (change the password!)
-- CREATE USER 'krishiveda'@'localhost' IDENTIFIED BY 'change-me';
-- GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON krishiveda.* TO 'krishiveda'@'localhost';
