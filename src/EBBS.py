import os
import logging
import eons as e
from .Exceptions import *

class EBBS(e.Executor):

    def __init__(self):
        super().__init__(name="eons Basic Build System", descriptionStr="A hackable build system for all languages!")

    def Configure(self):
        super().Configure()
        self.RegisterDirectory("language")
        self.RegisterDirectory("inc/language")
        self.RegisterDirectory("ebbs/inc/language")
        self.defaultRepoDirectory = "./ebbs/"

    #Override of eons.Executor method. See that class for details
    def RegisterAllClasses(self):
        super().RegisterAllClasses()
        self.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "language"))

    #Override of eons.Executor method. See that class for details
    def AddArgs(self):
        super().AddArgs()
        self.argparser.add_argument('dir', type=str, metavar='/project/build', help='path to build folder', default='.')
        self.argparser.add_argument('-l','--language', type=str, metavar='cpp', help='language of files to build', dest='lang')

    #Override of eons.Executor method. See that class for details
    def ParseArgs(self):
        super().ParseArgs()

        if (not self.args.lang):
            self.ExitDueToErr("You must specify a language.")

    #Override of eons.Executor method. See that class for details
    def UserFunction(self, **kwargs):
        super().UserFunction(**kwargs)
        self.Build()

    #Build things!
    def Build(self):
        builder = self.GetRegistered(self.args.lang, "build")

        repoData = {}
        if (hasattr(self.args, 'repo_store')):
            repoData['store'] = self.args.repo_store
        if (hasattr(self.args, 'repo_url')):
            repoData['url'] = self.args.repo_url
        if (hasattr(self.args, 'repo_username')):
            repoData['username'] = self.args.repo_username
        if (hasattr(self.args, 'repo_password')):
            repoData['password'] = self.args.repo_password

        builder(executor=self, dir=self.args.dir, repo=repoData, **self.extraArgs)

