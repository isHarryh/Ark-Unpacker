Additional Documentation for ArkUnpacker

# About the ArkModels Extraction and Sorting Tool

## Overview

[ArkModels](https://github.com/isHarryh/Ark-Models) is a Spine model repository for Arknights created by the author, containing a subset of Spine models from the game. The "ArkModels Extraction and Sorting Tool" is designed to assist in updating this repository. Its sub-features include:

- Model Extraction: Automatically extracts files that may be required by the ArkModels repository from the game's original resource files.
- File Sorting: Further filters the extracted files and organizes them according to the naming and structural requirements of the ArkModels repository.
- Dataset Generation: Decodes character data from FlatBuffers-encoded resource files, then writes information for each model in the ArkModels repository into a JSON dataset.

## Usage

1. Follow the instructions in the README to complete [Resource Preparation](../../README-en.md#1-asset-preparation). For the required resource folders, refer to the folder names indicated within the program. Place the prepared resource folders directly in the **program directory**.
2. Launch the program, enter the "ArkModels Extraction and Sorting Tool" interface, and follow the prompts to complete the process. Afterward, the required files (and folders) for the ArkModels repository will be generated in the program directory.
3. Clone the ArkModels repository, replace its original contents with the newly generated files (and folders), and perform commit and push operations to update the repository.