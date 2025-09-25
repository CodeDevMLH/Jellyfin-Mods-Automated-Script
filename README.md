# Jellyfin-Mods-Automated-Script
### File Manipulation Tool (for but not only Jellyfin Web)

This Python script is designed to automate the process of copying and modifying files and directories based on rules defined in a YAML configuration file.

It's main intention is the ability to automate the modifying process of the Jellyfin web directory after every new release (take a look at [CodeDevMLH/Jellyfin-Seasonals](https://github.com/CodeDevMLH/Jellyfin-Seasonals) or [BobHasNoSoul-jellyfin-mods](https://github.com/BobHasNoSoul/jellyfin-mods)).

Below is an overview of its main functionality and usage:

## Table of Contents
- [Jellyfin-Mods-Automated-Script](#jellyfin-mods-automated-script)
    - [File Manipulation Tool (for but not only Jellyfin Web)](#file-manipulation-tool-for-but-not-only-jellyfin-web)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Configuration File](#configuration-file)
    - [Simple example yaml](#simple-example-yaml)
    - [Running the Script](#running-the-script)

---

## Features

1. **Configuration Loading**:
   - Reads a YAML configuration file specified as a command-line argument.
   - Validates and parses the configuration to extract copy and modification rules.

2. **Directory Management**:
   - Ensures the existence of a specified destination directory where all operations will take place.

3. **File and Directory Copying**:
   - Supports multiple copy modes:
     - **Replace**: Overwrites existing files or directories in the destination.
     - **Update**: Copies only if the source file is newer than the destination file.
   - Handles both files and directories.
   - Generates warnings and error messages if issues occur (e.g., source file not found).

4. **File Modifications**:
   - Supports modifications to text files based on rules defined in the configuration file.
   - Operations include:
     - Inserting text before or after specific content.
     - Replacing old text with new text.
   - Recursively applies changes to files matching specified patterns in the destination directory.

5. **Error and Warning Tracking**:
   - Tracks the number of successful operations, errors, and warnings for both copy and modification processes.

6. **User Feedback**:
   - Provides detailed, color-coded output to indicate the progress and results of operations.
   - ANSI escape sequences are used for colored terminal messages.


## Usage

### Prerequisites
- Ensure Python 3.x is installed.
- Install the PyYAML-Library (pip install pyyaml)

### Configuration File
Create a YAML file with the following sections:
- `destination_directory`: Path to the target directory.
- `copy_rules`: List of copy instructions (source paths, modes, and targets).
- `modification_rules`: List of modification instructions (patterns, insertion, and replacement rules).

### Simple example yaml
For more details take a further look into config-TEMPLATE.yaml
```yaml
destination_directory: "./web"  # Target directory for operations

copy_rules:
  - sources:  # Files/folders to copy
      - './source_folder' # Entire folder located from where you called the script
      - source: "./src/file.js"
        target: "./dist/file.js"
    mode: "replace"  # Options: replace, update

    - sources:
          - './source_folder'  # Entire folder
          - './specific_file.txt'  # Single file
          - './source_directory/*.js'  # All JS files
        mode: 'copy'  # Copies files/folders located from where you called the script

modification_rules:
  - file_pattern: "*.js"  # Files to modify (supports regex)
    insert_rules:
      - after_text: "search text"  # Insert after this text
        insert_text: "new content"
      - before_text: "target"  # Insert before this text
        insert_text: "new content"
    replace_rules:
      - old_text: "original"  # Text to replace
        new_text: "replacement"
```

### Running the Script
Run the script by providing the path to your YAML configuration file, using the following command:
```bash
python script.py <path_to_config_file>
```
So for example:
```bash
python customize-WebUI.py config.yaml
```
