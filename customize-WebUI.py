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
                        mode = rule.get('mode')
                        if mode == 'replace':
                            # handled earlier
                            print(f"{Colors.YELLOW}Unexpected existing directory in replace mode (already handled): {targetPath}{Colors.RESET}")
                            errorList['copyWarnings'] += 1
                        elif mode in ('copy','merge'):
                            added = 0
                            for rootDir, subdirs, files in os.walk(sourcePath):
                                relRoot = os.path.relpath(rootDir, sourcePath)
                                relRoot = '' if relRoot == '.' else relRoot
                                destRoot = os.path.join(targetPath, relRoot) if relRoot else targetPath
                                ensureDirectory(destRoot)
                                for fname in files:
                                    srcFile = os.path.join(rootDir, fname)
                                    destFile = os.path.join(destRoot, fname)
                                    if not os.path.exists(destFile):
                                        shutil.copy2(srcFile, destFile)
                                        added += 1
                            if added:
                                print(f"{Colors.GREEN}Added {added} new file(s) into existing directory (copy merge behavior): {targetPath}{Colors.RESET}")
                                results['copies'] += added
                            else:
                                print(f"{Colors.YELLOW}Directory already up to date (no new files): {targetPath}{Colors.RESET}")
                                errorList['copyWarnings'] += 1
                        else:
                            print(f"{Colors.YELLOW}Skipping directory copy (mode {mode}): already exists {targetPath}{Colors.RESET}")
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
def _is_regex(marker: str) -> bool:
    """Return True if the marker is flagged as regex (prefix 're:')."""
    return isinstance(marker, str) and marker.startswith('re:')


