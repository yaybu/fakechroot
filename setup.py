from setuptools import setup, find_packages
import os

version = '0.2.0'

setup(name='fakechroot',
      version=version,
      url="http://github.com/yaybu/fakechroot",
      description="A fixture for using a fakechroot environment in your tests",
      long_description=open("README.rst").read(),
      author="John Carr",
      author_email="john.carr@isotoma.com",
      license="Apache Software License",
      classifiers = [
          "Intended Audience :: Developers",
          "Operating System :: POSIX",
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: Implementation :: PyPy",
      ],
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'six',
      ],
      extras_require = {
          'test': ['unittest2', 'discover'],
          },
      )
