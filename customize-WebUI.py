import os
import shutil
import yaml
import re
import sys

# ANSI escape sequences for colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

# Global variable to track errors
errorList = {"copies": 0, "modifications": 0, "copyWarnings": 0, "modWarnings": 0}

# Initialize results
results = {"copies": 0, "modifications": 0}

# MARK: Load configuration
def loadConfig(configPath):
    """Load YAML configuration."""
    try:
        print(f"Loading configuration from {configPath} ...")
        with open(configPath, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        # validate configuration
        if not config:
            raise ValueError("Empty configuration file")
        
        print(f"{Colors.GREEN}Configuration loaded successfully.{Colors.RESET}")
        return config
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Configuration file not found at ./{configPath}{Colors.RESET}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"{Colors.RED}Error parsing YAML configuration: {e}{Colors.RESET}")
        sys.exit(1)
    except ValueError as e:
        print(f"{Colors.RED}Configuration error: {e}{Colors.RESET}")
        sys.exit(1)


def ensureDirectory(path):
    """Ensure that a directory exists."""
    print(f"\nChecking for or creating directory: {path}")
    os.makedirs(path, exist_ok=True)


# MARK: Copy sources
def copySources(config, destinationDirectory):
    """Copy files and folders according to copy rules."""
    print(f"{Colors.YELLOW}Starting source file & folder copy and replace process...{Colors.RESET}")
    for rule in config.get('copy_rules', []):
        for source in rule.get('sources', []):
            try:
                # Distinguish between sources with explicit target and without
                if isinstance(source, dict):
                    sourcePath = source['source']
                    
                    checkTargetPath = source['target']
                    
                    # Check for absolute paths in target and correct them if necessary
                    if os.path.isabs(checkTargetPath):
                        targetPath = os.path.normpath(os.path.join(destinationDirectory, checkTargetPath.lstrip('./')))
                        raise ValueError(f"{Colors.RED}Absolute path incorrect: {Colors.YELLOW}Corrected {checkTargetPath} to {targetPath}.{Colors.RESET}")
                    else:
                        #targetPath = os.path.join(destinationDirectory, source['target']) # old code
                        targetPath = os.path.normpath(os.path.join(destinationDirectory, checkTargetPath))
                    

                else:
                    sourcePath = source
                    #targetPath = os.path.join(destinationDirectory, os.path.basename(sourcePath)) # old code
                    targetPath = os.path.normpath(os.path.join(destinationDirectory, os.path.basename(sourcePath)))

                    # Check if source exists
                    if not os.path.exists(sourcePath):
                        raise FileNotFoundError(f"Source path does not exist: {sourcePath}")

                # Create target directory
                ensureDirectory(os.path.dirname(targetPath))

                # Copy or replace mode
                if rule.get('mode') == 'replace' and os.path.exists(targetPath):
                    print(f"Replacing existing file/folder: {targetPath}")

                    # Explicitly handle directory or file deletion
                    if os.path.isdir(targetPath):
                        shutil.rmtree(targetPath)
                    else:
                        os.remove(targetPath)

                # Update mode
                if rule.get('mode') == 'update' and os.path.exists(targetPath):
                    print(f"Checking if {sourcePath} is newer than {targetPath}")
                    srcMtime = os.path.getmtime(sourcePath)
                    destMtime = os.path.getmtime(targetPath)
                    if srcMtime <= destMtime:
                        print(f"{Colors.YELLOW}Skipping {sourcePath}: Destination is up to date{Colors.RESET}")
                        break   # Skip this source file/folder
                elif rule.get('mode') != 'update' and not os.path.exists(sourcePath):
                    print(f"{Colors.YELLOW}Should update {sourcePath} to {targetPath}, but {sourcePath} is not (yet) existing.{Colors.RESET}")
                    
                # Copy files or directories
                if os.path.isdir(sourcePath):
                    if not os.path.exists(targetPath):
                        print(f"{Colors.GREEN}Copying directory: {sourcePath} -> {targetPath}{Colors.RESET}")
                        shutil.copytree(sourcePath, targetPath)
                        results['copies'] += 1
                    else:
                        print(f"{Colors.YELLOW}Skipping directory copy: {sourcePath} -> {targetPath} (already exists){Colors.RESET}")
                        errorList['copyWarnings'] += 1
                else:
                    if not os.path.exists(targetPath):
                        print(f"{Colors.GREEN}Copying file: {sourcePath} -> {targetPath}{Colors.RESET}")
                        shutil.copy2(sourcePath, targetPath)
                        results['copies'] += 1
                    else:
                        print(f"{Colors.YELLOW}Skipping file copy: {sourcePath} -> {targetPath} (already exists){Colors.RESET}")
                        errorList['copyWarnings'] += 1

            except FileNotFoundError as e:
                print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
                errorList["copies"] += 1
                continue

            except ValueError as e:
                print(f"\n{Colors.RED}Configuration error: {e}{Colors.RESET}")
                errorList["copies"] += 1
                continue

            except PermissionError:
                print(f"\n{Colors.RED}Error: Permission denied when copying {sourcePath}{Colors.RESET}")
                errorList["copies"] += 1
                continue

            except OSError as e:
                print(f"{Colors.RED}Error copying {sourcePath}: {e}{Colors.RESET}")
                errorList["copies"] += 1
                continue
            
    print(f"\n{Colors.GREEN}Source file & folder copy/replace process completed{Colors.RESET} with {Colors.RED}{errorList['copies']} errors{Colors.RESET} and {Colors.YELLOW}{errorList['copyWarnings']} warnings{Colors.RESET}.\n")


