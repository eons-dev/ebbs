import os
import logging
from ebbs.Builder import Builder

#Class name is what is used at cli, so we defy convention here in favor of ease-of-use.
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

    #Required Builder method. See that class for details.
    def Build(self):
        os.chdir(self.buildPath)
        self.GenCMake()
        self.CMake()
        self.Make()

    def get_cxx_files (self, directory, seperator=" "):
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
        #Write our cmake file
        cmake_open = '''
cmake_minimum_required (VERSION 3.1.1)
set (CMAKE_CXX_STANDARD 11)
include_directories(${CMAKE_SOURCE_DIR}/../inc)
'''

        cmake_file = open("CMakeLists.txt", "w")
        cmake_file.write(f"{cmake_open}\n")
        cmake_file.write(f"project ({self.projectName})\n")

        if (self.projectType == "bin" or self.projectType == "test"):
            logging.info("Addind binary specific code")
            
            cmake_file.write (f"add_executable ({self.projectName} {self.get_cxx_files ('../src')})\n")
            cmake_file.write ('''
include_directories(${CMAKE_SOURCE_DIR}/../lib)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
''')
            cmake_file.write (f"target_link_directories({self.projectName} " + "PUBLIC ${CMAKE_SOURCE_DIR}/../lib)\n")
            cmake_file.write (f"target_link_libraries({self.projectName} Threads::Threads {self.get_libs('../lib')})")

        if (self.projectType == "lib"):
            logging.info("Addind library specific code")

            #TODO: support windows install targets
            src_path = "/usr/local/lib"
            inc_path = "/usr/local/include/{self.projectName}"

            cmake_file.write (f"add_library ({self.projectName} STATIC {self.get_cxx_files('../src')})\n")
            cmake_file.write (f"set_target_properties({self.projectName} PROPERTIES PUBLIC_HEADER \"{self.get_cxx_files('../inc',';')}\")\n")
            cmake_file.write (f"INSTALL(TARGETS {self.projectName} LIBRARY DESTINATION {src_path} PUBLIC_HEADER DESTINATION {inc_path})\n")

        cmake_close = '''
'''
        cmake_file.write (f"{cmake_close}")

    def CMake(self):
        self.RunCommand("cmake .")

    def Make(self):
        self.RunCommand("make")

