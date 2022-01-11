import os
import logging
import platform
import shutil
import jsonpickle
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath
from subprocess import Popen, PIPE, STDOUT
import eons as e
from .Exceptions import *

class Builder(e.UserFunctor):
    def __init__(self, name=e.INVALID_NAME()):
        super().__init__(name)

        self.requiredKWArgs.append("dir")

        #For optional args, supply the arg name as well as a default value.
        self.optionalKWArgs = {}

        self.supportedProjectTypes = []

        self.projectType = "bin"
        self.projectName = e.INVALID_NAME()

        self.clearBuildPath = True

    # Build things!
    # Override this or die.
    # Empty Builders can be used with config.json to start build trees.
    def Build(self):
        pass

    # RETURN whether or not the build was successful.
    # Override this to perform whatever success checks are necessary.
    # This will be called before running the next build step.
    def DidBuildSucceed(self):
        return True

    # Hook for any pre-build configuration
    def PreBuild(self, **kwargs):
        pass

    # Hook for any post-build configuration
    def PostBuild(self, **kwargs):
        pass

    # Sets the build path that should be used by children of *this.
    # Also sets src, inc, lib, and dep paths, if they are present.
    def PopulatePaths(self, buildPath):
        self.buildPath = buildPath

        rootPath = os.path.abspath(os.path.join(self.buildPath, "../"))
        if (os.path.isdir(rootPath)):
            self.rootPath = rootPath
        else:
            self.rootPath = None

        paths = [
            "src",
            "inc",
            "dep",
            "lib"
        ]
        for path in paths:
            tmpPath = os.path.abspath(os.path.join(self.buildPath, f"../{path}"))
            if (os.path.isdir(tmpPath)):
                setattr(self, f"{path}Path", tmpPath)
            else:
                setattr(self, f"{path}Path", None)


    #Takes config values and keywords and makes them member variables.
    #CLI args (kwargs) always take priority over config values.
    def PopulateVars(self, **kwargs):
        if (self.config is not None):
            for key, val in self.config.items():
                setattr(self, key, val)
        for key, val in kwargs.items():
            setattr(self, key[2:], val) #[2:] to strip "--"

    # Calls PopulatePaths and PopulateVars after getting information from local directory
    # Projects should have a name of {project-type}_{project-name}.
    # For information on how projects should be labelled see: https://eons.dev/convention/naming/
    # For information on how projects should be organized, see: https://eons.dev/convention/uri-names/
    def PopulateProjectDetails(self, **kwargs):
        self.os = platform.system()
        self.executor = kwargs.pop("executor")
        self.PopulatePaths(kwargs.pop("dir"))
        details = os.path.basename(os.path.abspath(os.path.join(self.buildPath, "../"))).split("_")
        self.projectType = details[0]
        if (len(details) > 1):
            self.projectName = '_'.join(details[1:])
        self.repo = kwargs.pop("repo")
        configPath = os.path.join(self.rootPath, "config.json")
        self.config = None
        if (os.path.isfile(configPath)):
            configFile = open(configPath, "r")
            self.config = jsonpickle.decode(configFile.read())
        self.PopulateVars(**kwargs)

    # Creates the folder structure for the next build step.
    # RETURNS the next buildPath.
    def PrepareNext(self, nextBuilder):
        logging.debug(f"Preparing for next builder: {nextBuilder['language']}")
        nextPath = f"{nextBuilder['type']}_{nextBuilder['name']}"
        mkpath(nextPath)
        if ("copy" in nextBuilder):
            for cpy in nextBuilder["copy"]:
                # logging.debug(f"copying: {cpy}")
                for src, dst in cpy.items():
                    destination = os.path.join(nextPath, dst)
                    mkpath(destination)
                    logging.debug(f"Copying {src} to {destination}")
                    if os.path.isfile(src):
                        copy_file(src, destination)
                    elif os.path.isdir(src):
                        copy_tree(src, destination)
        nextConfigFile = os.path.join(nextPath, "config.json")
        logging.debug(f"writing: {nextConfigFile}")
        nextConfig = open(nextConfigFile, "w")
        nextConfig.write(jsonpickle.encode(nextBuilder["config"]))
        nextConfig.close()
        return nextPath

    # Runs the next Builder.
    # Uses the Executor passed to *this.
    def BuildNext(self):
        if (not hasattr(self, "ebbs_next")):
            logging.info("Build process complete!")
            return

        for nxt in self.ebbs_next:
            nxtPath = os.path.join(self.PrepareNext(nxt), nxt["buildPath"])
            logging.debug(f"Executing {nxt['language']} in {nxtPath}")
            self.executor.Execute(language=nxt["language"], dir=nxtPath, parent=self)

    #Override of eons.UserFunctor method. See that class for details.
    def ValidateArgs(self, **kwargs):
        self.PopulateProjectDetails(**kwargs)

        for rkw in self.requiredKWArgs:
            if (hasattr(self, rkw)):
                continue
            # First, lets see if what we need is set in the environment.
            envVar = os.getenv(rkw)
            if (envVar is not None):
                setattr(self, rkw, envVar)
            else:
                # Nope. Failed.
                errStr = f"{rkw} required but not found."
                logging.error(errStr)
                raise MissingArgumentError(errStr)

        for okw, default in self.optionalKWArgs.items():
            if (hasattr(self, okw)):
                continue
            # First, lets see if what we need is set in the environment.
            envVar = os.getenv(okw)
            if (envVar is not None):
                setattr(self, okw, envVar)
            else:
                setattr(self, okw, default)

    # Override of eons.Functor method. See that class for details
    def UserFunction(self, **kwargs):
        self.buildPath = os.path.join(self.rootPath, self.buildPath)
        if(self.clearBuildPath):
            if (os.path.exists(self.buildPath)):
                logging.info(f"DELETING {self.buildPath}")
                shutil.rmtree(self.buildPath)
            mkpath(self.buildPath)
            os.chdir(self.buildPath)
        self.PreBuild()
        if (len(self.supportedProjectTypes) and self.projectType not in self.supportedProjectTypes):
            raise ProjectTypeNotSupported(
                f"{self.projectType} is not supported. Supported project types for {self.name} are {self.supportedProjectTypes}")
        logging.info(f"Using {self.name} to build {self.projectName}, a {self.projectType}")
        self.Build()
        self.PostBuild()
        if (self.DidBuildSucceed()):
            self.BuildNext()
        else:
            logging.error("Build did not succeed.")

    # RETURNS: an opened file object for writing.
    # Creates the path if it does not exist.
    def CreateFile(self, file, mode="w+"):
        mkpath(os.path.dirname(os.path.abspath(file)))
        return open(file, mode)

    # Run whatever.
    # DANGEROUS!!!!!
    # TODO: check return value and raise exceptions?
    # per https://stackoverflow.com/questions/803265/getting-realtime-output-using-subprocess
    def RunCommand(self, command):
        p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        while True:
            line = p.stdout.readline()
            if (not line):
                break
            print(line.decode('utf8')[:-1])  # [:-1] to strip excessive new lines.
