# EBBS

eons Basic Build System

This project derives from [esam](https://github.com/eons-dev/esam) to improve ease-of-hacking ;)

## Supported Languages

Currently, only C++ is supported

## Prerequisites
* python >= 3.6.3
* esam >= 1.0.0

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

Instead of writing and managing cmake files throughout your directory tree, you can use `ebbs --gen-cmake` from a `build` folder and all .h and .cpp files in 