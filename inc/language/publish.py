import os
import logging
import shutil
import requests
from ebbs import Builder
from ebbs import OtherBuildError

class publish(Builder):
    def __init__(self, name="Publisher"):
        super().__init__(name)

        self.requiredKWArgs.append("repo")
        self.requiredKWArgs.append("--version")
        # self.requiredKWArgs.append("--visibility") # this is optional. Defaults to private

        self.supportedProjectTypes = [] #all

    def PreBuild(self, **kwargs):
        self.repo = kwargs.get("repo")
        if (not len(self.repo)):
            raise OtherBuildError(f'Repo credentials required to publish package')

        self.packageVisibility = 'private'
        if ("--visibility" in kwargs):
            self.packageVisibility = kwargs.get("--visibility")

        self.packageType = ''
        if ("--package-type" in kwargs):
            self.packageType = kwargs.get("--package-type")

        self.desciption = ''
        if ("--description" in kwargs):
            self.description = kwargs.get("--description")

        nameComponents = [self.projectType, self.projectName]
        if (self.packageType):
            nameComponents.append(self.packageType)

        self.packageName = '_'.join(nameComponents)

        self.targetFileName = f'{self.packageName}.zip'
        self.targetFile = os.path.join(self.repo['store'], self.targetFileName)

        self.requestData = {
            'package_name': self.packageName,
            'version': kwargs.get("--version"),
            'visibility': self.packageVisibility
        }
        if (self.packageType):
            self.requestData['package_type'] = self.packageType
        if (self.desciption):
            self.requestData['description'] = self.description

    # Required Builder method. See that class for details.
    def Build(self):
        logging.debug("Creating archive")
        if (os.path.exists(self.targetFile)):
            os.remove(self.targetFile)

        shutil.make_archive(self.targetFile[:-4], 'zip', self.buildPath)
        logging.debug("Archive created")

        logging.debug("Uploading archive to repository")
        files = {
            'package': open(self.targetFile, 'rb')
        }
        logging.debug(f'Request data: {self.requestData}')
        packageQuery = requests.post(f"{self.repo['url']}/publish", auth=requests.auth.HTTPBasicAuth(self.repo['username'], self.repo['password']), data=self.requestData, files=files)

        logging.debug(f'''Request sent
Response: {packageQuery.status_code}
URL: {packageQuery.request.url}
Headers: {packageQuery.request.headers}
Content: {packageQuery.content.decode('ascii')}
''')

        if (packageQuery.status_code != 200):
            logging.error(f'Failed to publish {self.projectName}')
            raise OtherBuildError(f'Failed to publish {self.projectName}')

        logging.info(f'Successfully published {self.projectName}')