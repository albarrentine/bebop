try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='bebop',
    version='0.0.1dev',
    description='Lightweight Solr object mapping and schema generation without all the XML',
    author='Al Barrentine',
    url='http://www.github.com/thatdatabaseguy/bebop',
    install_requires=[
        "pysolr",
        "lxml>=2.2.3",
    ],
    packages=['bebop'],
    
    )
