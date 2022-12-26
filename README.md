# Eons Basic Build System

EBBS (or ebbs) is a framework for designing modular build pipelines for any language and system. Builders are python scripts that are downloaded and run on the fly with configuration provided by json config files, environment variables, and command line arguments!

Here, at eons, we have found building and distributing code to be too hard and far too disparate between languages. Thus, we designed ebbs to make packaging and distributing code consistent. No matter what language you're working with and no matter what you want to do with your code.

Want to compile C++ in a containerized environment then publish that code as an image back to Docker? How about publish your python code to PyPI or even just build a simple Wordpress plugin? No matter how intricate or big your project becomes, you'll be able to rely on ebbs to automate every step of your build process. It's just python. That's literally it.

With ebbs, there will be no more:
 * having to learn a new way to package code for every language.
 * having to change your code to fit your build system.
 * having to specify unnecessary configuration for every project.

Instead, you write your code the way you want and your ebbs build system will put the pieces together for you.
Ebbs has been written in adherence to the [eons naming conventions](https://eons.llc/convention/naming/) and [eons directory conventions](https://eons.llc/convention/uri-names/). However, we do try to make overriding these conventions as easy as possible so that you don't have to change your existing code to use our systems.

 For example, if you use "include" instead of the eons-preferred "inc", you can tell ebbs:
```json
"copy" : [
  {"../include" : "inc"}
]
```
In the same fashion, you can bypass the eons directory scheme ("my_project.exe", "my_project.lib", "my_project.img", etc.) by specifying `"name" : "my_project"` and `"type" : "exe"` or whatever you'd like.

If you find ebbs to be getting in the way or overly challenging, let us know! Seriously, building code should be easy and we're always happy to know how we can improve. Feel free to open issues or just email us at support@eons.llc.

## Installation
`pip install ebbs`

## Usage

Ebbs must be invoked from the directory you wish to build from.
For example, a well-designed project should allow you compile it locally by:
```shell
cd build
ebbs
```

Per (eons)[https://github.com/eons-dev/eons.lib], ebbs supports:
* `-v` or `--verbose` (count, i.e `-vv` = 2) or `--verbosity #`, where # is some number, or the `verbosity` environment or config value: will show more information and increase the logging level, e.g. print debug messages (3 for debug; 2 for info).
* `--config` or `-c` (string): the path to a json config file from which other values may be retrieved.
* `--no-repo` or the `no_repo` environment or config value (bool, i.e. 'True', 'true', etc.): whether or not to enable reaching out to online servers for code (see Dynamic Functionality, below).
* `--log-file` or the `log_file` environment or config value (string; supports formatting, e.g. '/var/log/eons/{this.name}.log'): optional value for logging to a file in addition to stderr.

As always, use `ebbs --help` for help ;)

### Configuration

Ebbs is intended to keep your build process separate from your code. With that said, it can be useful to specify some project-wide settings and build configurations.
Note that there isn't any real reason you can't move the build.json or even write an ebbs script to generate build.json and then call ebbs with it ;)

When running ebbs, the builder you select will pull its configuration values from the following external sources:
 1. the command line (e.g. in case you want to override anything)
 2. a "build.json" in the provided build folder (which can be specified via `--config`)
 3. a json file provided to `ebbs`.
 4. the system environment (e.g. for keeping passwords out of repo-files and commands)
Any existing member variables will override these external values.

You can manually specify the builder you'd like in one of 2 ways:
 1. the `-b` argument to ebbs.
 2. `"build" : "SOMETHING"` in the build.json

Lastly, you can specify a build folder (i.e. a folder to create within your project for all build output) with:
 1. `-i` on the cli; the default is "build" (e.g. "/path/to/my/project/build")
 2. `"build_in" : "BUILD_FOLDER"` in the build.json

You can also specify any number of other arguments in any of the command line, build.json, and system environments.
For example, `export pypi_username="__token__"` would make `this.Fetch('pypi_username)` in the "py" Builder return `__token__`, assuming you don't set `"pypi_username" : "something else"` in the build.json nor specify `--pypi-username "something else"` on the command line.

**IMPORTANT NOTE: Most ebbs Builders will DELETE the build folder you pass to them.**

This is done so that previous builds cannot create stale data which influence future builds. However, if you mess up and call, say, `ebbs -b cpp` from `./src` instead of from `./build`, you could lose your "src" folder. Please use this tool responsibly and read up on what each Builder does.
To make things easy, you can search for `clearBuildPath` in the python file and `clear_build_path` in the config files. If you see `this.clearBuildPath = False` it should be okay to use that Builder with any directory (such is the case for the Publish Builder, which zips the contents of any directory and uploads them to an online repository). Conversely, take note of where `"clear_build_path": true` is set.

### Where Are These "Builders"?

All Builders are searched for in the local file system from where ebbs was called within the following folders:
```python
"./eons" #per the eons.Executor.defaultRepoDirectory
```

If the build you specified is not found within one of those directories, ebbs will try to download it from the remote repository with a name of `{builder}.build`. The downloaded build script will be saved to whatever directory you set in `--repo-store` (default "./eons/").

Unfortunately, python class names cannot have dashes ("-") in them. Instead, a series of underscores (`_`) is often used instead. While this deviates from the eons naming schema, it should still be intelligible for short names. You are, of course, welcome to use whatever naming scheme you would like instead!

### The Build Path

As mentioned, ebbs depends on the directory it is invoked from. The `rootPath` provided to each Builder will be this directory. The `buildPath` is specified relative to the `rootPath`. If you would like to use a single folder for all Builders, please set the `repo_store` environment variable with an absolute path.

