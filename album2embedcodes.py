#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <flickr.programming@arne.cl>

"""
This module contains code for retrieving HTML embed codes for all images in a
given Flickr photoset/album URL.

Unforturnately, not all photosets which are visible on the website can be
accessed via Flickr's REST API. We can't simply extract the URLs from the
HTML source either, so we'll have to use a Javascript-capable library for
scraping (i.e. selenium).


NOTES:

668 x 1000 vorschau

c1.staticflickr.com/1/703/21526920079_554534770b_b.jpg

668 x 1000 embed

<a data-flickr-embed="true"  href="https://www.flickr.com/photos/endless_autumn/21526920079/in/album-72157659099366191/" title="Strand Child"><img src="https://farm1.staticflickr.com/703/21526920079_554534770b_b.jpg" width="668" height="1000" alt="Strand Child"></a><script async src="//embedr.flickr.com/assets/client-code.js" charset="utf-8"></script>

---

c1.staticflickr.com/1/718/21702233832_1427e9a5ac.jpg

---

http://c2.staticflickr.com/6/5807/21687640406_ed7c7fb8af.jpg

500 x 334
http://farm6.staticflickr.com/5807/21687640406_ed7c7fb8af.jpg

1000 x 668
http://farm6.staticflickr.com/5807/21687640406_ed7c7fb8af_b.jpg

800 x 543
http://farm6.staticflickr.com/5807/21687640406_ed7c7fb8af_c.jpg

640 x 428
http://farm6.staticflickr.com/5807/21687640406_ed7c7fb8af_z.jpg

1000 x 668 (original)
https://farm6.staticflickr.com/5807/21687640406_5b98071d3d_o.jpg


"""

from __future__ import absolute_import, division, print_function
import argparse
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.keys import Keys


def get_all_photo_urls_from_current_page(driver, debug=False):
    """
    returns all photo URLs from a Flickr photoset/album page, by scrolling
    down multiple times.
    """
    def extract(driver, debug=False):
        """
        returns all *currently visible* photo URLs from a Flickr photoset/album
        page.
        """
        photo_urls = set()
        
        image_elems = driver.find_elements_by_class_name('overlay')
        for elem in image_elems:
            url = elem.get_attribute('href')
            if debug is True and (not url in photo_urls):
                print(url)
            photo_urls.add(url)
        return photo_urls

    num_of_urls = 0
    while num_of_urls < 100:
        # this seems to be the canonical way to scroll "to the bottom"
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        current_num_of_urls = len(extract(driver, debug=debug))
        if debug:
            print(current_num_of_urls)

        if current_num_of_urls > num_of_urls:
            num_of_urls = current_num_of_urls
        else:
            break
    return extract(driver)


def get_photo_urls(album_url, driver, wait=2, debug=False):
    """
    returns a list of URLs of all photos belonging to
    the given album / photoset.
    """   
    driver.implicitly_wait(wait)
    driver.get(album_url)
    if 'Problem' in driver.title:  # the website can't be reached
        raise WebDriverException(driver.title)
    if not driver.find_elements_by_class_name('overlay'):
        raise NoSuchElementException('Is this really a Flickr Album page?')

    photo_urls = get_all_photo_urls_from_current_page(driver, debug=debug)

    # get URLs from follow-up pages, if any
    next_page = True
    while next_page:
        try:
            # this is not really a button, but you know what I mean ...
            next_page_button = driver.find_element_by_xpath("//a[@data-track='paginationRightClick']")
            next_page_button.click()
            photo_urls.update(get_all_photo_urls_from_current_page(driver, debug=debug))
        except NoSuchElementException as e:
            next_page = False
    return photo_urls


if __name__ == '__main__':
    parser = argparse.ArgumentParser("extract HTML embed codes from a Flickr album")
    parser.add_argument('--debug', action='store_true',
                        help="enable debug mode")
    parser.add_argument(
        'album_url',
        help='URL of the Flickr album/photoset to extract embed codes from')

    args = parser.parse_args(sys.argv[1:])
    if args.debug:
        import pudb
        pudb.set_trace()

    try:
        driver = webdriver.Firefox()
        photo_urls = get_photo_urls(args.album_url, driver, debug=args.debug)
    finally:
        driver.close()
