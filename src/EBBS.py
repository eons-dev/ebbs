import os
import logging
import argparse
import requests
import eons as e
from zipfile import ZipFile
from distutils.dir_util import mkpath
from .Exceptions import *

class EBBS(e.Executor):

    def __init__(self):
        super().__init__(name="eons Basic Build System", descriptionStr="A hackable build system for all languages!")

        self.RegisterDirectory("language")
        self.RegisterDirectory("inc/language")
        self.RegisterDirectory("ebbs/inc/language")

    #Override of eons.Executor method. See that class for details
    def RegisterAllClasses(self):
        super().RegisterAllClasses()
        self.RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "language"))

    #Override of eons.Executor method. See that class for details
    def AddArgs(self):
        super().AddArgs()
        self.argparser.add_argument('dir', type = str, metavar = '/project/build', help = 'path to build folder', default = '.')
        self.argparser.add_argument('-l','--language', type = str, metavar = 'cpp', help = 'language of files to build', dest = 'lang')
        self.argparser.add_argument('--repo-store', type=str, default='./ebbs/inc/language', help='file path for storing downloaded packages', dest = 'store')
        self.argparser.add_argument('--repo-url', type = str, default='https://api.infrastructure.tech/v1/package', help = 'package repository for additional languages', dest = 'url')
        self.argparser.add_argument('--repo-username', type = str, help = 'username for http basic auth', dest = 'username')
        self.argparser.add_argument('--repo-password', type = str, help = 'password for http basic auth', dest = 'password')

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
        try:
            builder = self.GetRegistered(self.args.lang)
        except:
            logging.debug(f'Builder for {self.args.lang} not found. Trying to download from repository.')
            try: #again
                self.DownloadPackage(f'build_{self.args.lang}')
                builder = self.GetRegistered(self.args.lang)
            except Exception as e:
                logging.error(f'Could not find builder for {self.args.lang}: {e}')
                raise OtherBuildError(f'Could not get builder for {self.args.lang}')
                return #just for extra safety.

        repoData = {}
        if (self.args.store and self.args.url and self.args.username and self.args.password):
            repoData = {
                'store': self.args.store,
                'url': self.args.url,
                'username': self.args.username,
                'password': self.args.password
            }

        builder(dir = self.args.dir, repo = repoData, **self.extraArgs)

    #Attempts to download the given package from the repo url specified in calling args.
    #Will refresh registered builders upon success
    #RETURNS void
    #Does not guarantee new builders are made available; errors need to be handled by the caller.
    def DownloadPackage(self, packageName):

        url = f'{self.args.url}/download?package_name={packageName}'

        auth = None
        if self.args.username and self.args.password:
            auth = requests.auth.HTTPBasicAuth(self.args.username, self.args.password)

        packageQuery = requests.get(url, auth=auth)

        if (packageQuery.status_code != 200 or not len(packageQuery.content)):
            logging.error(f'Unable to download {packageName}')
            #TODO: raise error?
            return #let caller decide what to do next.

        if (not os.path.exists(self.args.store)):
            logging.debug(f'Creating directory {self.args.store}')
            mkpath(self.args.store)

        packageZip = os.path.join(self.args.store, f'{packageName}.zip')

        logging.debug(f'Writing {packageZip}')
        open(packageZip, 'wb+').write(packageQuery.content) #TODO: close?
        if (not os.path.exists(packageZip)):
            logging.error(f'Failed to create {packageZip}')
            return

        logging.debug(f'Extracting {packageZip}')
        ZipFile(packageZip, 'r').extractall(f'{self.args.store}') #TODO: close?

        logging.debug(f'Registering classes in {self.args.store}')
        self.RegisterAllClassesInDirectory(self.args.store)