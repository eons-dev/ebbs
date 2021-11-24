import os
import logging
import platform
from abc import abstractmethod
from subprocess import Popen, PIPE, STDOUT
from distutils.dir_util import mkpath
import eons as e
from .Exceptions import *

class Builder(e.UserFunctor):
    def __init__(self, name=e.INVALID_NAME()):
        super().__init__(name)
        
        self.requiredKWArgs.append("dir")

        self.supportedProjectTypes = []

        #TODO: project is looking an awful lot like a Datum.. Would making it one add functionality?
        self.projectType = "bin"
        self.projectName = e.INVALID_NAME()

    #Build things!
    #Override this or die.
    @abstractmethod
    def Build(self):
        raise NotImplementedError

    #Projects should have a name of {project-type}_{project-name}.
    #For information on how projects should be labelled see: https://eons.dev/convention/naming/
    #For information on how projects should be organized, see: https://eons.dev/convention/uri-names/
    def PopulateProjectDetails(self):
        details = os.path.basename(self.rootPath).split("_")
        self.projectType = details[0]
        if (len(details) > 1):
            self.projectName = '_'.join(details[1:])
        self.os = platform.system()
        self.architecture = platform.machine()

    #Sets the build path that should be used by children of *this.
    #Also sets src, inc, lib, and dep paths, if they are present.
    def SetBuildPath(self, path):
        self.buildPath = path

        #TODO: Consolidate this code with more attribute hacks?
        self.rootPath = os.path.abspath(os.getcwd())

        srcPath = os.path.abspath(os.path.join(self.rootPath, "src"))
        if (os.path.isdir(srcPath)):
            self.srcPath = srcPath
        else:
            self.srcPath = None
        incPath = os.path.abspath(os.path.join(self.rootPath, "inc"))
        if (os.path.isdir(incPath)):
            self.incPath = incPath
        else:
            self.incPath = None
        depPath = os.path.abspath(os.path.join(self.rootPath, "dep"))
        if (os.path.isdir(depPath)):
            self.depPath = depPath
        else:
            self.depPath = None
        libPath = os.path.abspath(os.path.join(self.rootPath, "lib"))
        if (os.path.isdir(srcPath)):
            self.libPath = libPath
        else:
            self.libPath = None

    #Hook for any pre-build configuration
    def PreBuild(self, **kwargs):
        pass

    #Hook for any post-build configuration
    def PostBuild(self, **kwargs):
        # TODO: Do we need to clear self.buildPath here?
        pass

    def UserFunction(self, **kwargs):
        self.executor = kwargs.get("executor")
        self.SetBuildPath(kwargs.get("dir"))
        self.PopulateProjectDetails()
        self.PreBuild(**kwargs)
        if (len(self.supportedProjectTypes) and self.projectType not in self.supportedProjectTypes):
            raise ProjectTypeNotSupported(f"{self.projectType} is not supported. Supported project types for {self.name} are {self.supportedProjectTypes}")
        logging.info(f"Using {self.name} to build {self.projectName}, a {self.projectType}")
        self.Build()
        self.PostBuild(**kwargs)

    #RETURNS: an opened file object for writing.
    #Creates the path if it does not exist.
    def CreateFile(self, file, mode="w+"):
        mkpath(os.path.dirname(os.path.abspath(file)))
        return open(file, mode)

    #Run whatever.
    #DANGEROUS!!!!!
    #TODO: check return value and raise exceptions?
    #per https://stackoverflow.com/questions/803265/getting-realtime-output-using-subprocess
    def RunCommand(self, command):
        p = Popen(command, stdout = PIPE, stderr = STDOUT, shell = True)
        while True:
          line = p.stdout.readline()
          if (not line):
            break
          print(line.decode('ascii')[:-1]) #[:-1] to strip excessive new lines.
