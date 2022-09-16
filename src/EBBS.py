import os
import logging
import eons as e
from pathlib import Path
from .Exceptions import *

class EBBS(e.Executor):

    def __init__(this):
        super().__init__(name="eons Basic Build System", descriptionStr="A hackable build system for all builds!")

        # this.RegisterDirectory("ebbs")


    #Configure class defaults.
    #Override of eons.Executor method. See that class for details
    def Configure(this):
        super().Configure()

        this.defualtConfigFile = "build.json"


    #Override of eons.Executor method. See that class for details
    def RegisterAllClasses(this):
        super().RegisterAllClasses()
        # this.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build"))


    #Override of eons.Executor method. See that class for details
    def AddArgs(this):
        super().AddArgs()
        this.argparser.add_argument('-b','--build', type = str, metavar = 'cpp', help = 'script to use for building', dest = 'builder')
        this.argparser.add_argument('-e','--event', type = str, action='append', nargs='*', metavar = 'release', help = 'what is going on that triggered this build?', dest = 'events')


    #Override of eons.Executor method. See that class for details
    def ParseArgs(this):
        super().ParseArgs()

        this.args.path = os.getcwd() #used to be arg; now we hard code

        this.events = set()
        if (this.args.events is not None):
            [[this.events.add(str(e)) for e in l] for l in this.args.events]

        if (not this.args.builder):
            logging.debug("No build specified. Assuming build pipeline is written in config.")


    #Override of eons.Executor method. See that class for details
    def InitData(this):
        this.rootPath = Path(this.Fetch('path', '../')).resolve() #ebbs is usually called from a build folder in a project, i.e. .../build/../ = /


    #Override of eons.Executor method. See that class for details
    def UserFunction(this):
        super().UserFunction()
        build_in = this.extraArgs.pop('build_in', this.Fetch('build_in', default="build"))
        if (this.Execute(this.args.builder, this.args.path, build_in, this.events, **this.extraArgs)):
            logging.info("Build process complete!")
        else:
            logging.info("Build failed.")


    #Run a build script.
    #RETURNS whether or not the build was successful.
    def Execute(this, build, path, build_in, events, **kwargs):
        if (build is None or not build):
            builder = Builder("EMPTY")
        else:
            builder = this.GetRegistered(build, "build")
        prettyPath = str(Path(path).joinpath(build_in).resolve())
        logging.debug(f"Executing {build} in {prettyPath} with events {events} and additional args: {kwargs}")
        builder(executor=this, path=path, build_in=build_in, events=events, **kwargs)
        return builder.DidBuildSucceed()
