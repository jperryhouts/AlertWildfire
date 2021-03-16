
<table style='display:block; width: 100%'>
    <tr><th>Table</th><th>Columns</th></tr>
    <tr><td>stations</td><td>name, lon, lat, elevation</td></tr>
    <tr><td>weather</td><td>station, time_stamp, temperature, wind, precip, ...</td></tr>
    <tr><td>images</td><td>
        station, time_stamp, path, resolution, azimuth, tilt, zoom, night_mode,<br/>
        feature_{min, max, mean, median, grad_x_entropy, grad_y_entropy}
    </td></tr>
</table>

```sql
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
```

<!--
```python
import numpy as np
from skimage import data
from skimage.io import imread, imsave
from skimage.util import img_as_ubyte
from skimage.filters.rank import entropy
from skimage.morphology import disk
from skimage.color import rgb2hsv, rgb2gray, rgb2yuv

img = imread('fname.jpg')
img_gray = rgb2gray(img)
img_entropy = entropy(img_gray, disk(5))
imsave('fname-entropy.jpg', img_entropy)
```
-->
