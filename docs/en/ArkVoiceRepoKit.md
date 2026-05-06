Additional Documentation for ArkUnpacker

# About the ArkVoice Extraction and Sorting Tool

## Overview

[ArkVoice](https://github.com/isHarryh/Ark-Voice) is an Arknights voice repository created by the author, containing operator voice files in multiple languages from the game. The repository uses OGG encoding format with a segmented merging method for storage. The "ArkVoice Extraction and Sorting Tool" is designed to assist in updating this repository. Its sub-features include:

- Voice Extraction: Automatically extracts voice data as WAV files from the game's original resource files.
- Sorting and Merging: Merges segmented WAV files and re-encodes them into compressed OGG files.
- Dataset Generation: Writes detailed metadata of the voices in the ArkVoice repository into a JSON dataset.

## Usage

1. Follow the instructions in the README to complete [Resource Preparation](../README-en.md#1-asset-preparation). For the required resource folders, refer to the folder names indicated within the program. Place the prepared resource folders directly in the **program directory**.
2. Launch the program, enter the "ArkVoice Extraction and Sorting Tool" interface, and follow the prompts to complete the process. Afterward, the required files (and folders) for the ArkVoice repository will be generated in the program directory.
3. Clone the ArkVoice repository, replace its original contents with the newly generated files (and folders), and perform commit and push operations to update the repository, completing the voice library update.