# MARK: Modify files
def modifyFiles(config, destinationDirectory):
    """Modify files according to modification rules."""
    print(f"{Colors.YELLOW}Starting file modification process...{Colors.RESET}")
    for rule in config.get('modification_rules', []):
        filePattern = rule.get('file_pattern', '*')
        print(f"\nProcessing files matching pattern: {filePattern}")
        
        # Recursively search the destination directory
        for root, _, files in os.walk(destinationDirectory):
            for filename in files:
                try:
                    if re.match(filePattern, filename):
                        filePath = os.path.join(root, filename)
                        print(f"Modifying file: {filePath}")

                        # Read file content
                        with open(filePath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Perform text replacements
                        for insertRule in rule.get('insert_rules', []):
                            if 'after_text' in insertRule:
                                after_text = insertRule['after_text']
                                insert_text = insertRule['insert_text']
                                if after_text not in content:           #if not re.search(after_text, content):     # for use of * wildcard in text
                                    raise ValueError(f"Text '{after_text}' not found in file: {filePath}")
                                elif insert_text not in content:
                                    print(f"  {Colors.GREEN}Inserting text after: {after_text} {Colors.YELLOW}+ ->{Colors.GREEN} {insert_text}{Colors.RESET}")
                                    content = content.replace(after_text, after_text + insert_text.replace('\n', ''))
                                else:
                                    print(f"  {Colors.YELLOW}Text already present after: {after_text}{Colors.RESET}")
                                    errorList['modWarnings'] += 1


                            if 'before_text' in insertRule:
                                before_text = insertRule['before_text']
                                insert_text = insertRule['insert_text']
                                if before_text not in content:
                                    raise ValueError(f"Text '{before_text}' not found in file: {filePath}")
                                elif insert_text not in content:
                                    print(f"  {Colors.GREEN}Inserting text before: {insert_text} {Colors.YELLOW}+ <-{Colors.GREEN} {before_text}{Colors.RESET}")
                                    content = content.replace(before_text, insert_text.replace('\n', '') + before_text)
                                else:
                                    print(f"  {Colors.YELLOW}Text already present before: {before_text}{Colors.RESET}")
                                    errorList['modWarnings'] += 1

                        for replaceRules in rule.get('replace_rules', []):
                            if 'old_text' in replaceRules:
                                old_text = replaceRules['old_text']
                                new_text = replaceRules['new_text']
                                if old_text not in content and new_text not in content:
                                    raise ValueError(f"Text '{old_text}' not found in file: {filePath}")
                                elif new_text not in content:
                                    print(f"  {Colors.GREEN}Replacing text: {old_text} {Colors.YELLOW}->{Colors.GREEN} {new_text}{Colors.RESET}")
                                    content = content.replace(old_text, new_text)
                                else:
                                    print(f"  {Colors.YELLOW}Text already replaced: {old_text} -> {new_text}{Colors.RESET}")
                                    errorList['modWarnings'] += 1


                        # Write modified contents
                        with open(filePath, 'w', encoding='utf-8') as f:
                            f.write(content)

                        results['modifications'] += 1
                    #else:
                    #    print(f"Skipping file: {filename} (not found)")

                except ValueError as e:
                    print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
                    errorList["modifications"] += 1
                    continue

                except PermissionError:
                    print(f"\n{Colors.RED}Error: Permission denied when modifying {filePath}{Colors.RESET}")
                    errorList["modifications"] += 1
                    continue

                except IOError as e:
                    print(f"\n{Colors.RED}Error reading/writing file {filePath}: {e}{Colors.RESET}")
                    errorList["modifications"] += 1
                    continue

    print(f"\n{Colors.GREEN}File modification process completed{Colors.RESET} with {Colors.RED}{errorList['modifications']} errors{Colors.RESET} and {Colors.YELLOW}{errorList['modWarnings']} warnings{Colors.RESET}.\n")


# MARK: Main function
def main():
    """Main function to execute all operations."""
    # Check command-line argument
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Please provide the path to the configuration file.{Colors.RESET}")
        sys.exit(1)

    configPath = sys.argv[1]
    
    # Load configuration
    config = loadConfig(configPath)

    # Ensure destination directory
    destinationDirectory = config.get('destination_directory', './web')
    ensureDirectory(destinationDirectory)
    
    # Copy files and folders
    copySources(config, destinationDirectory)
    
    # Modify files
    modifyFiles(config, destinationDirectory)

    # Print results
    print(f'\n{Colors.GREEN}Total successful copies: {results["copies"]}')
    print(f'Total file modifications: {results["modifications"]}{Colors.RESET}')

    if errorList["copies"] > 0 or errorList["modifications"] > 0:
        print(f"{Colors.RED}Errors occurred during the process. Check the output for details.")
        print(f"Total copy errors: {errorList['copies']}")
        print(f"Total modification errors: {errorList['modifications']}{Colors.RESET}")
    elif errorList["copyWarnings"] > 0 or errorList["modWarnings"] > 0:
        print(f"{Colors.GREEN}All operations in {destinationDirectory} from {configPath} completed successfully!{Colors.YELLOW} But there were {errorList['modWarnings'] + errorList['copyWarnings']} warnings. Maybe you should check them.{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}All operations in {destinationDirectory} from {configPath} completed successfully!{Colors.RESET}")


if __name__ == '__main__':
    main()