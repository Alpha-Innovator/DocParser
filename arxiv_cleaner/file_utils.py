from pathlib import Path
import re
import shutil
import tempfile


def build_relative_path(path, relative_to_path):
    # Build the path object
    path_obj = Path(path)

    # Find the relative path
    relative_path_obj = path_obj.relative_to(relative_to_path)

    # Return the relative path
    return relative_path_obj.as_posix()


def change_extension(path, ext):
    # Build the path object
    path_obj = Path(path)

    # Change the suffix
    path_obj = path_obj.with_suffix(ext)

    # Return the updated path
    return str(path_obj)


def combine_paths(*paths):
    # Build the path object
    path_obj = Path(*paths)

    # Return the path
    return path_obj.as_posix()


def convert_paths_to_unix_style(paths):
    return [Path(path).as_posix() for path in paths]


def copy_file(src, dst):
    shutil.copyfile(src, dst)


def copy_files(relative_paths, src_dir, dst_dir, skip_nonexistent=False):
    # Copy each file from the source to destination directory
    for relative_path in relative_paths:
        # Build the source path
        src_path = combine_paths(src_dir, relative_path)

        # Check whether to skip nonexistent source file
        if skip_nonexistent:
            # Check whether the source file doesn't exist
            if not does_file_exist(src_path):
                # Skip the copying
                continue

        # Build the destination path
        dst_path = combine_paths(dst_dir, relative_path)

        # Ensure the destination directory exists
        ensure_path_exist(dst_path)

        # Copy the input file to the destination
        copy_file(src_path, dst_path)


def create_temp_dir(name=''):
    # Build the suffix
    suffix = '.{}'.format(name)

    # Create a temporary directory
    try:
        dir_obj = tempfile.TemporaryDirectory(
            prefix='arxiv_cleaner.', suffix=suffix)
    except:
        raise ValueError('Failed to create temporary directory')

    # Get the path of the temporary directory
    path = Path(dir_obj.name).as_posix()

    # Return the directory object
    return dir_obj, path


def create_temp_file(name=''):
    # Build the suffix
    suffix = '.{}'.format(name)

    # Create a temporary file
    try:
        # Create a named temporary file
        fp = tempfile.NamedTemporaryFile(
            delete=False, prefix='arxiv_cleaner.', suffix=suffix)
    except:
        raise ValueError('Failed to create temporary file')

    # Get the path of the temporary file
    path = Path(fp.name).as_posix()

    # Return the temporary file pointer and path
    return fp, path


def does_file_exist(path):
    # Build the path object
    path_obj = Path(path)

    # Check whether the file exists
    return path_obj.exists()


def ensure_path_exist(path):
    # Build the path object
    path_obj = Path(path)

    # Find the parent directory
    parent_obj = path_obj.parent

    # Make sure the parent directory exists
    parent_obj.mkdir(parents=True, exist_ok=True)


def find_files(path, extensions=[None], recursive=True):
    # Build the path object
    path_obj = Path(path)

    # Initialize all the found files
    all_found_files = []

    # Find files for each extension
    for extension in extensions:
        # Build the extension pattern
        if extension is None:
            extension_pattern = '*'
        else:
            extension_pattern = '*.{}'.format(extension)

        # Build the pattern
        pattern = '**/{}'.format(extension_pattern)

        # Find all files and directories
        found_files = path_obj.glob(pattern)

        # Filter only files
        found_files = filter(lambda f: f.is_file(), found_files)

        # Convert paths to Unix style
        found_files = convert_paths_to_unix_style(found_files)

        # Add the found files to the list
        all_found_files.extend(found_files)

    # Return all the found files
    return all_found_files


def remove_temp_dir(dir_obj):
    dir_obj.cleanup()


def remove_temp_file(fp):
    # Get the path of the temporary file
    path = Path(fp.name).as_posix()

    # Close the file pointer
    fp.close()

    # Try to delete the temporary file
    try:
        Path.unlink(path)
    except:
        # Ignore the error
        pass


def remove_unnecessary_blank_lines(path):
    # Read the content
    with open(path, 'r', encoding='utf-8') as fp:
        content = fp.read()

    # Remove unnecessary blank lines
    # Reference: https://stackoverflow.com/a/28902081
    cleaned_content = re.sub(r'\n\s*\n', '\n\n', content)

    # Remove also the starting blank lines
    cleaned_content = re.sub(r'^\s*\n', '', cleaned_content)

    # Save the content
    with open(path, 'w', encoding='utf-8') as fp:
        fp.write(cleaned_content)
