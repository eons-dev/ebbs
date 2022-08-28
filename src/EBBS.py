import os
import logging
import eons as e
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
        this.argparser.add_argument('path', type = str, nargs='?', metavar = '/project/', help = 'path to project folder', default = '.')
        this.argparser.add_argument('-b','--build', type = str, metavar = 'cpp', help = 'script to use for building', dest = 'builder')
        this.argparser.add_argument('-e','--event', type = str, action='append', nargs='*', metavar = 'release', help = 'what is going on that triggered this build?', dest = 'events')


    #Override of eons.Executor method. See that class for details
    def ParseArgs(this):
        super().ParseArgs()

        this.events = set()
        if (this.args.events is not None):
            [[this.events.add(str(e)) for e in l] for l in this.args.events]

        if (not this.args.builder):
            logging.debug("No build specified. Assuming build pipeline is written in config.")


    #Override of eons.Executor method. See that class for details
    def UserFunction(this, **kwargs):
        super().UserFunction(**kwargs)
        if (this.Execute(this.args.builder, this.args.path, this.Fetch('build_in', default="build"), this.events, **this.extraArgs)):
            logging.info("Build process complete!")
        else:
            logging.info("Build failed.")


    #Run a build script.
    #RETURNS whether or not the build was successful.
    def Execute(this, build, path, build_in, events, **kwargs):
        if (not build):
            builder = Builder("EMPTY")
        else:
            builder = this.GetRegistered(build, "build")
        logging.debug(f"Executing {build} in {path}/{build_in} with events {events} and additional args: {kwargs}")
        builder(executor=this, path=path, build_in=build_in, events=events, **kwargs)
        return builder.DidBuildSucceed()
