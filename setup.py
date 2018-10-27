import os
from setuptools import (
    find_packages,
    setup)


def contents(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename)) as fp:
        return fp.read()


setup(
    name='SmallVille',
    version='0.1.0',
    author='Elmer de Looff',
    author_email='elmer.delooff@gmail.com',
    description='SQLAlchemy models to create and simulate a small community',
    long_description=contents('README.rst'),
    keywords='sqlalchemy sql data',
    license='BSD',
    url='https://github.com/edelooff/smallville',
    packages=find_packages(),
    install_requires=[
        'sqlalchemy',
        'psycopg2-binary'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Database'])
