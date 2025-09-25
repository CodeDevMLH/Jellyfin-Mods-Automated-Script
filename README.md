# Jellyfin-Mods-Automated-Script
### File Manipulation Tool (for but not only Jellyfin Web)

This Python script is designed to automate the process of copying and modifying files and directories based on rules defined in a YAML configuration file.

It's main intention is the ability to automate the modifying process of the Jellyfin web directory after every new release (take a look at [CodeDevMLH/Jellyfin-Seasonals](https://github.com/CodeDevMLH/Jellyfin-Seasonals), [CodeDevMLH/Jellyfin-Featured-Content-Bar](https://github.com/CodeDevMLH/Jellyfin-Featured-Content-Bar) or [BobHasNoSoul-jellyfin-mods](https://github.com/BobHasNoSoul/jellyfin-mods)).

Below is an overview of its main functionality and usage:

- [Jellyfin-Mods-Automated-Script](#jellyfin-mods-automated-script)
    - [File Manipulation Tool (for but not only Jellyfin Web)](#file-manipulation-tool-for-but-not-only-jellyfin-web)
  - [Features](#features)
  - [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Configuration File](#configuration-file)
    - [Simple example yaml](#simple-example-yaml)
    - [Running the Script](#running-the-script)
    - [Regex Markers Cheat Sheet](#regex-markers-cheat-sheet)

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
     - **Update**: Copies only if the source file is newer than the destination file (files only).
     - **Copy**: Creates directories, if already exsisting, only copies non existing files in that folder
   - Handles both files and directories.
   - Generates warnings and error messages if issues occur (e.g., source file not found).

4. **File Modifications**:
   - Supports modifications to text files based on rules defined in the configuration file.
   - Operations include:
     - Inserting text before or after specific content.
     - Replacing old text with new text.
   - NEW: Regex support (prefix markers with `re:`) for `before_text`, `after_text`, and `old_text` to handle dynamical hashes (e.g. Jellyfin assets)
   - Recursively applies changes to files matching specified patterns in the destination directory.

5. **Error and Warning Tracking**:
   - Tracks the number of successful operations, errors, and warnings for both copy and modification processes.

6. **User Feedback**:
   - Provides detailed, color-coded output to indicate the progress and results of operations.
   - ANSI escape sequences are used for colored terminal messages.


## Usage

### Prerequisites
- Ensure Python 3.x is installed
- Install dependencies:
  - via file: `pip install -r requirements.txt`
  - Or manually: `pip install PyYAML`

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
      - after_text: "search text"  # Insert after this exact (plain) text
        insert_text: "new content"
      - before_text: "target"  # Insert before this exact (plain) text
        insert_text: "new content"
      - before_text: 're:<link href="main\.jellyfin\.[0-9a-z]+\.css?[0-9a-z]+" rel="stylesheet">'  # Regex variant
        insert_text: "<script>// injected</script>"
    replace_rules:
      - old_text: "original"  # Plain substring replacement
        new_text: "replacement"
      - old_text: 're:<link href="main\.jellyfin\.[0-9a-z]+\.css?[0-9a-z]+" rel="stylesheet">' # regex variant
        new_text: 'somthing new (without regex!!!)'
```

### Running the Script
Run the script by providing the path to your YAML configuration file, using the following command:
```bash
python customize-WebUI.py <path_to_config_file>
```
So for example if config is in same folder:
```bash
python customize-WebUI.py config.yaml
```

### Regex Markers Cheat Sheet
Prefix any marker with `re:` to interpret it as a Python Regex (DOTALL activ):

Examples:
```
before_text: 're:<link href="main\\.jellyfin\\.[^"]+\\.css[^"]*" rel="stylesheet">'
after_text:  're:data-backdroptype="movie,series,book">'
old_text:    're:this\\.get\("libraryPageSize",!1\),10\);return 0===t\?0:t\|\|100}'
```

Notes:
1. Properly escape backslashes (YAML + Regex!)
2. The first match will be used (count=1 for replacement/insertion)
3. Idempotency: The script checks whether the insertion or replacement text already exists to avoid duplicates