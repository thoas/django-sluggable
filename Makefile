pep8:
	flake8 sluggable --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=sluggable manage.py test sluggable
	coverage report --omit=sluggable/test*

release:
	python setup.py sdist register upload -s
