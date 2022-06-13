from setuptools import find_packages, setup
from distutils.command.build import build
import os
import sys
import subprocess

src_dir = os.path.dirname(os.path.abspath(__file__))
class build_binding(build):
    def run(self):
        cmd = ["python3", os.path.join(src_dir, "genbinding.py")]
        if subprocess.call(cmd) != 0:
            sys.exit(-1)
        build.run(self)

setup(
    name="libta",
    version="0.0.1",
    description="Basic timed automata reachability analysis tool",
    url="https://github.com/eaydingol/libta",
    author="Burak Köroğlu",
    author_email="koroglu.burak@metu.edu.tr",
    license="GPL3",
    install_requires=[
        "cppyy>=1.7.1",
    ],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    cmdclass = {
      'build': build_binding
    },
    package_data = {'libta':['rfiles/*']}
)
