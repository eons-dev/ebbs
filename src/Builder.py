import os
import logging
import platform
import shutil
import jsonpickle
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
import eons as e
from .Exceptions import *


class Builder(e.UserFunctor):
    def __init__(self, name=e.INVALID_NAME()):
        super().__init__(name)

        # For optional args, supply the arg name as well as a default value.
        self.optionalKWArgs = {}

        # What can this build, "bin", "lib", "img", ... ?
        self.supportedProjectTypes = []

        self.projectType = "bin"
        self.projectName = e.INVALID_NAME()

        self.clearBuildPath = False

        self.configMap = {
            "name": "projectName",
            "type": "projectType",
            "clear_build_path": "clearBuildPath"
        }

    # Build things!
    # Override this or die.
    # Empty Builders can be used with build.json to start build trees.
    def Build(self):
        pass

    # RETURN whether or not the build was successful.
    # Override this to perform whatever success checks are necessary.
    # This will be called before running the next build step.
    def DidBuildSucceed(self):
        return True

    # Hook for any pre-build configuration
    def PreBuild(self):
        pass

    # Hook for any post-build configuration
    def PostBuild(self):
        pass

    # Sets the build path that should be used by children of *this.
    # Also sets src, inc, lib, and dep paths, if they are present.
    def PopulatePaths(self, rootPath, buildFolder):
        if (rootPath is None):
            logging.warn("no \"dir\" supplied. buildPath is None")
            return

        self.rootPath = os.path.abspath(rootPath)

        self.buildPath = os.path.join(self.rootPath, buildFolder)
        Path(self.buildPath).mkdir(parents=True, exist_ok=True)

        paths = [
            "src",
            "inc",
            "dep",
            "lib",
            "test"
        ]
        for path in paths:
            tmpPath = os.path.abspath(os.path.join(self.rootPath, path))
            if (os.path.isdir(tmpPath)):
                setattr(self, f"{path}Path", tmpPath)
            else:
                setattr(self, f"{path}Path", None)

    # Wrapper around setattr
    def SetVar(self, varName, value):
        for key, var in self.configMap.items():
            if (varName == key):
                varName = var
                break
        logging.debug(f"Setting {varName} = {value}")
        setattr(self, varName, value)

    # Will try to get a value for the given varName from:
    #    first: self
    #    second: the parent
    #    third: the environment
    # RETURNS the value of the given variable or None.
    def FetchVar(self, varName):
        logging.debug(f"{self.name} looking to fetch {varName}")

        if (hasattr(self, varName)):
            logging.debug(f"{self.name} got {varName} from myself!")
            return getattr(self, varName)

        if (hasattr(self, "parent")):
            parentVar = self.parent.FetchVar(varName)
            if (parentVar is not None):
                logging.debug(f"{self.name} got {varName} from parent ({self.parent.name})")
                return parentVar

        envVar = os.getenv(varName)
        if (envVar is not None):
            logging.debug(f"{self.name} got {varName} from envionment")
            return envVar

        return None

    # Takes config values and keywords and makes them member variables.
    # CLI args (kwargs) always take priority over config values.
    def PopulateVars(self, **kwargs):
        if (self.config is not None):
            logging.debug(f"<---- vars from config ---->")
            for key, val in self.config.items():
                self.SetVar(key, val)
            logging.debug(f">----<")
        logging.debug(f"<---- vars from args ---->")
        for key, val in kwargs.items():
            if (key.startswith("--")):  # trim cli args
                key = key[2:]
            self.SetVar(key, val)
        logging.debug(f">----<")

    # Calls PopulatePaths and PopulateVars after getting information from local directory
    # Projects should have a name of {project-type}_{project-name}.
    # For information on how projects should be labelled see: https://eons.dev/convention/naming/
    # For information on how projects should be organized, see: https://eons.dev/convention/uri-names/
    def PopulateProjectDetails(self, **kwargs):
        self.os = platform.system()
        self.executor = kwargs.pop("executor")

        self.PopulatePaths(kwargs.pop("path"), kwargs.pop("build_in"))

        details = os.path.basename(self.rootPath).split("_")
        self.projectType = details[0]
        if (len(details) > 1):
            self.projectName = '_'.join(details[1:])

        configPath = os.path.join(self.rootPath, "build.json")
        self.config = None
        if (os.path.isfile(configPath)):
            configFile = open(configPath, "r")
            self.config = jsonpickle.decode(configFile.read())
            logging.debug(f"Got config contents: {self.config}")
        self.PopulateVars(**kwargs)

    # RETURNS whether or not we should trigger the next Builder based on what events invoked ebbs.
    # Anything in the "run_when" list will require a corresponding --event specification to run.
    # For example "run_when":"publish" would require `--event publish` to enable publication Builders in the workflow.
    def ValidateNext(self, nextBuilder):
        if ("run_when" in nextBuilder):
            if (not set([str(r) for r in nextBuilder["run_when"]]).issubset(self.events)):
                logging.info(
                    f"Skipping next builder: {nextBuilder['build']}; required events not met (needs {nextBuilder['run_when']} but only have {self.events})")
                return False
        return True

    # Creates the folder structure for the next build step.
    # RETURNS the next buildPath.
    def PrepareNext(self, nextBuilder):
        logging.debug(f"<---- preparing for next builder: {nextBuilder['build']} ---->")
        # logging.debug(f"Preparing for next builder: {nextBuilder}")

        nextPath = "."
        if ("path" in nextBuilder):
            nextPath = nextBuilder["path"]
        nextPath = os.path.join(self.buildPath, nextPath)
        # mkpath(nextPath) <- just broken.
        Path(nextPath).mkdir(parents=True, exist_ok=True)
        logging.debug(f"Next build path is: {nextPath}")

        if ("copy" in nextBuilder):
            for cpy in nextBuilder["copy"]:
                # logging.debug(f"copying: {cpy}")
                for src, dst in cpy.items():
                    destination = os.path.join(nextPath, dst)
                    if os.path.isfile(src):
                        logging.debug(f"Copying file {src} to {destination}")
                        copy_file(src, destination)
                    elif os.path.isdir(src):
                        logging.debug(f"Copying directory {src} to {destination}")
                        copy_tree(src, destination)

        if ("config" in nextBuilder):
            nextConfigFile = os.path.join(nextPath, "build.json")
            logging.debug(f"writing: {nextConfigFile}")
            nextConfig = open(nextConfigFile, "w")
            for key, var in self.configMap.items():
                if (key not in nextBuilder["config"]):
                    val = getattr(self, var)
                    logging.debug(f"Adding to config: {key} = {val}")
                    nextBuilder["config"][key] = val
            nextConfig.write(jsonpickle.encode(nextBuilder["config"]))
            nextConfig.close()

        logging.debug(f">----<")
        return nextPath

    # Runs the next Builder.
    # Uses the Executor passed to *this.
    def BuildNext(self):
        if (not hasattr(self, "ebbs_next")):
            logging.info("Build process complete!")
            return

        for nxt in self.ebbs_next:
            if (not self.ValidateNext(nxt)):
                continue
            nxtPath = self.PrepareNext(nxt)
            buildFolder = f"then_build_{nxt['build']}"
            if ("build_in" in nxt):
                buildFolder = nxt["build_in"]
            self.executor.Execute(build=nxt["build"], path=nxtPath, build_in=buildFolder, events=self.events,
                                  parent=self, name=self.projectName, type=self.projectType)

    # Override of eons.UserFunctor method. See that class for details.
    def ValidateArgs(self, **kwargs):
        # logging.debug(f"Got arguments: {kwargs}")

        self.PopulateProjectDetails(**kwargs)

        for rkw in self.requiredKWArgs:
            if (hasattr(self, rkw)):
                continue

            fetched = self.FetchVar(rkw)
            if (fetched is not None):
                self.SetVar(fetched)
                continue

            # Nope. Failed.
            errStr = f"{rkw} required but not found."
            logging.error(errStr)
            raise BuildError(errStr)

        for okw, default in self.optionalKWArgs.items():
            if (hasattr(self, okw)):
                continue

            fetched = self.FetchVar(okw)
            if (fetched is not None):
                self.SetVar(okw, fetched)
                continue

            logging.debug(f"Failed to fetch {okw}. Using defualt value: {default}")
            self.SetVar(okw, default)

    # Override of eons.Functor method. See that class for details
    def UserFunction(self, **kwargs):
        if (self.clearBuildPath):
            if (os.path.exists(self.buildPath)):
                logging.info(f"DELETING {self.buildPath}")
                shutil.rmtree(self.buildPath)
        # mkpath(self.buildPath) <- This just straight up doesn't work. Race condition???
        Path(self.buildPath).mkdir(parents=True, exist_ok=True)
        os.chdir(self.buildPath)

        self.PreBuild()

        if (len(self.supportedProjectTypes) and self.projectType not in self.supportedProjectTypes):
            raise ProjectTypeNotSupported(
                f"{self.projectType} is not supported. Supported project types for {self.name} are {self.supportedProjectTypes}")
        logging.info(f"Using {self.name} to build \"{self.projectName}\", a \"{self.projectType}\" in {self.buildPath}")

        logging.debug(f"<---- Building {self.name} ---->")
        self.Build()
        logging.debug(f">----<")

        self.PostBuild()

        if (self.DidBuildSucceed()):
            self.BuildNext()
        else:
            logging.error("Build did not succeed.")

    # RETURNS: an opened file object for writing.
    # Creates the path if it does not exist.
    def CreateFile(self, file, mode="w+"):
        Path(os.path.dirname(os.path.abspath(file))).mkdir(parents=True, exist_ok=True)
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
