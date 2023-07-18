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


	#Override of eons.Executor method. See that class for details
	def AddArgs(this):
		super().AddArgs()
		this.argparser.add_argument('-b','--build', type = str, metavar = 'cpp', help = 'script to use for building', dest = 'builder')
		this.argparser.add_argument('-e','--event', type = str, action='append', nargs='*', metavar = 'release', help = 'what is going on that triggered this build?', dest = 'events')


	#Override of eons.Executor method. See that class for details
	def ParseArgs(this):
		super().ParseArgs()

		this.parsedArgs.path = os.getcwd() #used to be arg; now we hard code

		this.events = set()
		if (this.parsedArgs.events is not None):
			[[this.events.add(str(e)) for e in l] for l in this.parsedArgs.events]


	def WarmUpFlow(this, flow):
		flow.WarmUp(executor=this, path=this.rootPath, build_in=this.defaultBuildIn, events=this.events, **this.extraArgs)


	#Override of eons.Executor method. See that class for details
	def InitData(this):
		if ('build_in' in this.extraArgs):
			this.Set('defaultBuildIn', this.extraArgs.pop('build_in'), False)
		else:
			this.Set('defaultBuildIn', this.Fetch('build_in', default="build"), False)
	
		this.Set(
			'rootPath',
			str(Path(this.FetchWithout(['environment'], 'path', default='../')).resolve()), #ebbs is usually called from a build folder in a project, i.eons. .../build/../ = /
			False
		)
		this.Set('buildPath', str(Path('./').joinpath(this.defaultBuildIn).resolve()), False)


	#Override of eons.Executor method. See that class for details
	def Function(this):
		super().Function()
		if (this.parsedArgs.builder):
			build = this.parsedArgs.builder
		else:
			build = this.FetchWithout(['environment'], 'build', default="default")

		pathToBuilder = build.split('/')
		build = pathToBuilder[-1]
		this.RegisterAllClassesInDirectory(
			Path('./').joinpath('/'.join(pathToBuilder[:-1])),
			recurse = False
		)
		
		buildIn = os.path.relpath(this.buildPath, this.rootPath)

		args = this.extraArgs.copy()
		args['build'] = build
		args['path'] = this.rootPath
		args['build_in'] = buildIn
		args['events'] = this.events

		logging.info(f"{this.name} building{args}")

		return this.Build(**args)


	#Run a build script.
	#RETURNS whether or not the build was successful.
	def Build(this, build, path, build_in, events, **kwargs):
		if (not build):
			build = "default"

		# prettyPath = str(Path(path).joinpath(build_in).resolve())
		# logging.debug(f"Building {build} in {prettyPath} with events {events} and additional args: {kwargs}")

		return this.Execute(build, path=path, build_in=build_in, events=events, **kwargs)
