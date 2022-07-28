import os
import logging
import platform
import shutil
import jsonpickle
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
import eons as e
from .Exceptions import *


class Builder(e.UserFunctor):
    def __init__(this, name=e.INVALID_NAME()):
        super().__init__(name)

        # For optional args, supply the arg name as well as a default value.
        this.optionalKWArgs = {}

        # What can this build, "bin", "lib", "img", ... ?
        this.supportedProjectTypes = []

        this.projectType = None
        this.projectName = None

        this.clearBuildPath = False

        this.configMap = {
            "name": "projectName",
            "type": "projectType",
            "clear_build_path": "clearBuildPath"
        }


    # Build things!
    # Override this or die.
    # Empty Builders can be used with build.json to start build trees.
    def Build(this):
        pass


    # RETURN whether or not the build was successful.
    # Override this to perform whatever success checks are necessary.
    # This will be called before running the next build step.
    def DidBuildSucceed(this):
        return True


    # Hook for any pre-build configuration
    def PreBuild(this):
        pass


    # Hook for any post-build configuration
    def PostBuild(this):
        pass


    # Sets the build path that should be used by children of *this.
    # Also sets src, inc, lib, and dep paths, if they are present.
    def PopulatePaths(this, rootPath, buildFolder):
        if (rootPath is None):
            logging.warn("no \"dir\" supplied. buildPath is None")
            return

        this.rootPath = os.path.abspath(rootPath)

        this.buildPath = os.path.join(this.rootPath, buildFolder)
        Path(this.buildPath).mkdir(parents=True, exist_ok=True)

        paths = [
            "src",
            "inc",
            "dep",
            "lib",
            "bin",
            "test"
        ]
        for path in paths:
            tmpPath = os.path.abspath(os.path.join(this.rootPath, path))
            if (os.path.isdir(tmpPath)):
                setattr(this, f"{path}Path", tmpPath)
            else:
                setattr(this, f"{path}Path", None)


    # Populate the configuration details for *this.
    def PopulateLocalConfig(this, configName="build.json"):
        this.config = None
        localConfigFile = os.path.join(this.rootPath, configName)
        logging.debug(f"Looking for local configuration: {localConfigFile}")
        if (os.path.isfile(localConfigFile)):
            configFile = open(localConfigFile, "r")
            this.config = jsonpickle.decode(configFile.read())
            configFile.close()
            logging.debug(f"Got local config contents: {this.config}")


    # Convert Fetched values to their proper type.
    # This can also allow for use of {this.val} expression evaluation.
    def EvaluateToType(this, value, evaluateExpression = False):
        if (isinstance(value, dict)):
            ret = {}
            for key, value in value.items():
                ret[key] = this.EvaluateToType(value)
            return ret

        elif (isinstance(value, list)):
            ret = []
            for value in value:
                ret.append(this.EvaluateToType(value))
            return ret

        else:
            if (evaluateExpression):
                evaluatedvalue = eval(f"f\"{value}\"")
            else:
                evaluatedvalue = str(value)

            #Check original type and return the proper value.
            if (isinstance(value, (bool, int, float)) and evaluatedvalue == str(value)):
                return value

            #Check resulting type and return a casted value.
            #TODO: is there a better way than double cast + comparison?
            if (evaluatedvalue.lower() == "false"):
                return False
            elif (evaluatedvalue.lower() == "true"):
                return True

            try:
                if (str(float(evaluatedvalue)) == evaluatedvalue):
                    return float(evaluatedvalue)
            except:
                pass

            try:
                if (str(int(evaluatedvalue)) == evaluatedvalue):
                    return int(evaluatedvalue)
            except:
                pass

            #The type must be a string.
            return evaluatedvalue

    # Wrapper around setattr
    def Set(this, varName, value):
        value = this.EvaluateToType(value)
        for key, var in this.configMap.items():
            if (varName == key):
                varName = var
                break
        logging.debug(f"Setting ({type(value)}) {varName} = {value}")
        setattr(this, varName, value)


    # Will try to get a value for the given varName from:
    #    first: this
    #    second: the local config file
    #    third: the executor (args > config > environment)
    # RETURNS the value of the given variable or None.
    def Fetch(this,
        varName,
        default=None,
        enableThisBuilder=True,
        enableThisExecutor=True,
        enableArgs=True,
        enableLocalConfig=True,
        enableExecutorConfig=True,
        enableEnvironment=True):

        ret = this.executor.Fetch(varName, default, enableThisExecutor, enableArgs, enableExecutorConfig, enableEnvironment)

        if (enableThisBuilder and hasattr(this, varName)):
            logging.debug("...got {varName} from self ({this.name}).")
            return getattr(this, varName)

        if (enableLocalConfig and this.config is not None):
            for key, val in this.config.items():
                if (key == varName):
                    logging.debug(f"...got {varName} from local config.")
                    return val

        return ret


    # Calls PopulatePaths and PopulateVars after getting information from local directory
    # Projects should have a name of {project-type}_{project-name}.
    # For information on how projects should be labelled see: https://eons.llc/convention/naming/
    # For information on how projects should be organized, see: https://eons.llc/convention/uri-names/
    def PopulateProjectDetails(this, **kwargs):
        this.os = platform.system()
        this.executor = kwargs.pop('executor')
        this.events = kwargs.pop('events')

        this.PopulatePaths(kwargs.pop("path"), kwargs.pop('build_in'))
        this.PopulateLocalConfig()

        for key, var in this.configMap.items():
            this.Set(key, this.Fetch(key, default=None, enableThisBuilder=False, enableThisExecutor=False))

        details = os.path.basename(this.rootPath).split("_")
        if (this.projectType is None):
            this.projectType = details[0]
        if (this.projectName is None):
            if (len(details) > 1):
                this.projectName = '_'.join(details[1:])
            else:
                this.projectName = e.INVALID_NAME()


    # RETURNS whether or not we should trigger the next Builder based on what events invoked ebbs.
    # Anything in the "run_when" list will require a corresponding --event specification to run.
    # For example "run_when":"publish" would require `--event publish` to enable publication Builders in the workflow.
    def ValidateNext(this, nextBuilder):
        if ("run_when" in nextBuilder):
            if (not set([str(r) for r in nextBuilder["run_when"]]).issubset(this.events)):
                logging.info(
                    f"Skipping next builder: {nextBuilder['build']}; required events not met (needs {nextBuilder['run_when']} but only have {this.events})")
                return False
        return True


    # Creates the folder structure for the next build step.
    # RETURNS the next buildPath.
    def PrepareNext(this, nextBuilder):
        logging.debug(f"<---- preparing for next builder: {nextBuilder['build']} ---->")
        # logging.debug(f"Preparing for next builder: {nextBuilder}")

        nextPath = "."
        if ("path" in nextBuilder):
            nextPath = nextBuilder["path"]
        nextPath = os.path.join(this.buildPath, nextPath)
        # mkpath(nextPath) <- just broken.
        Path(nextPath).mkdir(parents=True, exist_ok=True)
        logging.debug(f"Next build path is: {nextPath}")

        if ("copy" in nextBuilder):
            for cpy in nextBuilder["copy"]:
                # logging.debug(f"copying: {cpy}")
                for src, dst in cpy.items():
                    destination = os.path.join(nextPath, dst)
                    if (os.path.isfile(src)):
                        logging.debug(f"Copying file {src} to {destination}")
                        try:
                            shutil.copy(src, destination)
                        except shutil.Error as exc:
                            errors = exc.args[0]
                            for error in errors:
                                src, dst, msg = error
                                logging.debug(f"{msg}")
                    elif (os.path.isdir(src)):
                        logging.debug(f"Copying directory {src} to {destination}")
                        try:
                            shutil.copytree(src, destination)
                        except shutil.Error as exc:
                            errors = exc.args[0]
                            for error in errors:
                                src, dst, msg = error
                                logging.debug(f"{msg}")

        if ("config" in nextBuilder):
            nextConfigFile = os.path.join(nextPath, "build.json")
            logging.debug(f"writing: {nextConfigFile}")
            nextConfig = open(nextConfigFile, "w")
            for key, var in this.configMap.items():
                if (key not in nextBuilder["config"]):
                    val = getattr(this, var)
                    logging.debug(f"Adding to config: {key} = {val}")
                    nextBuilder["config"][key] = val
            nextConfig.write(jsonpickle.encode(nextBuilder["config"]))
            nextConfig.close()

        logging.debug(f">----<")
        return nextPath


    # Runs the next Builder.
    # Uses the Executor passed to *this.
    def BuildNext(this):
        #When fetching what to do next, everything is valid EXCEPT the environment. Otherwise we could do something like `export next='nop'` and never quit.
        #A similar situation arises when using the global config for each build step. We only use the global config if *this is the first builder and no local config was supplied.
        shouldUseExecutor = this.config is None
        if (shouldUseExecutor):
            logging.debug(f"{this.name} has no local config, so we will see if the Executor knows what to do next.")
        next = this.Fetch('next',
            default=None,
            enableThisBuilder=True,
            enableThisExecutor=shouldUseExecutor,
            enableArgs=shouldUseExecutor,
            enableLocalConfig=True,
            enableExecutorConfig=shouldUseExecutor,
            enableEnvironment=False)

        if (next is None):
            return

        for nxt in next:
            if (not this.ValidateNext(nxt)):
                continue
            nxtPath = this.PrepareNext(nxt)
            buildFolder = f"then_build_{nxt['build']}"
            if ("build_in" in nxt):
                buildFolder = nxt["build_in"]
            result = this.executor.Execute(
                build=nxt["build"],
                path=nxtPath,
                build_in=buildFolder,
                events=this.events)
            if (not result and ('tolerate_failure' not in nxt or not nxt['tolerate_failure'])):
                logging.error(f"Building {nxt['build']} failed. Aborting.")
                break



    # Override of eons.UserFunctor method. See that class for details.
    def ValidateArgs(this, **kwargs):
        # logging.debug(f"Got arguments: {kwargs}")

        this.PopulateProjectDetails(**kwargs)

        for rkw in this.requiredKWArgs:
            if (hasattr(this, rkw)):
                continue

            fetched = this.Fetch(rkw)
            if (fetched is not None):
                this.Set(rkw, fetched)
                continue

            # Nope. Failed.
            errStr = f"{rkw} required but not found."
            logging.error(errStr)
            raise BuildError(errStr)

        for okw, default in this.optionalKWArgs.items():
            if (hasattr(this, okw)):
                continue

            this.Set(okw, this.Fetch(okw, default=default))


    # Override of eons.Functor method. See that class for details
    def UserFunction(this, **kwargs):
        if (this.clearBuildPath):
            if (os.path.exists(this.buildPath)):
                logging.info(f"DELETING {this.buildPath}")
                shutil.rmtree(this.buildPath)
        # mkpath(this.buildPath) <- This just straight up doesn't work. Race condition???
        Path(this.buildPath).mkdir(parents=True, exist_ok=True)
        os.chdir(this.buildPath)

        this.PreBuild()

        if (len(this.supportedProjectTypes) and this.projectType not in this.supportedProjectTypes):
            raise ProjectTypeNotSupported(
                f"{this.projectType} is not supported. Supported project types for {this.name} are {this.supportedProjectTypes}")
        logging.info(f"Using {this.name} to build \"{this.projectName}\", a \"{this.projectType}\" in {this.buildPath}")

        logging.debug(f"<---- Building {this.name} ---->")
        this.Build()
        logging.debug(f">----<")

        this.PostBuild()

        if (this.DidBuildSucceed()):
            this.BuildNext()
        else:
            logging.error("Build did not succeed.")


    # RETURNS: an opened file object for writing.
    # Creates the path if it does not exist.
    def CreateFile(this, file, mode="w+"):
        Path(os.path.dirname(os.path.abspath(file))).mkdir(parents=True, exist_ok=True)
        return open(file, mode)


    # Run whatever.
    # DANGEROUS!!!!!
    # TODO: check return value and raise exceptions?
    # per https://stackoverflow.com/questions/803265/getting-realtime-output-using-subprocess
    def RunCommand(this, command):
        p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
        while True:
            line = p.stdout.readline()
            if (not line):
                break
            print(line.decode('utf8')[:-1])  # [:-1] to strip excessive new lines.
