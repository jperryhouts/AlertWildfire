Data wrangling
=================

## Extract

Data collection currently comes from three sources: live metadata from all lookout cameras, [live imagery](http://www.alertwildfire.org/) from a subset of active lookout sites, and hourly weather data from [openweathermap.org](https://openweathermap.org).

### Images and station metadata

Images and site metadata are obtained by periodically querying the public API endpoint that drives the live web streams on the [alertwildfire](http://www.alertwildfire.org/) website.
Those endpoints are actually just public S3 buckets that are updated regularly. I fetch data from them every 30 seconds, but I believe the actual data is available at a much higher sample rate if it turns out I need higher resolution for whatever reason.

The only challenge with the imagery and metadata are that the S3 bucket is configured to only allow access from the [alertwildfire.org](alertwildfire.org) domain.
It's possible to handle that by just sending a "`Referer: https://www.alertwildfire.org`" header along with each request.

Data retrieval fees become a real consideration if I need to access any of the imagery data, so during the data transformation step I create scaled, lower resolution versions of each image, and save them along side the full resolution version.
I also extract all of the exif data from each image in case I need to query some other image metadata without downloading the full images.

Metadata comes from the same S3 endpoint, and is retrieved for all cameras in the same loop that captures image data. It is lightly cleaned up, and then dumped into .csv files for subsequent processing.

All images and metadata are then uploaded to a dedicated S3 bucket.

### Weather data

It's possible to get data for the past 5 days with an unpaid [openweathermap.org](openweathermap.org) account, but getting data any further back costs money. I had been collecting data from the Axis-Brightwood site in Oregon for about a month before I decided to also log weather data, so I'm considering purchasing access to historical data for that one site farther back in time. It only costs \$10 per location, so if it appears that data will help my model I might go for it.
Until then, I will continue gathering weather data from all the stations which I'm currently archiving.

Weather data retrieval is handled in the [getweather.ipynb](./getweather.ipynb) notebook, which has to be run at least once every five days.
Once I get around to copy-pasting that code into its own script I can just have it automatically run once a day via cron.

## Transform

[Work in progress]

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

## Load

Data is stored in a set of four SQL tables, arranged as follows:

<table style='display:block; width: 100%'>
    <tr><th>Table</th><th>Columns</th></tr>
    <tr><td>stations</td><td>name, lon, lat, elevation</td></tr>
    <tr><td>weather</td><td>station, time_stamp, temperature, wind, precip, ...</td></tr>
    <tr><td>images</td><td>
        station, time_stamp, path, resolution, azimuth, tilt, zoom, night_mode,<br/>
        feature_{min, max, mean, median, grad_x_entropy, grad_y_entropy}
    </td></tr>
</table>

The complete database schema is described in [CreateDBTables.sql](CreateDBTables.sql).