# a '-' before a shell command causes make to ignore its exit code (errors)

install:
	python setup.py install

uninstall:
	yes | pip uninstall flickr-album-embed-codes

clean:
	find . -name '*.pyc' -delete
	rm -rf build dist *.egg-info __pycache__

