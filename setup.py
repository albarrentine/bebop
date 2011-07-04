from distutils.core import setup

setup(
    name='bebop',
    version='0.0.2',
    description='Solr object mapping and schema generation without all the XML',
    author='Al Barrentine',
    url='http://www.github.com/thatdatabaseguy/bebop',
    install_requires=[
        "pysolr",
        "lxml>=2.2.3",
    ],
    packages=['bebop'],
    
    )
