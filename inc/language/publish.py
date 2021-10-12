import os
import logging
import shutil
import requests
from ebbs import Builder
from ebbs import OtherBuildError

class publish(Builder):
    def __init__(self, name="Wordpress Plugin Builder"):
        super().__init__(name)

        self.requiredKWArgs.append("repo")
        self.requiredKWArgs.append("--version")
        self.requiredKWArgs.append("--visibility")

        self.supportedProjectTypes = [] #all

    def PreBuild(self, **kwargs):
        self.repo = kwargs.get("repo")
        if (not len(self.repo)):
            raise OtherBuildError(f'Repo credentials required to publish package')

        self.targetFileName = f'{self.projectName}.zip'
        self.targetFile = os.path.join(self.rootPath, self.targetFileName)

        self.packageName = f'{self.projectType}_{self.projectName}'

        self.requestData = {
            #user and pass included in POST, rather than requests.auth.HTTPBasicAuth, because of a limitation in the Infrastructure API.
            'username': self.repo['username'],
            'password': self.repo['password'],
            'package_name': self.packageName,
            'version': kwargs.get("--version"),
            'visibility': kwargs.get("--visibility")
        }

    # Required Builder method. See that class for details.
    def Build(self):
        logging.debug("Creating archive")
        if (os.path.exists(self.targetFile)):
            os.remove(self.targetFile)

        shutil.make_archive(self.targetFile[:-4], 'zip', self.buildPath)
        # archive = ZipFile(self.targetFile, 'w')
        # for dirname, subdirs, files in os.walk(self.workingPath):
        #     archive.write(dirname)
        #     for filename in files:
        #         archive.write(os.path.join(dirname, filename))
        # archive.close()
        logging.debug("Achive created")

        logging.debug("Uploading archive to repository")
        files = {
            'package': open(self.targetFile, 'rb')
        }
        logging.debug(f'Request data: {self.requestData}')
        packageQuery = requests.post(f'{self.repo["url"]}/publish', data=self.requestData, files=files)

        if (packageQuery.status_code != 200):
            logging.error(f'Failed to publish {self.projectName}')
            raise OtherBuildError(f'Failed to publish {self.projectName}')

        logging.info(f'Successfully published {self.projectName}')