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
"""

from __future__ import absolute_import, division, print_function
import argparse
import re
import sys
import time

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, WebDriverException)


# string that includes the width, height and URL of a hotlinked image on
# a Flickr album page
STYLE_STRING_PATTERN = """
.*? # ignore
width:\ (?P<width>\d+) # width
.*? # ignore
height:\ (?P<height>\d+) # height
.*? # ignore
//(?P<url>.*)" # hotlink URL
"""

# The URL of an image used on a Flickr album page is not the same as the
# one they use in their HTML embed codes. Since we're playing nice,
# we will only URLs that would also be used for embed codes.
HOTLINK_URL_REGEX = """
^                      # beginning of string
(?P<subdomain>c\d+)    # subdomain, e.g. c1
\.staticflickr.com/    # domain
(?P<farm_id>\d+)/      # ID of the server farm
(?P<image_id>.*?)      # ID of the image
(?P<image_size>(_\S)?) # optional suffix, e.g. '_z'
                       # (for dimensions other than 500x334px)
\.jpg                  # file extension
$                      # end of string
"""


def get_orientation(width, height):
    """
    returns the orientation of an image.

    Returns
    -------
    orientation : str
        'landscape', if the image is wider than tall. 'portrait', otherwise.
    """
    return 'landscape' if width > height else 'portrait'


def _get_visible_photos(browser, known_urls, output=None):
    """
    extracts all *currently visible* photo URLs from a Flickr photoset/album
    page, converts them into "embed code compatible" (i.e. sanctioned by
    Flickr) URLs and returns them.

    Parameters
    ----------
    browser : TODO ???
        a selenium webdriver instance
    known_urls : set
        a set of embed code compatible image URLs already extracted from
        the current page. We'll update this list, if we find new image
        after scrolling down the page.
    output : str or None
        if 'cli': print an embed code as soon as a new image is found/parsed

    Returns
    -------
    known_urls : set(str)
        a set of embed code compatible image URLs
    """
    image_elems = browser.find_elements_by_class_name('awake')
    for elem in image_elems:
        style_attrib = elem.get_attribute('style')
        match = re.match(STYLE_STRING_PATTERN, style_attrib, re.VERBOSE)
        width = int(match.group('width'))
        height = int(match.group('height'))
        orientation = get_orientation(width, height)
        url = match.group('url')

        # URL of the page that only shows one image
        try:
            image_page_elem = elem.find_element_by_class_name('overlay')
            image_page = image_page_elem.get_attribute('href')
        except NoSuchElementException as e:
            image_page = browser.current_url

        # title of the image
        try:
            title_elem = elem.find_element_by_class_name('interaction-bar')
            title_str = title_elem.get_attribute('title')
            title = re.match('^(?P<title>.*) by.*$', title_str).group('title')
        except NoSuchElementException as e:
            title = ''

        try:
            embed_url = hotlink_url2embed_url(url)
            if output == 'cli' and (not embed_url in known_urls):
                embed_code = embed_url2embed_code(
                    embed_url, image_page, title, orientation)
                print(embed_code+'\n')

            known_urls.add(embed_url)
        except AttributeError as e:
            raise AttributeError("Warning: can't convert URL: {}".format(url))
    return known_urls


def _get_page_photos(browser, output=None):
    """
    returns all photo URLs from a Flickr photoset/album page, by scrolling
    down multiple times.

    Parameters
    ----------
    browser : TODO ???
        a selenium webdriver instance
    output : str or None
        if 'cli': print an embed code as soon as a new image is found/parsed
    """
    urls = set()
    num_of_urls = 0

    while num_of_urls < 100:
        # this seems to be the canonical way to scroll "to the bottom"
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        current_num_of_urls = len(_get_visible_photos(
            browser, urls, output=output))

        if current_num_of_urls > num_of_urls:
            num_of_urls = current_num_of_urls
        else:
            break
    return _get_visible_photos(browser, urls, output=output)


def get_photo_urls(album_url, browser, wait=2, output=None, progressbar=True):
    """
    returns a list of URLs of all photos belonging to
    the given album / photoset.

    Parameters
    ----------
    album_url : str
        URL of a Flickr album / photoset page
    browser : TODO ???
        a selenium webdriver instance
    wait : int
        time in seconds to wait/retry before a network/browser-related error is
        thrown (default: 2)
    output : str or None
        if 'cli': print an embed code as soon as a new image is found/parsed

    Returns
    -------
    photo_urls : set(str)
        a set of embed code compatible image URLs
    """
    browser.implicitly_wait(wait)
    browser.get(album_url)
    if 'Problem' in browser.title:  # the website can't be reached
        raise WebDriverException(browser.title)
    if not browser.find_elements_by_class_name('awake'):
        raise NoSuchElementException('Is this really a Flickr Album page?')

    if progressbar:
        from tqdm import tqdm
        photo_count_elem = browser.find_element_by_class_name('photo-counts')
        photo_count = int(photo_count_elem.text.split()[0])
        pbar = tqdm(total=photo_count)

    photo_urls = _get_page_photos(browser, output=output)

    if progressbar:
        pbar.update(len(photo_urls))

    # get URLs from follow-up pages, if any
    next_page = True
    while next_page:
        try:
            # this is not really a button, but you know what I mean ...
            next_page_button = browser.find_element_by_xpath(
                "//a[@data-track='paginationRightClick']")
            next_page_button.click()
            next_page_photos = _get_page_photos(browser, output=output)
            photo_urls.update(next_page_photos)
            if progressbar:
                pbar.update(len(next_page_photos))
        except NoSuchElementException as e:
            next_page = False
    return photo_urls


def hotlink_url2embed_url(hotlink_url):
    """
    Given a image URL extracted from a Flickr album page, returns the
    corresponding URL for embedding that image into another website. These
    URLs differ in terms of the server name and directory structure.

    Since images on a Flickr album page are shown in different sizes
    (for design purposes), we will have to 'normalize' the URL first, in order
    to always embed images of the same size (i.e. 500x334).

    Flickr image sizes
    ------------------

    without ending: 500 x 334
    ending with _b: 100 x 668
    ending with _c: 800 x 543
    ending with _z: 640 x 428
    ending with _o: 100 x 668 (or "original size")
    """
    match = re.match(HOTLINK_URL_REGEX, hotlink_url, re.VERBOSE)
    embed_url = 'https://farm{}.staticflickr.com/{}.jpg'.format(
        match.group('farm_id'), match.group('image_id'))
    return embed_url


def embed_url2embed_code(image_url, image_page, title, orientation):
    """
    creates an HTML embed code for a given Flickr image of medium dimensions
    (i.e. 500x334 or 334x500).
    """
    if orientation == 'landscape':
        width = 500
        height = 334
    else:
        width = 334
        height = 500

    embed_code = (
        u'<a data-flickr-embed="true" href="{image_page}" '
        'title="{image_title}"> <img src="{image_url}" '
        'width="{width}" height="{height}" '
        'alt="{image_title}"></a>').format(
            image_page=image_page, image_title=title, image_url=image_url,
            width=width, height=height)
    return embed_code


def get_headless_browser():
    """
    returns a headless (i.e. invisible) Firefox browser instance.
    cf. http://stackoverflow.com/a/8910326
    """
    display = Display(visible=0, size=(1024, 768))
    display.start()

    # now Firefox will run in a virtual display.
    # you will not see the browser.
    return webdriver.Firefox()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "extract HTML embed codes from a Flickr album")
    parser.add_argument('--debug', action='store_true',
                        help="enable debug mode")
    parser.add_argument(
        'album_url',
        help='URL of the Flickr album/photoset to extract embed codes from')
    parser.add_argument(
        'output_file', nargs='?', default=sys.stdout,
        help='output file')


    args = parser.parse_args(sys.argv[1:])
    if args.debug:
        import pudb
        pudb.set_trace()
        browser = webdriver.Firefox()
    else:
        browser = get_headless_browser()

    try:
        photo_urls = get_photo_urls(args.album_url, browser, output='cli')
    finally:
        browser.close()
