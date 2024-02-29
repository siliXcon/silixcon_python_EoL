# silixcon_python_EoL

Welcome to the silixcon_python_EoL documentation! This repository provides an EXAMPLE of production scripts built around siliXcon SWTools for seamless integration and control of siliXcon devices using Python.

## A little background of the scripts:

The scripts are a small part of the scripts used in siliXcon production. The script was modified to work without other proprietary tools from siliXcon manufacturing.

This means that the scripts are not used by siliXcon, because siliXcon has an internal copy. Their purpose is an example, that you can automate things using Python and SWTools. If you want to use the scripts as they are, you may need some work on them. The scripts are not maintained, but you can use them as a starting point for your own scripts.

## Getting Started

Connect siliXcon controller and run the example.py script provided in this repository. This script demonstrates the usage of various functions and showcases the capabilities of the production scripts.

```bash
python example.py
```

## Description

The core components of this repository are the swtools.py and yos_device.py scripts. These scripts serve as wrappers around the siliXcon SWTools, enabling you to utilize Python functions for efficient control and interaction with siliXcon devices.

## Include in PYTHONPATH:

For easy accessibility from any location, consider adding the path to the `swtools.py` and `yos_device.py` scripts to the PYTHONPATH environmental variable.