def _extract_pattern(marker: str) -> str:
    """Strip the 're:' prefix and return the regex pattern."""
    return marker[3:]


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

                        # Perform text replacements / insertions
                        for insertRule in rule.get('insert_rules', []):
                            # AFTER TEXT INSERTION
                            if 'after_text' in insertRule:
                                raw_after = insertRule['after_text']
                                insert_text = insertRule['insert_text'].replace('\n', '')
                                if _is_regex(raw_after):
                                    pattern = _extract_pattern(raw_after)
                                    # search first occurrence
                                    match = re.search(pattern, content, re.DOTALL)
                                    if not match:
                                        raise ValueError(f"Regex after_text pattern '{pattern}' not found in file: {filePath}")
                                    anchor = match.group(0)
                                    # idempotency check
                                    if anchor + insert_text in content[match.start():match.start()+len(anchor)+len(insert_text)+5]:
                                        print(f"  {Colors.YELLOW}Regex after_text already has insertion after anchor.{Colors.RESET}")
                                        errorList['modWarnings'] += 1
                                    else:
                                        print(f"  {Colors.GREEN}Regex inserting after anchor: /{pattern}/ -> {insert_text[:60]}...{Colors.RESET}")
                                        content = content[:match.end()] + insert_text + content[match.end():]
                                        results['modifications'] += 1
                                else:
                                    # Plain (substring) variant – use first occurrence only (consistent with replace count=1)
                                    anchor = raw_after
                                    idx = content.find(anchor)
                                    if idx == -1:
                                        raise ValueError(f"Text '{anchor}' not found in file: {filePath}")
                                    after_pos = idx + len(anchor)
                                    # Precise idempotency: is insert_text already directly after anchor?
                                    if content.startswith(insert_text, after_pos):
                                        print(f"  {Colors.YELLOW}Plain after_text already directly followed by insertion (idempotent).{Colors.RESET}")
                                        errorList['modWarnings'] += 1
                                    else:
                                        print(f"  {Colors.GREEN}Inserting text after (plain): {anchor[:40]} -> {insert_text[:60]}...{Colors.RESET}")
                                        content = content[:after_pos] + insert_text + content[after_pos:]
                                        results['modifications'] += 1

                            # BEFORE TEXT INSERTION
                            if 'before_text' in insertRule:
                                raw_before = insertRule['before_text']
                                insert_text = insertRule['insert_text'].replace('\n', '')
                                if _is_regex(raw_before):
                                    pattern = _extract_pattern(raw_before)
                                    match = re.search(pattern, content, re.DOTALL)
                                    if not match:
                                        raise ValueError(f"Regex before_text pattern '{pattern}' not found in file: {filePath}")
                                    anchor = match.group(0)
                                    segment_start = max(0, match.start() - len(insert_text) - 5)
                                    if insert_text + anchor in content[segment_start:match.end()+len(insert_text)]:
                                        print(f"  {Colors.YELLOW}Regex before_text already has insertion before anchor.{Colors.RESET}")
                                        errorList['modWarnings'] += 1
                                    else:
                                        print(f"  {Colors.GREEN}Regex inserting before anchor: /{pattern}/ <- {insert_text[:60]}...{Colors.RESET}")
                                        content = content[:match.start()] + insert_text + content[match.start():]
                                        results['modifications'] += 1
                                else:
                                    # Plain (substring) variant – first occurrence logic
                                    anchor = raw_before
                                    idx = content.find(anchor)
                                    if idx == -1:
                                        raise ValueError(f"Text '{anchor}' not found in file: {filePath}")
                                    before_pos = idx
                                    # Precise idempotency: does insert_text already sit immediately before anchor?
                                    if before_pos >= len(insert_text) and content[before_pos - len(insert_text): before_pos] == insert_text:
                                        print(f"  {Colors.YELLOW}Plain before_text already directly preceded by insertion (idempotent).{Colors.RESET}")
                                        errorList['modWarnings'] += 1
                                    else:
                                        print(f"  {Colors.GREEN}Inserting text before (plain): {insert_text[:60]}... <- {anchor[:40]}{Colors.RESET}")
                                        content = content[:before_pos] + insert_text + content[before_pos:]
                                        results['modifications'] += 1

                        # REPLACE RULES
                        for replaceRules in rule.get('replace_rules', []):
                            if 'old_text' in replaceRules:
                                raw_old = replaceRules['old_text']
                                new_text = replaceRules['new_text']
                                if _is_regex(raw_old):
                                    pattern = _extract_pattern(raw_old)
                                    if re.search(re.escape(new_text), content):
                                        print(f"  {Colors.YELLOW}Regex replacement already applied -> {new_text[:60]}...{Colors.RESET}")
                                        errorList['modWarnings'] += 1
                                        continue
                                    if not re.search(pattern, content, re.DOTALL):
                                        raise ValueError(f"Regex old_text pattern '{pattern}' not found in file: {filePath}")
                                    content_new, count = re.subn(pattern, new_text, content, count=1)
                                    if count:
                                        print(f"  {Colors.GREEN}Regex replacing pattern /{pattern}/ -> {new_text[:60]}...{Colors.RESET}")
                                        content = content_new
                                        results['modifications'] += 1
                                    else:
                                        print(f"  {Colors.YELLOW}Regex replacement produced no change for /{pattern}/.{Colors.RESET}")
                                        errorList['modWarnings'] += 1
                                else:
                                    old_text = raw_old
                                    if old_text not in content and new_text not in content:
                                        raise ValueError(f"Text '{old_text}' not found in file: {filePath}")
                                    elif new_text not in content:
                                        print(f"  {Colors.GREEN}Replacing text: {old_text[:60]}... -> {new_text[:60]}...{Colors.RESET}")
                                        content = content.replace(old_text, new_text, 1)
                                        results['modifications'] += 1
                                    else:
                                        print(f"  {Colors.YELLOW}Text already replaced: {old_text[:40]} -> {new_text[:40]}{Colors.RESET}")
                                        errorList['modWarnings'] += 1


                        # Write modified contents
                        with open(filePath, 'w', encoding='utf-8') as f:
                            f.write(content)

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