For example, if you have a "git" and a "workspace" folder in your home directory and you want to use your custom Builder, "my_build" on all the projects in the git folder, instead of copying my_build to every project's workspace, you could simply `export repo_store="~/workspace"` and call ebbs from the appropriate build directory for each project.
Something like: `me@mine:~/git/my_cpp_project.exe/build$ ebbs -b my_build`. NOTE: if the build.json file `~/git/my_cpp_project.exe/build/build.json` exists, it will affect the behavior of `my_build` and potentially even effect other Builders. To ensure no side-effects are generated from project build configurations, you should create an empty folder to invoke your custom build process from (e.g `local/`).

Your home folder would then look something like:
```
home/
├─ git/
│  ├─ my_cpp_project.exe/
├─ workspace/
│  ├─ my_build.py
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

By default, ebbs will use the [infrastructure.tech](https://infrastructure.tech) package repository. See the [Infrastructure web server](https://github.com/infrastructure-tech/infrastructure.srv) for more info.

**IMPORTANT CAVEAT FOR ONLINE PACKAGES:** the package name must be suffixed with the "build" extension to be found by ebbs.  
For example, if you want to use `-b my_build` from the repository, ebbs will attempt to download "my_build.build". The package zip (my_build.build.zip) is then downloaded, extracted, registered, and instantiated.  
All packages are .zip files.

### Example Build Scripts:

* [Python](https://github.com/eons-dev/py.build)
* [C++](https://github.com/eons-dev/cpp.build)
* [Docker](https://github.com/eons-dev/docker.build)
* [Publish](https://github.com/eons-dev/publish.build) <- this one makes other Builders available online.
* [In Container](https://github.com/eons-dev/in_container.build) <- this one moves the remaining build process into a docker container.
* [Arbitrary](https://github.com/eons-dev/arbitrary.build) <- this one just runs commands.
* [Proxy](https://github.com/eons-dev/proxy.build) <- this one loads another json config file.
* [Test](https://github.com/eons-dev/test.build) <- this one runs commands and validates the outputs.

### Cascading Builds

As with any good build system, you aren't limited to just one step or even one file. With ebbs, you can specify "next" in your build.json (see below), which will execute a series of Builders after the initial.

Here's an example build.json that builds a C++ project then pushes it to Dockerhub (taken from the [Infrastructure web server](https://github.com/infrastructure-tech/infrastructure.srv)):
```json
{
  "clear_build_path" : true,
  "next": [
	{
	  "build" : "in_container",
	  "config" : {
		"image" : "eons/dev-webserver.img",
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
                  "path" : "infrastructure.srv",
                  "copy" : [
                    {"out/" : "src/"}
                  ],
                  "config" : {
                    "base_image" : "eons/webserver.img",
                    "image_name" : "eons/infrastructure.srv",
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
This script can be invoked with just `ebbs` (assuming the appropriate docker credentials are stored in your environment, docker is installed, etc.).

For other examples, check out the `build` folder of this repo and any other mentioned above!

## Design

### I Want One!

Before diving too deep into EBBS, please also give a quick look at the parent library: [eons](https://github.com/eons-dev/eons.lib).
The [UserFunctor Utilities](https://github.com/eons-dev/eons.lib#user-functor) will be of particular use in your Builders.

Ebbs builds packages or whatever with `ebbs.Builders`, which extend the self-registering `eons.UserFunctor`. This means you can write your own build scripts and publish them, distribute them with your code, or store them locally in the `repo_store` (see above). A major driving force behind ebbs is to encourage you to share your automation tools with colleagues, friends, and enemies! For example, you could create "my_build.py", containing something like:
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
        # this.supportedProjectTypes.append("exe")
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
That file can then go in a "./ebbs/" or "./eons/" directory, perhaps within your project repository or on [infrastructure.tech](https://infrastructure.tech)!
ebbs can then be invoked with something like: `ebbs -b my_build --my-required-arg my-value`, which will run your Builder in the current path!

Also note the "--" preceding "--my-required-arg", which evaluates to "my_required_arg" (without the "--" and with "_" in place of "-") once in the Builder. This is done for convenience of both command line syntax and python code.

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

ebbs -b my_build
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

For `supportedProjectTypes`, the `Builder` class will split the folder containing the buildPath (i.e. the `rootPath`) on underscores (`_`), storing the first value as `this.projectType` and the second as `this.projectName`. The `projectType` is checked against the used build's `supportedProjectTypes`. If no match is found, the build is aborted prior to executing the build. If you would like your Builder to work with all project types (and thus ignore that whole naming nonsense), set `this.supportedProjectTypes = []`, where none (i.e. `[]`, not actually `None`) means "all".


You'll also get the following paths variables populated by default:
```python
this.srcPath = f"{this.rootPath}/src"
this.incPath = f"{this.rootPath}/inc"
this.depPath = f"{this.rootPath}/dep"
this.libPath = f"{this.rootPath}/lib"
this.exePath = f"{this.rootPath}/exe"
this.testPath = f"{this.rootPath}/test"
```

When a `Builder` is executed, the following are called in order:  
(kwargs is the same for all)
```python
this.ValidateArgs() # <- not recommended to override.
this.BeforeFunction() # <- virtual (ok to override)
#Builder sets the above mentioned variables here
this.PreBuild() # <- virtual (ok to override)
#Supported project types are checked here
this.Build() # <- abstract method for you  (MUST override)
this.PostBuild() # <- virtual (ok to override)
if (this.DidBuildSucceed()):
    this.BuildNext()
this.AfterFunction() # <- virtual (ok to override)
```
