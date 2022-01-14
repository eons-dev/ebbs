import os
import logging
import eons as e
from .Exceptions import *

class EBBS(e.Executor):

    def __init__(this):
        super().__init__(name="eons Basic Build System", descriptionStr="A hackable build system for all builds!")

        this.RegisterDirectory("ebbs")

    #Override of eons.Executor method. See that class for details
    def RegisterAllClasses(this):
        super().RegisterAllClasses()
        this.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build"))

    #Override of eons.Executor method. See that class for details
    def AddArgs(this):
        super().AddArgs()
        this.argparser.add_argument('path', type = str, nargs='?', metavar = '/project/', help = 'path to project folder', default = '.')
        this.argparser.add_argument('-i', '--build-in', type = str, metavar = 'build', help = 'name of folder to use inside project (/project/build/)', default = 'build', dest = 'build_in')
        this.argparser.add_argument('-b','--build', type = str, metavar = 'cpp', help = 'build of files to build', dest = 'builder')
        this.argparser.add_argument('-e','--event', type = str, action='append', nargs='*', metavar = 'release', help = 'what is going on that triggered this build?', dest = 'events')


    #Override of eons.Executor method. See that class for details
    def ParseArgs(this):
        super().ParseArgs()

        this.events = set()
        if (this.args.events is not None):
            [[this.events.add(str(e)) for e in l] for l in this.args.events]

        if (not this.args.builder):
            logging.debug("No build specified. Assuming build pipeline is written in build.json.")

    #Override of eons.Executor method. See that class for details
    def UserFunction(this, **kwargs):
        super().UserFunction(**kwargs)
        this.Execute(this.args.builder, this.args.path, this.args.build_in, this.events, **this.extraArgs)

    #Run a build script.
    def Execute(this, build, path, build_in, events, **kwargs):
        if (not build):
            builder = Builder("EMPTY")
        else:
            builder = this.GetRegistered(build, "build")
        logging.debug(f"Executing {build} in {path}/{build_in} with events {events} and additional args: {kwargs}")
        builder(executor=this, path=path, build_in=build_in, events=events, **kwargs)
