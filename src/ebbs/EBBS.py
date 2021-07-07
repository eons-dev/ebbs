import os
import logging
import argparse
from esam.SAM import SAM
from esam.SelfRegistering import RegisterAllClassesInDirectory

class EBBS(SAM):

    def RegisterAllClasses(self):
        RegisterAllClassesInDirectory(os.path.join(os.path.dirname(os.path.abspath(__file__)), "language"))

    def AddArgs(self):
        self.argparser.add_argument('-d','--directory', type = str, metavar = '/project/build', help = 'path to build folder', dest = 'dir', default = '.')
        self.argparser.add_argument('-l','--language', type = str, metavar = 'cpp', help = 'language of files to build', dest = 'lang')

    def ParseArgs(self):
        self.args = self.argparser.parse_args()

        if (not self.args.lang):
            self.ExitDueToErr("You must specify a language.")

    def UserFunction(self, **kwargs):
        self.ParseArgs()
        self.Build()

    def Build(self):
        builder = self.GetFunctor(self.args.lang)
        builder(dir = self.args.dir)