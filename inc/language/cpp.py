import os
import logging
import shutil
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath
from ebbs import Builder


# Class name is what is used at cli, so we defy convention here in favor of ease-of-use.
class cpp(Builder):
    def __init__(self, name="C++ Builder"):
        super().__init__(name)

        self.supportedProjectTypes.append("lib")
        self.supportedProjectTypes.append("bin")
        self.supportedProjectTypes.append("test")

        self.valid_cxx_extensions = [
            ".cpp",
            ".h"
        ]
        self.valid_lib_extensions = [
            ".a",
            ".so"
        ]

    # Required Builder method. See that class for details.
    def Build(self):
        self.buildPath = os.path.join(self.rootPath, self.buildPath)
        if (os.path.exists(self.buildPath)):
            logging.info(f"DELETING {self.buildPath}")
            shutil.rmtree(self.buildPath)
        mkpath(self.buildPath)
        os.chdir(self.buildPath)
        self.packagePath = os.path.join(self.buildPath, self.projectName)
        mkpath(self.packagePath)

        logging.debug(f"Building in {self.buildPath}")
        logging.debug(f"Packaging in {self.packagePath}")

        self.GenCMake()
        self.CMake(".")
        self.Make()

        # include header files with libraries
        if (self.projectType in ["lib"]):
            copy_tree(self.incPath, self.packagePath)

    def get_cxx_files(self, directory, seperator=" "):
        ret = ""
        for root, dirs, files in os.walk(directory):
            for f in files:
                name, ext = os.path.splitext(f)
                if (ext in self.valid_cxx_extensions):
                    # logging.info(f"    {os.path.join(root, f)}")
                    ret += f"{os.path.join(root, f)}{seperator}"
        return ret[:-1]

    def get_libs(self, directory, seperator=" "):
        ret = ""
        for file in os.listdir(directory):
            if not os.path.isfile(os.path.join(directory, file)):
                continue
            name, ext = os.path.splitext(file)
            if (ext in self.valid_lib_extensions):
                ret += (f"{name[3:]}{seperator}")
        return ret[:-1]

    def GenCMake(self):
        # Write our cmake file
        cmake_open = f'''
cmake_minimum_required (VERSION 3.1.1)
set (CMAKE_CXX_STANDARD 11)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY {self.packagePath})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY {self.packagePath})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY {self.packagePath})
include_directories({self.incPath})
'''

        cmake_file = open("CMakeLists.txt", "w")
        cmake_file.write(f"{cmake_open}\n")
        cmake_file.write(f"project ({self.projectName})\n")

        if (self.projectType in ["bin", "test"]):
            logging.info("Addind binary specific code")

            cmake_file.write(f"add_executable ({self.projectName} {self.get_cxx_files(self.srcPath)})\n")
            cmake_file.write(f'''
include_directories({self.libPath})
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
''')
            cmake_file.write(f"target_link_directories({self.projectName} " + f"PUBLIC {self.libPath}))\n")
            cmake_file.write(
                f"target_link_libraries({self.projectName} Threads::Threads {self.get_libs(self.libPath)})")

        if (self.projectType in ["lib", "mod"]):
            logging.info("Adding library specific code")

            # #TODO: support windows install targets
            installSrcPath = "/usr/local/lib"
            installIncPath = "/usr/local/include/{self.projectName}"

            cmake_file.write(f"add_library ({self.projectName} SHARED {self.get_cxx_files(self.srcPath)})\n")
            cmake_file.write(
                f"set_target_properties({self.projectName} PROPERTIES PUBLIC_HEADER \"{self.get_cxx_files(self.incPath, ';')}\")\n")
            cmake_file.write(
                f"INSTALL(TARGETS {self.projectName} LIBRARY DESTINATION {installSrcPath} PUBLIC_HEADER DESTINATION {installIncPath})\n")

        cmake_close = '''
'''
        cmake_file.write(f"{cmake_close}")

        cmake_file.close()

    def CMake(self, path):
        self.RunCommand(f"cmake {path}")

    def Make(self):
        self.RunCommand("make")

