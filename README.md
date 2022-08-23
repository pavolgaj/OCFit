# OCFit
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2547766.svg)](https://doi.org/10.5281/zenodo.2547766)
[![DOI](https://img.shields.io/badge/ascl-1901.002-blue.svg?colorB=262255)](http://ascl.net/1901.002)
[![PyPI version](https://img.shields.io/pypi/v/ocfit.svg?colorB=green&style=flat)](https://pypi.org/project/OCFit/)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/b3fe9f8e7f1d438ca0e9a11e9c951a20)](https://www.codacy.com/gh/pavolgaj/OCFit/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=pavolgaj/OCFit&amp;utm_campaign=Badge_Grade)

![](https://img.shields.io/github/languages/top/pavolgaj/ocfit.svg?style=flat)
![](https://img.shields.io/github/downloads/pavolgaj/ocfit/total.svg?label=GitHub&nbsp;downloads&style=flat)
![](https://img.shields.io/pypi/dm/ocfit.svg?label=PyPI&nbsp;downloads&style=flat)
![](https://img.shields.io/github/issues/pavolgaj/ocfit.svg?style=flat)
![](https://img.shields.io/github/issues-closed/pavolgaj/ocfit.svg?style=flat)


:warning:__WARNING: This is a copy of the package OCFit which used `pymc` package (v2.3.8). The development of this version was stopped! The new version uses the `emcee` package instead of `pymc`.__

:warning:__IMPORTANT NOTE: E-mail address given in a paper is not working! If you want to contact me, use my new address `pavol (dot) gajdos (at) upjs (dot) sk` or create new issue here on GitHub.__

Python package OCFit includes 4 classes for analysis and fitting of O-C diagrams of Eclipsing binaries

In a case of using this package for scientific purposes, please, cite our paper [Gajdoš &
Parimucha (2019)](https://ui.adsabs.harvard.edu/abs/2019OEJV..197...71G/abstract) in [OEJV](http://var.astro.cz/oejv/issues/oejv0197.pdf) where you can also find more detail description about fitting functions
and used models.

For install it, download/clone this repository or download suitable binary file from releases.

### Requirements
* numpy
* matplotlib
* PyAstronomy
* pymc (v2.3.8; recommended)

Installation is possible from source code or using build installation binary file (only for OS
Windows). The following procedure is only for installation from the source code. Extract
files and go to new-created folder. Running script ``setup.py`` the installation will be done:

``python setup.py install``

Or using pip:

``pip install OCFit==0.1.4``
