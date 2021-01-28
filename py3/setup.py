try: from setuptools import setup
except ImportError: from distutils.core import setup

import sys

py_version = sys.version_info[0]

if not py_version==(3):	raise RuntimeError('Python 3 is required!	')

dist=setup(name="OCFit",
      version="0.1.5",
      description="Fitting O-C diagrams",
      author="Pavol Gajdos",
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3",
          "Topic :: Scientific/Engineering :: Astronomy"],
      url='https://github.com/pavolgaj/OCFit',
      install_requires=['numpy>=1.10.2','matplotlib>=1.5.0','PyAstronomy>=0.9.0'],
      extras_require={'MonteCarlo Fitting':  ['pymc>=2.3.6']},
      py_modules=["OCFit/__init__","OCFit/OC_class","OCFit/info_mc","OCFit/info_ga","OCFit/ga"]
)
