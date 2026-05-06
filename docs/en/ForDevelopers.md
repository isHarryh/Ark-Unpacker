Additional Documentation for ArkUnpacker

# Developer Guide

This document describes the preparation steps and procedures required to run the source code or contribute to the project.

## Dependencies

1. **Python:** This project requires a **Python 3.9–3.12** runtime environment. You can [download it here](https://www.python.org/downloads).  
2. **IDE:** The recommended integrated development environment (IDE) is **VS Code**. You can [download it here](https://code.visualstudio.com).  
    > Recommended VS Code extensions:  
    > - [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)  
    > - [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)  
3. **Poetry:** This project uses **Poetry 2** for dependency management. You can [view the documentation here](https://python-poetry.org/docs). All dependencies will be installed in Poetry’s virtual environment.  
    > Quick installation steps for Poetry:  
    > 1. Run `pip install pipx` in the command line to install pipx (a CLI tool manager);  
    > 2. Run `pipx install poetry` to install Poetry, then run `pipx ensurepath` to configure PATH;  
    > 3. Run `poetry -v` to verify the installation (this may require a new terminal session).  
4. **Submodule:** This project uses the [ArkFBSPy](https://github.com/isHarryh/Ark-FBS-Py) module for FlatBuffers data decoding. It is included in the repository as a Git submodule.  

## Project Setup

1. Clone the repository using Git, then open the project folder in your IDE.  
    > Since this repository uses Git submodules:  
    > - Run `git submodule update --init --recursive` to initialize submodules.  
    > - When the remote submodules are updated, run `git submodule update --remote --recursive` to update them locally.  
2. In VS Code, run the `Project Setup` terminal task (it usually runs automatically when opening the project), or execute `poetry install` in the command line. This will activate Poetry and install dependencies in the virtual environment. The main dependencies can be found in `pyproject.toml`.  
3. Select the Python interpreter from the Poetry virtual environment (run `poetry env info` to get the interpreter path).  
4. In VS Code, run `Python: ArkUnpacker` to start debugging the main program.  

## Testing and Build

1. **Testing:** Run the `Test` terminal task in VS Code, or execute the `Test.py` script directly. This will simulate unpacking using the included test game resource files (located in the `test/res` directory). After testing, a runtime record file `test/rt.json` will be generated.  
2. **Build:** Run the `Build Dist` terminal task in VS Code, or execute the `Build.py` script directly. This will use PyInstaller to generate distributable files in the `build/dist` directory of the project.  