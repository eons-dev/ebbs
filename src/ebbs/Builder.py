import os
import logging
from abc import abstractmethod
from subprocess import Popen, PIPE, STDOUT
from distutils.dir_util import mkpath
from esam.UserFunctor import UserFunctor
from esam import Constants as c

class Builder(UserFunctor):
    def __init__(self, name=c.INVALID_NAME):
        super().__init__(name)
        
        self.requiredKWArgs.append("dir")

        self.supportedProjectTypes = []

        #TODO: project is looking an awful lot like a Datum.. Would making it one add functionality?
        self.projectType = "bin"
        self.projectName = c.INVALID_NAME

    #Build things!
    #Override this or die.
    @abstractmethod
    def Build(self):
        raise NotImplementedError

    #Project types can be things like "lib" for library, "bin" for binary, etc. Generally, they are any string that evaluates to a different means of building code.
    class ProjectTypeNotSupported(Exception): pass

    #Projects should have a name of {project-type}_{project-name}.
    #For information on how projects should be labelled see: https://eons.dev/convention/naming/
    #For information on how projects should be organized, see: https://eons.dev/convention/uri-names/
    def PopulateProjectDetails(self):
        details = os.path.basename(os.path.abspath(os.path.join(self.buildPath,"../"))).split("_")
        self.projectType = details[0]
        if (len(details) > 1):
            self.projectName = ''.join(details[1:])
        
    #Sets the build path that should be used by children of *this.
    #Also sets src, inc, lib, and dep paths, if they are present.
    def SetBuildPath(self, path):
        self.buildPath = path

        #TODO: Consolidate this code with more attribute hacks?
        rootPath = os.path.abspath(os.path.join(self.buildPath, "../"))
        if (os.path.isdir(rootPath)):
            self.rootPath = rootPath
        else:
            self.rootPath = None
        srcPath = os.path.abspath(os.path.join(self.buildPath, "../src"))
        if (os.path.isdir(srcPath)):
            self.srcPath = srcPath
        else:
            self.srcPath = None
        incPath = os.path.abspath(os.path.join(self.buildPath, "../inc"))
        if (os.path.isdir(incPath)):
            self.incPath = incPath
        else:
            self.incPath = None
        depPath = os.path.abspath(os.path.join(self.buildPath, "../dep"))
        if (os.path.isdir(depPath)):
            self.depPath = depPath
        else:
            self.depPath = None
        libPath = os.path.abspath(os.path.join(self.buildPath, "../lib"))
        if (os.path.isdir(srcPath)):
            self.libPath = libPath
        else:
            self.libPath = None

    def UserFunction(self, **kwargs):
        self.SetBuildPath(kwargs.get("dir"))
        self.PopulateProjectDetails()
        if (self.projectType not in self.supportedProjectTypes):
            raise self.ProjectTypeNotSupported(f"{self.projectType} is not supported. Supported project types for {self.name} are {self.supportedProjectTypes}")
        logging.info(f"Using {self.name} to build {self.projectName}, a {self.projectType}")
        self.Build()
        #TODO: Do we need to clear self.buildPath here?

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
