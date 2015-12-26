# This is your "setup.py" file.
# See the following sites for general guide to Python packaging:
#   * `The Hitchhiker's Guide to Packaging <http://guide.python-distribute.org/>`_
#   * `Python Project Howto <http://infinitemonkeycorps.net/docs/pph/>`_

from setuptools import setup, find_packages
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

version = '0.1.0'

install_requires = [
    'pyvirtualdisplay', 'selenium'
]



setup(name='flickr-album-embed-codes',
    version=version,
    description="extract HTML embed codes from all images of a Flickr album",
    long_description=README,
    keywords='flickr album photoset embed-code',
    author='Arne Neumann',
    author_email='flickr.programming@arne.cl',
    url='https://github.com/arne-cl/flickr-album-embed-codes',
    license='3-Clause BSD License',
    py_modules=['album2embedcodes'],
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            ['flickr-album-embed-codes=album2embedcodes:cli']
    }
)
