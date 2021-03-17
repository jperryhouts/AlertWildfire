#!/usr/bin/env python3

"""
Brute force method for scraping AlertWildfire imagery. Use a Selenium
driver to load the webpage, then periodically screenshot the segment
of the page where the imagery is displayed.

## Usage:
    while [ 1 == 1 ]; do ./scrape.py ~/Data/Storage/AlertWF/Brightwood/ ; done
"""

import os, sys, time
from tempfile import NamedTemporaryFile
from datetime import datetime

from PIL import Image
from selenium import webdriver # type: ignore


URL = "http://www.alertwildfire.org/oregon/index.html?camera=Axis-Brightwood"


def mktemp(suffix: str) -> str:
    with NamedTemporaryFile(suffix=suffix) as tmpf:
        tmpname = tmpf.name
    return tmpname


if __name__ == '__main__':
    outputdir = sys.argv[-1]
    assert os.path.isdir(outputdir), 'Specify an output directory'

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    with webdriver.Chrome(options=options) as driver:
        driver.fullscreen_window()
        driver.get(URL)
        time.sleep(5)
        max_btn = driver.find_elements_by_class_name('max-btn')[0]
        driver.execute_script("arguments[0].click();", max_btn)
        for c in ('max-btn', 'play-ctrl', 'camera-health-check-component'):
            el = driver.find_elements_by_class_name(c)[0]
            driver.execute_script("arguments[0].style.display = 'none';", el)
        time.sleep(2)

        el = driver.find_element_by_xpath("//*[@id=\"camera-block\"]")
        driver.execute_script("arguments[0].scrollIntoView();", el)
        time.sleep(2)

        el = driver.find_element_by_xpath("//*[@id=\"camera-block\"]")
        location = el.location
        size = el.size
        x0, y0 = location['x'], location['y']
        y0 = 0.0
        x1, y1 = (x0+size['width']), (y0+size['height'])

        last_saved = None
        while True:
            tmpImgName = mktemp('.png')
            driver.save_screenshot(tmpImgName)
            img = Image.open(tmpImgName)
            img = img.crop((int(x0), int(y0), int(x1), int(y1)))
            imgBytes = img.tobytes()
            if imgBytes != last_saved:
                print("Saving screen capture")
                last_saved = imgBytes
                img.save(f"{outputdir}/Brightwood_{datetime.now().isoformat()}.jpg")
            else:
                print("Skipping save (image has not changed)")
            os.remove(tmpImgName)
            time.sleep(10)
