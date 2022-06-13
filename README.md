# libta
Libta is a python library for basic timed automata reachability analysis in python. Includes a wrapper for [libutap](https://github.com/UPPAALModelChecker/utap) using [cppyy](https://github.com/wlav/cppyy). This project is still a work in progress.

## Dependencies:

- [libutap](https://github.com/UPPAALModelChecker/utap) Uppaal timed automata parser
  
- [cppyy](https://github.com/wlav/cppyy) >= 1.7.1

To be able to use this library, libutap has to be built as a dynamic library for now.

### Building libutap as a dynamic library:

Clone [libutap](https://github.com/UPPAALModelChecker/utap), copy the patch from this repository to the cloned directory and apply with:

	git apply dynamic_link.patch && autoreconf -i

Then build and install with the instructions specified in libutap's repository. Note that global instruction is required for libta to be able to find libutap for now.

### Generating bindings:
The install script takes care of this, but in case of building from source, run genbinding.py

### Install libta:
Build and install libutap, then simply run:

	pip install .

### TODOs:
- Unit tests for parameter values in expressions and initial clock valuations
- Product automaton calculation
- Use python or CMake environment to automate building and installation of libutap.
- Error handling, prevent crashing of the Python kernel completely
