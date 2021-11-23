# eons Basic Build System

![build](https://github.com/eons-dev/bin_ebbs/actions/workflows/python-package.yml/badge.svg)

This project derives from [eons](https://github.com/eons-dev/lib_eons) for easy hacking ;)

## Installation
`pip install ebbs`

## Usage

ebbs assumes that your project is named in accordance with [eons naming conventions](https://eons.dev/convention/naming/) as well as [eons directory conventions](https://eons.dev/convention/uri-names/)

This usually means your project has the name of `bin_my-project`, `lib_my-project`, `test_my-project`, etc.

You must invoke this tool from the root directory of your project. For `{project-type}_{project-name}/build/path`, you would use `ebbs -l {language} build/path`, which would tell ebbs to build `{project-name}` as a `{project-type}` with the `{language}` builder.

Use `ebbs --help` for help ;)

Unfortunately, python class names cannot have dashes ("-") in them. Instead, a series of underscores ("_") is often used instead. While this deviates from the eons naming schema, it should still be intelligible for short names. You are, of course, welcome to use whatever naming schemes you would like instead!

### Repository

Online repository credentials can be specified with:
```
--repo-store
--repo-url
--repo-username
--repo-password
```

These credentials, when used, are passed to the language Builder. This is done primarily for publishing. Because these creds are not pulled from environment variables and are visible on the command line, it is advisable to use app tokens with short expirations. This will be addressed in a future release.

Publishing requires the following additional arguments:
```
--version
```
and, optionally:
```
--visibility
```
More information below on repository usage and publishing.

### C++

Instead of writing and managing cmake files throughout your directory tree, you can use `ebbs -l cpp` from a `build` folder and all .h and .cpp files in your source tree will be discovered and added to a CMakeLists.txt, which is then built with cmake and make, so you get the compiled product you want.

Supported project types:
* lib
* bin
* test (alias for bin)

Prerequisites:
* cmake >= 3.1.1
* make >= whatever
* g++ or equivalent

Currently lacking support for auto-discovered tool chains and build targets - only compiles for the system it is run on.

### Python

Do you hate having empty `__init__.py` files and other nonsense strewn about your project? This fixes that. Somehow.  
To build a python library or binary, go to the root of your project and run `ebbs -l py generated`.  
This will copy all `*.py` files out of `src` and compile them into a single `PROJECT_NAME.py` in a dependency-aware fashion.  
It will also copy all files and directories from `inc` and add them to the build folder.  
Then, it creates python project files, like `__main__.py` and `__init__.py`s.  
Lastly, it invokes python's build package and pip to build and install your code. This will fail if the necessary dependencies are not installed.

IMPORTANT: DO NOT USE THIS IN A `build` FOLDER!  
Building packages from a folder named "build" with `python -m build` (and setuptools?) will result in an empty package as all `*.py` files in that directory are ignored.
Someone please fix this...

Supported project types:
* bin
* lib

Prerequisites:
* `build` python package
* valid setup and pyproject.toml files  

See [how to package python projects](https://packaging.python.org/tutorials/packaging-projects/) for information on required files.  
NOTE: Setup files are not created for you, since there is some variability in what you might want.

## Design

Ebbs builds packages or whatever with `Builders`, which extend the self-registering `eons.UserFunctor`. This means you can write your own build scripts and place them in a "workspace" that can then be shared with colleagues, etc. For example, you could create "my_language.py", containing something like:
```python
from ebbs import Builder

class my_language(Builder):
    def __init__(self, name="My Language"):
        super().__init__(name)
        
        self.supportedProjectTypes = [] #all
        #or
        # self.supportedProjectTypes.append("lib")
        # self.supportedProjectTypes.append("bin")
        # self.supportedProjectTypes.append("test")
        
        #-- is used for consistency and highly recommended.
        #self.requiredKWArgs will cause an error to be thrown prior to execution (i.e. .*Build methods)
        self.requiredKWArgs.append("--my-cli-option")
        
    #Use --my-cli-option
    def PreBuild(self, **kwargs):
        self.my_option = kwargs.get("--my-cli-option")
        
    #Required Builder method. See that class for details.
    def Build(self):
        #DO STUFF!
```
That file can then go in a "./ebbs/inc/language" directory, perhaps within your project repository.  
ebbs can then be invoked with something like: `ebbs -l my_language ./generated --my-cli-option my-value`, which will run your Build method from "./generated".

The `Builder` class will split the folder containing the buildPath (e.g. "./generated) on underscores ("_"), storing the first value as `self.projectType` and the second as `self.projectName`. The `projectType` is checked against the used language's `supportedProjectTypes`. If no match if found, the build is aborted prior to executing the language.

`Builder` also provides the following path variables by default:
```python
        self.buildPath = path #The one specified on the cli
        self.rootPath = os.path.abspath(os.path.join(self.buildPath, "../"))
        self.srcPath = os.path.abspath(os.path.join(self.buildPath, "../src"))
        self.incPath = os.path.abspath(os.path.join(self.buildPath, "../inc"))
        self.depPath = os.path.abspath(os.path.join(self.buildPath, "../dep"))
        self.libPath = os.path.abspath(os.path.join(self.buildPath, "../lib"))
```
As well as the following methods:  
(See Builder.py for more details)
```python
def CreateFile(self, file, mode="w+")
def RunCommand(self, command)
```

When a `Builder` is executed, the following are called in order:  
(kwargs is the same for all)
```python
self.ValidateArgs(**kwargs) # <- not recommended to override.
self.PreCall(**kwargs) # <- virtual
#Builder sets the above mentioned variables here
self.PreBuild(**kwargs) # <- virtual
#Supported project types are checked here
self.Build() # <- abstract method for you 
self.PostBuild(**kwargs) # <- virtual
self.PostCall(**kwargs) # <- virtual
```

## Supported Languages

Out of the box, you can build:
* C++
* Python (yes, this repository is circularly dependent on itself. That's how you know it's stable!)

You can also "publish" packages to an online repository with `-l publish`. This is just another `Builder` and can be extended or substituted as with any other "language".  
When publishing your code, you can use `--visibility 'private'` or `--visibility 'publish'`. Anything other than `private` or `publish` will fail, unless you build your own repository api. 

Ebbs will try to download a language package if the one specified is not found in your workspace.
You may add credentials and even provide your own repo url for searching. If credentials are supplied, private packages will be searched before public ones. The same credentials (or those with write access) are required for publishing.

By default, ebbs will use the [infrastructure.tech](https://infrastructure.tech) package repository. See the [Infrastructure API docs](https://github.com/infrastructure-tech/api) for more info.

**IMPORTANT CAVEAT FOR ONLINE PACKAGES:** the package name must be preceded by "build_" to be found by ebbs.  
For example, if you want to use `-l my_language` from the repository, ebbs will attempt to download "build_my_language". The package zip is then downloaded, extracted, registered, and instantiated.  
All packages are .zip files.
