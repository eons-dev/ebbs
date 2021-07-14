# eons Basic Build System

![build](https://github.com/eons-dev/bin_ebbs/actions/workflows/python-package.yml/badge.svg)

This project derives from [eons](https://github.com/eons-dev/lib_eons) to improve ease-of-hacking ;)

## Supported Languages

Currently supporting:
* C++
* Python (yes, this repository is circularly dependent on itself)

## Prerequisites
* python >= 3.6.3
* eons >= 0.1.0

### Prerequisites for C++
* cmake >= 3.1.1
* make >= whatever
* g++ or equivalent for cmake

## Installation
`pip install ebbs`

## Usage

ebbs assumes that your project is named in accordance with [eons naming conventions](https://eons.dev/convention/naming/) as well as [eons directory conventions](https://eons.dev/convention/uri-names/)

This usually means your project has the name of `bin_my-project`, `lib_my-project`, `test_my-project`, etc.

Specific usage is language specific

### C++

Instead of writing and managing cmake files throughout your directory tree, you can use `ebbs -l cpp` from a `build` folder and all .h and .cpp files in your source tree will be discovered and added to a CMakeLists.txt.

Supported project types:
* bin
* lib
* test (alias for bin)

### Python

Do you hate having empty `__init__.py` files and other nonsense strewn about your project? This fixes that. Somehow.  
To build a python library or binary, go to the root of your project and run `ebbs -l py -d build`.  
This will copy all `*.py` files out of `src` and compile them into a single `PROJECT_NAME.py` in a dependency-aware fashion.  
It will also copy all files and directories from `inc` and add them to the build folder.  
Then, it creates python project files, like `__main__.py` and `__init__.py`s.  
Lastly, it invokes python's build package and pip to build and install your code. This will fail if the necessary dependencies are not installed.

Supported project types:
* bin
* lib