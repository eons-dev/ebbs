import os
import logging
import eons as e
from .Exceptions import *

class EBBS(e.Executor):

    def __init__(self):
        super().__init__(name="eons Basic Build System", descriptionStr="A hackable build system for all builds!")

        self.RegisterDirectory("ebbs")

    #Override of eons.Executor method. See that class for details
    def RegisterAllClasses(self):
        super().RegisterAllClasses()
        self.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build"))

    #Override of eons.Executor method. See that class for details
    def AddArgs(self):
        super().AddArgs()
        self.argparser.add_argument('path', type = str, nargs='?', metavar = '/project/', help = 'path to project folder', default = '.')
        self.argparser.add_argument('-i', '--build-in', type = str, metavar = 'build', help = 'name of folder to use inside project (/project/build/)', default = 'build', dest = 'build_in')
        self.argparser.add_argument('-b','--build', type = str, metavar = 'cpp', help = 'build of files to build', dest = 'lang')

    #Override of eons.Executor method. See that class for details
    def ParseArgs(self):
        super().ParseArgs()

        if (not self.args.lang):
            logging.debug("No build specified. Assuming build pipeline is written in build.json.")

    #Override of eons.Executor method. See that class for details
    def UserFunction(self, **kwargs):
        super().UserFunction(**kwargs)
        self.Execute(self.args.lang, self.args.path, self.args.build_in, **self.extraArgs)

    #Run a build script.
    def Execute(self, build, path, build_in, **kwargs):
        if (not build):
            builder = Builder("EMPTY")
        else:
            builder = self.GetRegistered(build, "build")
        logging.debug(f"Executing {build} in {path}/{build_in} with additional args: {kwargs}")
        builder(executor=self, path=path, build_in=build_in, **kwargs)
