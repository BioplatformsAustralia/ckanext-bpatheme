#!/usr/bin/env/python
from setuptools import setup

setup(
    name='ckanext-bpatheme',
    version='0.67.0',
    description='',
    license='AGPL3',
    author='CCG, Murdoch University',
    author_email='tech@ccg.murdoch.edu.au',
    url='https://github.com/muccg/ckanext-bpatheme/',
    namespace_packages=['ckanext'],
    packages=['ckanext.bpatheme'],
    zip_safe=False,
    include_package_data=True,
    package_dir={'ckanext.bpatheme': 'ckanext/bpatheme'},
    package_data={'ckanext.bpatheme': ['*.json', 'templates/*.html', 'templates/*/*.html', 'templates/*/*/*.html', 'static/*.css', 'static/*.png', 'static/*.jpg', 'static/*.css', 'static/*.ico']},
    entry_points = """
        [ckan.plugins]
        bpa_theme = ckanext.bpatheme.plugins:CustomTheme
    """
)
