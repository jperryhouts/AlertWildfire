CREATE DATABASE IF NOT EXISTS AlertWildfire;
USE AlertWildfire;

CREATE TABLE IF NOT EXISTS stations (
    id VARCHAR(255),
    `name` VARCHAR(255),
    `state` VARCHAR(2),
    lon FLOAT, lat FLOAT, elevation FLOAT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS weather (
    id INT NOT NULL AUTO_INCREMENT,
    station VARCHAR(255),
    time_stamp DATETIME,
    temp_c FLOAT,
    wind_kph FLOAT,
    wind_az FLOAT,
    precip VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS images (
	id INT NOT NULL AUTO_INCREMENT,
    station VARCHAR(255),
    time_stamp DATETIME,
    path VARCHAR(255),
    res_x INT, res_y INT,
    azimuth FLOAT, tilt FLOAT, zoom FLOAT,
    night_mode TINYINT,
    feature_min FLOAT,
    feature_max FLOAT,
    feature_mean FLOAT,
    feature_median FLOAT,
    feature_grad_x_entropy FLOAT,
    feature_grad_y_entropy FLOAT,
    PRIMARY KEY (id)
);