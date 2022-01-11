# eons Basic Build System

![build](https://github.com/eons-dev/bin_ebbs/actions/workflows/python-package.yml/badge.svg)

This project derives from [eons](https://github.com/eons-dev/lib_eons) for easy hacking ;)

## Installation
`pip install ebbs`

## Usage

ebbs assumes that your project is named in accordance with [eons naming conventions](https://eons.llc/convention/naming/) as well as [eons directory conventions](https://eons.llc/convention/uri-names/)

This usually means your project has the name of `bin_my-project`, `lib_my-project`, `test_my-project`, etc.

You must invoke this tool from the root directory of your project (or wherever your code is). For `{project-type}_{project-name}/build`, you would use `ebbs -l {language} build`, which would tell ebbs to build `{project-name}` as a `{project-type}` with the `{language}` builder in the `{build}` folder. At this time only 1 directory level is supported for the buildPath (i.e. "/my/build/path/" is probably invalid, but it depends on the language being used); for now, stick to something safe, like "./build/" or "./generated/". NOTE: The directory you choose does not have to exist: ebbs will make it for you.

Using `-l {language}` executes a Builder (`ebbs.Builder`). The term "language" and "Builder" are often interchangeable; however, "Builder" is preferred, since it is the name of the class. 

Use `ebbs --help` for help ;)

**IMPORTANT NOTE: Most ebbs Builders will DELETE the directory you pass to them.**

This is done so that previous builds cannot create stale data which influence future builds. However, if you mess up and call, say, `ebbs -l cpp ./src` instead of `ebbs -l cpp ./build`, you will lose your "src" folder. Please use this tool responsibly and read up on what each Builder does.
To make things easy, you can search for `clearBuildPath`. If you see `self.clearBuildPath = False` it should be okay to use that Builder with any directory (such is the case for the Publish Builder, which zips & uploads the contents of any directory).

### Where Are These "Languages"?

All languages are searched for in the local file system within the following folders:
NOTE: Collectively, these folders, within your project folder, are called the "workspace"
```python
self.RegisterDirectory("language")
self.RegisterDirectory("inc/language")
self.RegisterDirectory("ebbs/inc/language")
#and 
"eons" #per the eons.Executor.defaultRepoDirectory
```
If the language you specified is not found within one of those directories, ebbs will try to download it from the remote repository with a name of `build_{language}`. The downloaded build script will be saved to whatever directory you set in `--repo-store` (default "./eons/").

Unfortunately, python class names cannot have dashes ("-") in them. Instead, a series of underscores ("_") is often used instead. While this deviates from the eons naming schema, it should still be intelligible for short names. You are, of course, welcome to use whatever naming scheme you would like instead!

### Side Note on Build Path and Languages

The workspace is dependent on where ebbs is invoked. The rootPath & Builder variables are dependent on the directory above the specified buildPath. While this prevents you from using "/my/build/path/", it does allow you to create a single workspace for all your projects.

For example, if you have a "git" and a "workspace" folder in your home directory and you want to use your custom Builder, "my_language" on all the projects in the git folder, instead of copying my_language to every project's workspace, you could simply cd to /home/workspace and call ebbs with the appropriate build directory.
Something like: `me@mine:~/workspace$ ebbs -l my_language ~/git/bin_my-cpp-project/build/; ebbs -l my_language ~/git/lib_my-python-library/generated/`.
While that should work, this is easier but hasn't been tested:`me@mine:~/workspace$ ebbs -l my_language ~/git/**/generated/`

Something like:
```
home/
├─ git/
│  ├─ bin_my-cpp-project/
│  ├─ lib_my-python-library/
├─ workspace/
│  ├─ language/
│  │  ├─ my_language.py
```

### Repository

Online repository settings can be specified with:
```
--repo-store (default = ./eons/)
--repo-url (default = https://api.infrastructure.tech/v1/package)
--repo-username
--repo-password
```

NOTE: you do not need to supply any repo settings to download packages from the public repository.
Because these creds are not pulled from environment variables and are visible on the command line, it is advisable to use app tokens with short expirations. This will be addressed in a future release.

For more info on the repo integration, see [the eons library](https://github.com/eons-dev/lib_eons#online-repository)

By default, ebbs will use the [infrastructure.tech](https://infrastructure.tech) package repository. See the [Infrastructure web server](https://github.com/infrastructure-tech/srv_infrastructure) for more info.

**IMPORTANT CAVEAT FOR ONLINE PACKAGES:** the package name must be preceded by "build_" to be found by ebbs.  
For example, if you want to use `-l my_language` from the repository, ebbs will attempt to download "build_my_language". The package zip is then downloaded, extracted, registered, and instantiated.  
All packages are .zip files.

### Example Build Scripts:

* [Publish](https://github.com/eons-dev/build_publish) <- this one makes other Builders available online.
* [Python](https://github.com/eons-dev/build_py)
* [C++](https://github.com/eons-dev/build_cpp)
* [Docker](https://github.com/eons-dev/build_docker)

### Cascading Builds

As with any good build system, you aren't limited to just one step. With ebbs, you can specify "ebbs_next" in your config.json (see below), which will execute a series of Builders after the initial.

Here's an example config.json that builds a C++ project then pushes it to Dockerhub (taken from the [Infrastructure web server](https://github.com/infrastructure-tech/srv_infrastructure)):
```json
{
  "name" : "entrypoint",
  "cpp_version" : 17,
  "libs_shared": [
    "restbed",
    "cpr"
  ],
  "ebbs_next": [
    {
      "language": "docker",
      "type" : "srv",
      "name" : "infrastructure",
      "buildPath" : "tmp",
      "copy" : [
        {"out/" : "src/"}
      ],
      "config" : {
        "name" : "eons/srv_infrastructure",
        "from" : "eons/img_webserver",
        "os" : "debian",
        "entrypoint" : "/usr/local/bin/entrypoint",
        "also" : [
          "EXPOSE 80"
        ]
      }
    }
  ]
}
```
This script can be invoked with just `ebbs -l cpp ./build` (assuming the appropriate docker credentials are stored in your environment).

## Design

### Where Variables Come From and the config.json

Ebbs is intended to keep your build process separate from your code. With that said, it can be useful to specify some project-wide settings and build configurations.
In order to accommodate more complex builds, ebbs supports the use of a config.json file in the root directory of your project (one directory above the buildPath you provide).

Each Builder will record which arguments it needs and wants in order to function. Those arguments are then populated from:
1. The system environment
2. The config.json
3. The command line

Where, the command line overrides anything specified in the environment and config file.

### I Want One!

Ebbs builds packages or whatever with `ebbs.Builders`, which extend the self-registering `eons.UserFunctor`. This means you can write your own build scripts and place them in a "workspace" (see above) which can then be shared with colleagues, etc. For example, you could create "my_language.py", containing something like:
```python
import logging
from ebbs import Builder

class my_language(Builder):
    def __init__(self, name="My Language"):
        super().__init__(name)
        
        # delete whatever dir was provided to this, so we can start fresh.
        self.clearBuildPath = True
        
        self.supportedProjectTypes = [] #all
        #or
        # self.supportedProjectTypes.append("lib")
        # self.supportedProjectTypes.append("bin")
        # self.supportedProjectTypes.append("test")
        
        #self.requiredKWArgs will cause an error to be thrown prior to execution (i.e. .*Build methods) iff they are not found in the system environment, config.json, nor command line.
        self.requiredKWArgs.append("my_required_arg")
        
        #self.my_optional_arg will be "some default value" unless the user overrides it from the command line or config.json file.
        self.optionalKWArgs["my_optional_arg"] = "some default value"
        
    #Check if the output of all your self.RunCommand() and whatever other calls did what you expected.
    #The "ebbs_next" step will only be executed if this step succeeded.
    def DidBuildSucceed(self):
        return True; #yeah, why not?

    def PreBuild(self):
        logging.info(f"Got {self.my_required_arg} and {self.my_optional_arg}")
        
    #Required Builder method. See that class for details.
    def Build(self):
        #DO STUFF!
```
That file can then go in a "./ebbs/inc/language" directory, perhaps within your project repository or on infrastructure.tech!
ebbs can then be invoked with something like: `ebbs -l my_language ./build --my_required_arg my-value`, which will run your Build method from "./build" (NOTE: "build" does not work with the "py" Builder, use "generated" or literally anything else instead).

Also note the "--" preceding "--my_required_arg", which evaluates to just "my_required_arg" (without the "--") once in the Builder. This is done for convenience of both command line syntax and python code.

You could also do something like:
```shell
cat << EOF > ./config.json
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

ebbs -l my_language ./build
```
Here, the config.json file will be automatically read in, removing the need to specify the args for your language.


Regarding `self.clearBuildPath`, as mentioned above, it is important to not call ebbs on the wrong directory. If your Builder does not need a fresh build path, set `self.clearBuildPath = False`.
With that said, most compilation, packaging, etc. can be broken by stale data from past builds, so ebbs will clear the `buildPath` for you by default. 

You may also have noticed the combination of camelCase and snake_case. This is used to specify buildInValues from user_provided_values. This convention may change with a future release (let us know what you think!).

For `supportedProjectTypes`, the `Builder` class will split the folder containing the buildPath (i.e. the `rootPath`) on underscores ("_"), storing the first value as `self.projectType` and the second as `self.projectName`. The `projectType` is checked against the used language's `supportedProjectTypes`. If no match is found, the build is aborted prior to executing the language. If you would like your Builder to work with all project types (and thus ignore that whole naming nonsense), set `self.supportedProjectTypes = []`, where none (i.e. `[]`, not actually `None`) means "all".


You'll also get the following paths variables populated by default:
(NOTE: the way this is done is why more than 1 level for buildPath is currently unsupported)
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
self.PreCall(**kwargs) # <- virtual (ok to override)
#Builder sets the above mentioned variables here
self.PreBuild(**kwargs) # <- virtual (ok to override)
#Supported project types are checked here
self.Build() # <- abstract method for you  (MUST override)
self.PostBuild(**kwargs) # <- virtual (ok to override)
if (self.DidBuildSucceed()):
    self.BuildNext()
self.PostCall(**kwargs) # <- virtual (ok to override)
```
