# AlertWildfire Image Recognition

This project aims to automatically identify nascent wildfires in live imagery using neural networks.

Currently, fire lookout stations are deployed in [hundreds of sites around the western US](http://www.alertwildfire.org/about.html).
Each station includes a pan/tilt/zoom camera with near-infrared capability.
All stations continuously stream high resolution imagery at several frames per minute to centralized servers for human monitoring and analysis.

Lookout stations are [extremely expensive to deploy](https://www.youtube.com/watch?v=ZU2NJtJE1H8), because their high power and bandwidth consumption requires access to a reliable energy source and communications equipment.
Because of their resource needs, monitoring stations are typically co-located with existing communications infrastructure.
Remote sites which require dedicated solar power harvesting, power storage, and radio antennas are 3-5 times more expensive, and are therefore only installed in limited critical locations.
This leaves many rural areas without reliable systems for identifying and reporting early-stage fires, resulting in slower emergency response and larger overall burns.

The goal of this project is to develop an AI algorithm capable of operating on low-power embedded systems, allowing lookout stations to autonomously decide when to upload data, and when to conserve their resources.
If successful, this approach could dramatically reduce the bandwidth and power consumed by each station, lowering the cost of installing and operating individual nodes, and enabling wider deployment to a larger number of monitoring sites.

## Data

Data handling is described in [DATA.md](./DATA.md).

## Coming soon...

This documentation is a work in progress, and more will be added here as the project progresses.

<!-- 
### Data acquisition

Data for this project was obtained by scraping the [alertwildfire live streams](http://www.alertwildfire.org/oregon/index.html?camera=Axis-Brightwood).
I've focused on the Brightwood, OR site as training data for this proof of concept model.

#### Method 1 (Selenium scraper):

The site is unfortunately not an easy source to scrape because its live imagery is represented as a dynamic javascript canvas element which is automatically updated via a JavaScript partial page refresh.
The brute force approach to scraping that sort of dynamic web content relies on a full browser engine to render the web page, including its dynamic elements.
I started by developing a spider based on the [Selenium web driver](https://github.com/SeleniumHQ/selenium), which is stored in the [WebScraper](./WebScraper/) directory of this repository.

Selenium is a heavy-weight tool for "browser automation", which effectively means that it interacts with the web exactly as a browser would.
It literally starts a full web browser, but operates it in "headless mode" where graphics are drawn to a virtual screen, without opening an actual gui window.
The [WebScraper/spider.py](./WebScraper/spider.py) script loads the alertwildfire live stream webpage, simulates a click on the 'full screen' icon to enlarge the image, and periodically "screenshots" the actual imagery to a file on the local filesystem.

The live feed updates approximately every 20-30 seconds.
In order to catch each new image, the scraper takes a new screenshot every 10 seconds.
It remembers the pixels from the most recent saved screenshot, and compares each subsequent screenshot to eliminate duplicate data.

#### Method 2 (API query):

I originally built the Selenium scraper because the image refresh mechanism appeared to be handled through some third-party JavaScript library, and untangling how it worked seemed challenging.
However, minimal poking around in the browser's HTTP traffic revealed that the images are simply refreshed from a single S3 endpoint.
The endpoint is configured to only respond to network traffic referred from the AlertWildfire URL, but otherwise there is no authentication required.
This seems obvious, since it's a public live stream and authentication would be useless, as evidenced by my Selenium web scraper above, but I had assumed that because they're using some sort of general purpose streaming library, there may be some anti-piracy thing built in.

Anyway, it now appears that I can scrape live data by simply querying their S3 endpoint:

```bash
curl -O -e 'https://www.alertwildfire.org/' \
    "https://s3-us-west-2.amazonaws.com/alertwildfire-data-public/Axis-Brightwood/latest_full.jpg"
```

I implemented an automated scraping pipeline in [scraper.py](./scraper.py).

### Metadata extraction

Imagery available through AlertWildfire is associated with metadata that describes the camera's orientation and zoom, as well as a timestamp for the precise time at which each image was taken.
As with the imagery itself, metadata is not presented in an easily scrape-able way: it is embedded as a watermark within each live streamed image.
In order to extract that information, I have developed a workflow for extracting the watermark information using an [OCR](https://en.wikipedia.org/wiki/Optical_character_recognition) library.

Code in [Imagery_ETL.ipynb](./Imagery_ETL.ipynb) walks through the process of opening each image, cropping the image down to the black bar in the lower left corner, and extracting text from it using [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).
Surprisingly, the most challenging part of that process is cropping to the correct region.
The black box containing metadata text is always the same height, and same number of pixels from the bottom of the image, but its width varies depending on the length of the text it contains.
This changes from image to image as the orientation and zoom of the camera switch from single digits to double or triple digits, and switch from negative to positive as the camera moves.

Leaving unpredictable bits of non-text at the end of the cropped pixel frame is apparently too much for Tesseract to handle, so cropping to the correct width is really important.
After cropping the image to its predefined vertical range, I take the median of each each column of pixels in the wide/thin strip. Pixels in the text box should be either fully black or fully white, while I expect pixels in the rest of the strip to be more randomly distributed.
I then filter the array of medians to either fully black or fully white regions, and find the longest contiguous stretch from the left side of the frame which match that condition.
Unfortunately, because these images are by this point re-encoded several times using jpeg compression, there is some noise in these pixels.
I therefore smooth the vector of medians before operating on it in order to smooth out any irregularities.
Lastly, I pass the cropped pixel array into tesseract, and validate its format by matching it to a regular expression.

As of the time of writing this, I've extracted metadata from about 30,000 images using the method described above, and only a handful of images have been unsuccessful.
All of those were cases where the camera had gone down, and the spider was scraping full frames of black pixels with no data at all.

### Labeling

Tagging images for various characteristics must be done manually, so I created an interactive app using ipywidgets to assist with that process ([Labeling.ipynb](./Labeling.ipynb))\*\*.
It presents the user with one image at a time, and listens for keyboard input to identify what label should be applied before moving on to the next image.
It allows the user to skip images, or scroll back to previous images using the arrow keys.

The app is built to enable arbitrary sorting of images presented to the user.
It is currently configured to simply iterate through imagery data sequentially, but I plan to implement an "active learning" approach whereby the app  skips images that it can already confidently identify on its own, and request user input on the images which it is least capable of classifying.

\*\* *Note:* This tool is not yet complete.

## Features \& labels

### Feature selection

Having not yet attempted model fitting for this data I'm not yet sure which features will be important, but the most obvious ones are the individual components of the timestamp (time of day and day of the year) which I extract to a dedicated `Features` table.
I anticipate that bulk metrics derived from the raw imagery will be less valuable than the imagery itself.
However, I do extract some simple statistics from each image, including the pixel mean, median, and standard deviation, as well as the [image entropy](https://stats.stackexchange.com/questions/235270/entropy-of-an-image).

### Label selection

I obviously need to tag any images that have smoke in them, but those images are few and far between (I don't have any of them at the moment, actually).
But besides that, there are some other categories of images that are important to identify.
Namely, it's useful to first discard any images that are blurry or otherwise obscured.

The AlertWildfire cameras continuously pan around their field of view, collecting images at fixed time intervals.
Shutter triggering seems to be independent of the mechanism for panning, so there are a significant number of images that get captured during the process of swiveling, producing extremely blurred images.
Because these cameras are deployed outdoors they are obviously susceptible to other factors that may obscure their view such as snow cover, raindrops on the lens, dense fog, sun glare, or curious birds.

Many of these conditions would be simple to detect automatically.
Fog, for example, could potentially be identified through a single metric like image entropy.
But other conditions like nosy birds are more complicated.
It isn't clear to me yet whether it would be worth training many individual models suited to each case, or one complex neural network that detects all categories of obstructions.
At this point I am labeling each condition as a separate category, but I may combine them into a single "obscured" vs "clear" flag later on.
 -->