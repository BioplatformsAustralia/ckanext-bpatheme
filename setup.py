#!/usr/bin/env/python
from setuptools import setup

install_requires = ["pandas>=1.4.3"]

setup(
    name="ckanext-bpatheme",
    version="3.4.8",
    description="CKAN Theme for the Bioplatforms Australia Data Portal",
    license="AGPL3",
    author="Bioplatforms Australia",
    author_email="help@bioplatforms.com",
    url="https://github.com/BioplatformsAustralia/ckanext-bpatheme",
    namespace_packages=["ckanext"],
    packages=["ckanext.bpatheme"],
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,
    package_dir={"ckanext.bpatheme": "ckanext/bpatheme"},
    package_data={
        "ckanext.bpatheme": [
            "*.json",
            "assets/*.js",
            "assets/*.yml",
            "assets/*.config",
            "assets/scripts/*.js",
            "assets/styles/*.css",
            "assets/styles/*.scss",
            "templates/*.html",
            "templates/*/*.html",
            "templates/*/*/*.html",
            "templates/*/*/*/*.html",
            "templates/*.txt",
            "static/datacats/*.png",
            "static/fonts/arial/*.eot",
            "static/fonts/arial/*.svg",
            "static/fonts/arial/*.woff",
            "static/fonts/arial/*.woff2",
            "static/fonts/arial/*.ttf",
            "static/*.png",
            "static/*.ico",
            "static/bootstraptable/*.js",
            "static/bootstraptable/*.css",
            "static/*.webp",
        ]
    },
    entry_points="""
        [ckan.plugins]
        bpa_theme = ckanext.bpatheme.plugins:CustomTheme
    """,
)
