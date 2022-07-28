# eons Basic Build System

![build](https://github.com/eons-dev/bin_ebbs/actions/workflows/python-package.yml/badge.svg)

EBBS (or ebbs) is a framework for designing modular build pipelines for any language and system. Builders are python scripts that are downloaded and run on the fly with configuration provided by a "build.json" file, environment variables, and command line arguments!

Here, at eons, we have found building and distributing code to be too hard and far too disparate between languages. Thus, we designed ebbs to make packaging and distributing code consistent, no matter what language you're working with and no matter what you want to do with your code.

Want to compile C++ in a containerized environment then publish that code as an image back to Docker? How about publish your python code to PyPi or even just build a simple Wordpress plugin? No matter how intricate or big your project becomes, you'll be able to rely on ebbs to automate every step of your build process. It's just python. That's literally it.

With ebbs, there will be no more:
 * having to write lengthy config files for every project.
 * having to change your code to fit your build system.
 * having to learn a new way to package code for every language.

Instead, you write your code the way you want and your ebbs build system will put the pieces together for you.
Ebbs has been written in adherence to the [eons naming conventions](https://eons.llc/convention/naming/) and [eons directory conventions](https://eons.llc/convention/uri-names/). However, we do try to make overriding these conventions as easy as possible so that you don't have to change your existing code to use our systems.

 For example, if you use "include" instead of the eons-preferred "inc", you can tell ebbs:
```json
"copy" : [
  {"../include" : "inc"}
]
```
In the same fashion, you can bypass the eons directory scheme ("bin_my-project", "lib_my-project", "img_my-project", etc.) by specifying `"name" : "my-project"` and `"type" : "bin"` or whatever you'd like.

If you find ebbs to be getting in the way or overly challenging, let us know! Seriously, building code should be easy and we're always happy to know how we can improve. Feel free to open issues or just email us at support@eons.llc.

## Installation
`pip install ebbs`

## Usage

When running ebbs, the builder you select will pull its configuration values from:
 1. the command line (e.g. in case you want to override anything)
 2. a "build.json" in the provided build folder (which can be specified via `--config`)
 3. the system environment (e.g. for keeping passwords out of repo-files and commands)

You can specify the builder you'd like in one of 2 ways:
 1. the `-b` argument to ebbs.
 2. `"build" : "SOMETHING"` in the build.json

You can specify the path to your project similarly:
 1. just type the folder path after `ebbs` on the command line
 2. `"path" : "/path/to/my/project"` in the build.json

Lastly, you can specify a build folder (i.e. a folder to create within your project for all build output) with:
 1. `-i` on the cli; the default is "build" (e.g. "/path/to/my/project/build")
 2. `"build_in" : "BUILD_FOLDER"` in the build.json

You can also specify any number of other arguments in any of the command line, build.json, and system environments.
For example, `export pypi_username="__token__"` would make `this.Fetch('pypi_username)` in the "py" Builder return `__token__`, assuming you don't set `"pypi_username" : "something else"` in the build.json nor specify `--pypi-username "something else"` on the command line.

As always, use `ebbs --help` for help ;)

**IMPORTANT NOTE: Most ebbs Builders will DELETE the build folder you pass to them.**

This is done so that previous builds cannot create stale data which influence future builds. However, if you mess up and call, say, `ebbs -b cpp ./src` instead of `ebbs -b cpp ./build`, you will lose your "src" folder. Please use this tool responsibly and read up on what each Builder does.
To make things easy, you can search for `clearBuildPath`. If you see `this.clearBuildPath = False` it should be okay to use that Builder with any directory (such is the case for the Publish Builder, which zips the contents of any directory and uploads them to an online repository).

### Where Are These "Builders"?

All Builders are searched for in the local file system from where ebbs was called within the following folders:
```python
"./eons" #per the eons.Executor.defaultRepoDirectory
```
NOTE: Collectively, these folders, within your project folder, are called the "workspace"
For example, `me@mine:~/workspace$ ebbs` would cause the workspace to be "~/workspace" and ebbs would look in "~/workspace/eons/" for any Builders.

If the build you specified is not found within one of those directories, ebbs will try to download it from the remote repository with a name of `build_{builder}`. The downloaded build script will be saved to whatever directory you set in `--repo-store` (default "./eons/").

Unfortunately, python class names cannot have dashes ("-") in them. Instead, a series of underscores ("_") is often used instead. While this deviates from the eons naming schema, it should still be intelligible for short names. You are, of course, welcome to use whatever naming scheme you would like instead!

### Side Note on Build Path and Languages

The workspace is dependent on where ebbs is invoked. The rootPath & Builder variables are dependent on the directory above the specified buildPath. While this prevents you from using "/my/build/path/ebbs/my_build.py", it does allow you to create a single workspace for all your projects.

For example, if you have a "git" and a "workspace" folder in your home directory and you want to use your custom Builder, "my_build" on all the projects in the git folder, instead of copying my_build to every project's workspace, you could simply cd to ~/workspace and call ebbs with the appropriate build directory.
Something like: `me@mine:~/workspace$ ebbs -b my_build ~/git/bin_my-cpp-project/build/; ebbs -b my_build ~/git/lib_my-python-bibrary/generated/`.
While that should work, this is easier but hasn't been tested:`me@mine:~/workspace$ ebbs -b my_build ~/git/**/generated/`

Something like:
```
home/
├─ git/
│  ├─ bin_my-cpp-project/
│  ├─ lib_my-python-bibrary/
├─ workspace/
│  ├─ build/
│  │  ├─ my_build.py
```

### Repository

Online repository settings can be specified with:
```
--repo-store (default = ./eons/)
--repo-url (default = https://api.infrastructure.tech/v1/package)
--repo-username
--repo-password
```

NOTE: you do not need to supply any repo credentials or other settings in order to download packages from the public repository.

For more info on the repo integration, see [the eons library](https://github.com/eons-dev/lib_eons#online-repository)

It is also worth noting that the online repository system is handled upstream (and downstream, for Publish) of ebbs.

By default, ebbs will use the [infrastructure.tech](https://infrastructure.tech) package repository. See the [Infrastructure web server](https://github.com/infrastructure-tech/srv_infrastructure) for more info.

**IMPORTANT CAVEAT FOR ONLINE PACKAGES:** the package name must be preceded by "build_" to be found by ebbs.  
For example, if you want to use `-b my_build` from the repository, ebbs will attempt to download "build_my_build". The package zip is then downloaded, extracted, registered, and instantiated.  
All packages are .zip files.

### Example Build Scripts:

* [Publish](https://github.com/eons-dev/build_publish) <- this one makes other Builders available online.
* [Python](https://github.com/eons-dev/build_py)
* [C++](https://github.com/eons-dev/build_cpp)
* [Docker](https://github.com/eons-dev/build_docker)

### Cascading Builds

As with any good build system, you aren't limited to just one step. With ebbs, you can specify "next" in your build.json (see below), which will execute a series of Builders after the initial.

Here's an example build.json that builds a C++ project then pushes it to Dockerhub (taken from the [Infrastructure web server](https://github.com/infrastructure-tech/srv_infrastructure)):
```json
{
  "clear_build_path" : true,
  "next": [
    {
      "build" : "in_container",
      "config" : {
        "image" : "eons/img_dev-webserver",
        "copy_env" : [
          "docker_username",
          "docker_password"
        ],
        "next" : [
          {
            "build" : "cpp",
            "build_in" : "build",
            "copy" : [
              {"../../inc/" : "inc/"},
              {"../../src/" : "src/"}
            ],
            "config" : {
              "file_name" : "entrypoint",
              "cpp_version" : 17,
              "libs_shared": [
                "restbed",
                "cpr"
              ],
              "next" : [
                {
                  "build": "docker",
                  "path" : "srv_infrastructure",
                  "copy" : [
                    {"out/" : "src/"}
                  ],
                  "config" : {
                    "base_image" : "eons/img_webserver",
                    "image_name" : "eons/srv_infrastructure",
                    "image_os" : "debian",
                    "entrypoint" : "/usr/local/bin/entrypoint",
                    "also" : [
                      "EXPOSE 80"
                    ]
                  }
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```
This script can be invoked with just `ebbs` (assuming the appropriate docker credentials are stored in your environment).

## Design

### Where Variables Come From and the build.json

Ebbs is intended to keep your build process separate from your code. With that said, it can be useful to specify some project-wide settings and build configurations.
In order to accommodate more complex builds, ebbs supports the use of a build.json file in the root directory of your project (one directory above the buildPath you provide). Note that there isn't any real reason you can't move the build.json or even write an ebbs script to generate build.json and then call ebbs with it ;)

Each Builder will record which arguments it needs and wants in order to function. Those arguments are then populated from:
1. The system environment
2. The configuration file supplied to ebbs (e.g. build.json in the root directory)
3. The local configuration file (e.g. build.json in the build directory)
4. The command line

Where, the command line overrides anything specified in the environment and config files.

### I Want One!

Ebbs builds packages or whatever with `ebbs.Builders`, which extend the this-registering `eons.UserFunctor`. This means you can write your own build scripts and place them in a "workspace" (see above) which can then be shared with colleagues, etc. For example, you could create "my_build.py", containing something like:
```python
import logging
from ebbs import Builder

class my_build(Builder):
    def __init__(this, name="My Build"):
        super().__init__(name)
        
        # delete whatever dir was provided to this, so we can start fresh.
        this.clearBuildPath = True
        
        this.supportedProjectTypes = [] #all
        #or
        # this.supportedProjectTypes.append("lib")
        # this.supportedProjectTypes.append("bin")
        # this.supportedProjectTypes.append("test")
        
        #this.requiredKWArgs will cause an error to be thrown prior to execution (i.e. .*Build methods) iff they are not found in the system environment, build.json, nor command line.
        this.requiredKWArgs.append("my_required_arg")
        
        #this.my_optional_arg will be "some default value" unless the user overrides it from the command line or build.json file.
        this.optionalKWArgs["my_optional_arg"] = "some default value"
        
    #Check if the output of all your this.RunCommand() and whatever other calls did what you expected.
    #The "next" step will only be executed if this step succeeded.
    def DidBuildSucceed(this):
        return True; #yeah, why not?

    def PreBuild(this):
        logging.info(f"Got {this.my_required_arg} and {this.my_optional_arg}")
        
    #Required Builder method. See that class for details.
    def Build(this):
        #DO STUFF!
```
That file can then go in a "./ebbs/" or "./eons/" directory, perhaps within your project repository or on infrastructure.tech!
ebbs can then be invoked with something like: `ebbs -b my_build ./build --my_required_arg my-value`, which will run your Build method from "./build" (NOTE: "build" does not work with the "py" Builder, use "generated" or literally anything else instead).

Also note the "--" preceding "--my_required_arg", which evaluates to just "my_required_arg" (without the "--") once in the Builder. This is done for convenience of both command line syntax and python code.

You could also do something like:
```shell
cat << EOF > ./build.json
{
  "my_required_arg" : "my-value",
  "my_optional_arg" : [
    "some",
    "other",
    "value",
    "that",
    "you",
    "don't",
    "want",
    "to",
    "type"
  ]
}
EOF

ebbs -b my_build ./build
```
Here, the build.json file will be automatically read in, removing the need to specify the args for your build.

If you'd like to take this a step further, you can remove the need for `-b my_build` by specifying it under an empty builder in the build.json, like so:

```shell
cat << EOF > ./build.json
{
  "next": [
    {
      "build" : "my_build",
      "build_in" : "build",
      "copy" : [
        {"../src/" : "src/"},
        {"../inc/" : "inc/"},
        {"../test/" : "test/"}
      ],
      "config" : {
        "my_required_arg" : "my-value",
        "my_optional_arg" : [
          "some",
          "other",
          "value",
          "that",
          "you",
          "don't",
          "want",
          "to",
          "type"
        ]
      }
    }
  ]
}
EOF

ebbs #no args needed!
```

Regarding `this.clearBuildPath`, as mentioned above, it is important to not call ebbs on the wrong directory. If your Builder does not need a fresh build path, set `this.clearBuildPath = False`.
With that said, most compilation, packaging, etc. can be broken by stale data from past builds, so make sure to set `this.clearBuildPath = True` if you need to.

You may also have noticed the combination of camelCase and snake_case. This is used to specify builtInValues from user_provided_values. This convention may change with a future release (let us know what you think!).

For `supportedProjectTypes`, the `Builder` class will split the folder containing the buildPath (i.e. the `rootPath`) on underscores ("_"), storing the first value as `this.projectType` and the second as `this.projectName`. The `projectType` is checked against the used build's `supportedProjectTypes`. If no match is found, the build is aborted prior to executing the build. If you would like your Builder to work with all project types (and thus ignore that whole naming nonsense), set `this.supportedProjectTypes = []`, where none (i.e. `[]`, not actually `None`) means "all".


You'll also get the following paths variables populated by default:
```python
this.buildPath = path #The one specified on the cli
this.rootPath = os.path.abspath(os.path.join(this.buildPath, "../"))
this.srcPath = os.path.abspath(os.path.join(this.buildPath, "../src"))
this.incPath = os.path.abspath(os.path.join(this.buildPath, "../inc"))
this.depPath = os.path.abspath(os.path.join(this.buildPath, "../dep"))
this.libPath = os.path.abspath(os.path.join(this.buildPath, "../lib"))
this.libPath = os.path.abspath(os.path.join(this.buildPath, "../bin"))
this.testPath = os.path.abspath(os.path.join(this.buildPath, "../test"))
```
As well as the following methods:  
(See Builder.py for more details)
```python
def CreateFile(this, file, mode="w+")
def RunCommand(this, command)
```

When a `Builder` is executed, the following are called in order:  
(kwargs is the same for all)
```python
this.ValidateArgs(**kwargs) # <- not recommended to override.
this.PreCall(**kwargs) # <- virtual (ok to override)
#Builder sets the above mentioned variables here
this.PreBuild(**kwargs) # <- virtual (ok to override)
#Supported project types are checked here
this.Build() # <- abstract method for you  (MUST override)
this.PostBuild(**kwargs) # <- virtual (ok to override)
if (this.DidBuildSucceed()):
    this.BuildNext()
this.PostCall(**kwargs) # <- virtual (ok to override)
```
