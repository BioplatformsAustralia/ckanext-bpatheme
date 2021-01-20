#!/usr/bin/env/python
from setuptools import setup

install_requires=[
    'pandas==0.24.2',
]

setup(
    name='ckanext-bpatheme',
    version='3.0.6',
    description='',
    license='AGPL3',
    author='data.wa.gov.au team',
    author_email='florian.mayer@dpaw.wa.gov.au',
    url='http://govhack2015.readthedocs.org/',
    namespace_packages=['ckanext'],
    packages=['ckanext.bpatheme'],
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,
    package_dir={'ckanext.bpatheme': 'ckanext/bpatheme'},
    package_data={'ckanext.bpatheme': ['*.json', 'fanstatic/*.js', 'fanstatic/styles/*.css', 'fanstatic/styles/*.scss', 'templates/*.html', 'templates/*/*.html',
                                               'templates/*/*/*.html', 'static/datacats/*.png', 'static/fonts/arial/*.eot', 'static/fonts/arial/*.svg', 'static/fonts/arial/*.woff', 'static/fonts/arial/*.woff2', 'static/fonts/arial/*.ttf', 'static/*.png', 'static/*.ico', 'static/bootstraptable/*.js', 'static/bootstraptable/*.css']},

    entry_points="""
        [ckan.plugins]
        bpa_theme = ckanext.bpatheme.plugins:CustomTheme
    """
)
