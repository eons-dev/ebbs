import os
import logging
import eons
from pathlib import Path
from .Exceptions import *

class EBBS(eons.Executor):

	def __init__(this, name="Eons Basic Build System", descriptionStr="A hackable build system for all builds!"):
		super().__init__(name, descriptionStr)
		# this.RegisterDirectory("ebbs")

	# Register included files early so that they can be used by the rest of the system.
	# If we don't do this, we risk hitting infinite loops because modular functionality relies on these modules.
	# NOTE: this method needs to be overridden in all children which ship included Functors, Data, etc. This is because __file__ is unique to the eons.py file, not the child's location.
	def RegisterIncludedClasses(this):
		super().RegisterIncludedClasses()
		includePaths = [
			'build',
		]
		for path in includePaths:
			this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath(path)))


	#Configure class defaults.
	#Override of eons.Executor method. See that class for details
	def Configure(this):
		super().Configure()

		this.defaultBuildIn = "build"
		this.defaultConfigFile = "config"
		this.defaultPackageType = "build"
		this.defaultPrefix = "build" # DEPRECATED


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

		this.parsedArgs.path = os.getcwd() #used to be arg; now we hard code
		this.rootPath = str(Path(this.parsedArgs.path).resolve())

		this.events = set()
		if (this.parsedArgs.events is not None):
			[[this.events.add(str(e)) for e in l] for l in this.parsedArgs.events]

			if (not this.parsedArgs.builder):
				logging.debug("No build specified. Assuming build pipeline is written in config.")


	def WarmUpFlow(this, flow):
		flow.WarmUp(executor=this, path=this.parsedArgs.path, build_in=this.defaultBuildIn, events=this.events, **this.extraArgs)


	#Override of eons.Executor method. See that class for details
	def InitData(this):
		if ('build_in' in this.extraArgs):
			this.defaultBuildIn = this.extraArgs.pop('build_in')
		else:
			this.defaultBuildIn = this.Fetch('build_in', default="build")
	
		this.rootPath = Path(this.FetchWithout(['environment'], 'path', default='../')).resolve() #ebbs is usually called from a build folder in a project, i.eons. .../build/../ = /


	#Override of eons.Executor method. See that class for details
	def Function(this):
		super().Function()
		build = this.Fetch('build', default="default")
		return this.Build(build, this.parsedArgs.path, this.defaultBuildIn, this.events, **this.extraArgs)

	#Run a build script.
	#RETURNS whether or not the build was successful.
	def Build(this, build, path, build_in, events, **kwargs):
		if (not build):
			build = "default"

		# prettyPath = str(Path(path).joinpath(build_in).resolve())
		# logging.debug(f"Building {build} in {prettyPath} with events {events} and additional args: {kwargs}")

		return this.Execute(build, path=path, build_in=build_in, events=events, **kwargs)
