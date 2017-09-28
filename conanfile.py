from conans import ConanFile, tools, VisualStudioBuildEnvironment
from conans.tools import cpu_count, os_info, SystemPackageTool
from conans.util.files import load
from conans.errors import ConanException
import os, sys
from distutils.spawn import find_executable

class QwtConan(ConanFile):
    name = "Qwt"
    version = "6.1.3"
    license = "Qwt License, Version 1.0 http://qwt.sourceforge.net/qwtlicense.html"
    url = "https://github.com/kenfred/conan-qwt"
    description = "The Qwt library contains GUI Components and utility classes which are " \
                    "primarily useful for programs with a technical background. Beside a " \
                    "framework for 2D plots it provides scales, sliders, dials, compasses, " \
                    "thermometers, wheels and knobs to control or display values, arrays, or " \
                    "ranges of type double."
    settings = "os", "compiler", "build_type", "arch"
    
    options = {
        "shared": [True, False],
        "plot": [True, False],
        "widgets": [True, False],
        "svg": [True, False],
        "opengl": [True, False],
        "mathml": [True, False],
        "designer": [True, False],
        "examples": [True, False],
        "playground": [True, False]
    }
    default_options = "shared=True", "plot=True", "widgets=True", "svg=True", "opengl=True", \
                        "mathml=False", "designer=True", "examples=False", "playground=False"

    build_requires = "Qt/5.8.0@kenfred/testing"               

    def source(self):
        zip_name = "qwt-%s.zip" % self.version if sys.platform == "win32" else "qwt-%s.tar.gz" % self.version
        url = "https://sourceforge.net/projects/qwt/files/qwt/%s/%s" % (self.version, zip_name)
        self.output.info("Downloading %s..." % url)
        tools.download(url, zip_name)
        tools.unzip(zip_name)
        os.unlink(zip_name)

    def build(self):
        qwt_path = "qwt-%s" % self.version
        qwt_config_file_path = os.path.join(qwt_path, "qwtconfig.pri" )
        qwt_config = load(qwt_config_file_path)
        qwt_config += "\nQWT_CONFIG %s= QwtDLL" % ("+" if self.options.shared else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtPlot" % ("+" if self.options.plot else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtWidgets" % ("+" if self.options.widgets else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtSvg" % ("+" if self.options.svg else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtOpenGL" % ("+" if self.options.opengl else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtMathML" % ("+" if self.options.mathml else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtDesigner" % ("+" if self.options.designer else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtExamples" % ("+" if self.options.examples else "-")
        qwt_config += "\nQWT_CONFIG %s= QwtPlayground" % ("+" if self.options.playground else "-")
        qwt_config = qwt_config.encode("utf-8")
        with open(qwt_config_file_path, "wb") as handle:
            handle.write(qwt_config)

        qwt_build_string = "CONFIG += %s" % ("release" if self.settings.build_type=="Release" else "debug")
        qwt_build_file_path = os.path.join(qwt_path, "qwtbuild.pri")
        tools.replace_in_file(qwt_build_file_path, "CONFIG           += debug_and_release", qwt_build_string)
        tools.replace_in_file(qwt_build_file_path, "CONFIG           += build_all", "")
        tools.replace_in_file(qwt_build_file_path, "CONFIG           += release", qwt_build_string)

        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                self._build_msvc()
            else:
                raise ConanException("Not yet implemented for this compiler")
        else:
            raise ConanException("Not yet implemented for this compiler")

    def _build_msvc(self, args = ""):
        build_command = find_executable("jom.exe")
        if build_command:
            build_args = ["-j", str(cpu_count())]
        else:
            build_command = "nmake.exe"
            build_args = []

        self.output.info("Using '%s %s' to build" % (build_command, " ".join(build_args)))

        env_build = VisualStudioBuildEnvironment(self)

        with tools.environment_append(env_build.vars):
            vcvars = tools.vcvars_command(self.settings)
            self.run("cd qwt-%s && %s && qmake -r qwt.pro" % (self.version, vcvars))
            self.run("cd qwt-%s && %s && %s %s" % (self.version, vcvars, build_command, " ".join(build_args)))

    def package(self):
        self.copy("*.h", dst="include", src="qwt")
        self.copy("*qwt.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["qwt"]
