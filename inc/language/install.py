import os
import logging
import shutil
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath
from ebbs import Builder
from ebbs import OtherBuildError

class install(Builder):
    def __init__(self, name="Install a package"):
        super().__init__(name)

        #we don't use the local system
        self.supportedProjectTypes = []

        self.installSrcPath = "./"
        self.installIncPath = "./"
        self.installBinPath = "./"

    #Optional Builder method. See that class for details.
    def PreBuild(self, **kwargs):
        self.repo = kwargs.get("repo")
        if (not len(self.repo)):
            raise OtherBuildError('Repo credentials required to know where saved packages end up!')

        if (self.os in ['Linux']):
            self.installSrcPath = "/usr/local/lib"
            self.installIncPath = "/usr/local/include/"
            self.installBinPath = "/usr/bin"
        #TODO: support windows & mac

        #rewrite builder code for our own uses.
        details = self.buildPath.split("_")
        self.projectType = details[0]
        if (len(details) > 1):
            self.projectName = '_'.join(details[1:])

    #Required Builder method. See that class for details.
    def Build(self):
        self.executor.DownloadPackage(self.projectName)
        packagePath = os.path.join(self.repo.store, self.projectName)
        if (not os.path.isdir(packagePath)):
            raise OtherBuildError('Couldn\'t find downloaded package')
        os.chdir(packagePath)

        if (self.projectType in ['lib']):
            for thing in os.listdir('.'):
                thingPath = os.path.abspath(thing)
                if os.path.isfile(thingPath):
                    copy_file(thingPath, self.installSrcPath)
                elif os.path.isdir(thingPath):
                    copy_tree(thingPath, self.installIncPath)

        if (self.projectType in ['bin']):
            for thing in os.listdir('.'):
                thingPath = os.path.abspath(thing)
                if os.path.isfile(thingPath):
                    copy_file(thingPath, self.installBinPath)
                #ignore folders.