from arxiv_cleaner.file_utils import (
    build_relative_path, combine_paths, copy_files, create_temp_dir,
    does_file_exist, find_files, remove_temp_dir,
    remove_unnecessary_blank_lines)
from arxiv_cleaner.latex import LatexRunner
from arxiv_cleaner.logger import Logger


class Cleaner:
    def __init__(self, input_dir=None, output_dir=None, tex=None,
                 command_options=None, verbose=False):
        # Save the arguments
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.verbose = verbose

        # Initialize the logger
        self._init_logger()

        # Initialize input files
        self._init_input_files()

        # Initialize TEX files
        self._init_tex_files(tex)

        # Initialize the latex runner
        self._init_latex_runner(command_options)

    ############################################################################
    # Cleaning Methods
    ############################################################################

    def clean(self):
        # Log the start
        self.logger.info('Start cleaning')

        # Expand the files
        expanded_dir_obj, expanded_dir = self.expand_files()

        # Create a temporary project with expanded files
        project_dir_obj, project_dir = self.create_temp_project()

        # Copy the input files to the temporary project directory
        self.copy_input_files_to_project(project_dir)

        # Copy the expanded files to the temporary project directory
        self.copy_expanded_files_to_project(expanded_dir, project_dir)

        # Compile the TEX files with latex compiler to find the dependencies
        project_deps = self.compile_tex_to_find_dependencies(project_dir)

        # Compile the TEX files with bibliography compiler to find the
        # dependencies
        bbl_deps = self.compile_bib_to_find_dependencies(project_dir)

        # Copy the dependency files to the output directory
        self.copy_dependencies_to_output(project_deps)

        # Copy the expanded files to the output directory
        self.copy_expanded_files_to_output(project_deps, expanded_dir)

        # Copy the BBL dependencies to the output directory
        self.copy_bbl_files_to_output(bbl_deps, project_dir)

        # Remove unnecessary blank lines
        self.remove_unnecessary_blank_lines()

        # Remove the temporary expanded directory
        remove_temp_dir(expanded_dir_obj)

        # Remove the temporary project directory
        remove_temp_dir(project_dir_obj)

        # Log the finish
        self.logger.info(
            'Check the cleaned project at "{}"'.format(self.output_dir))

    ############################################################################
    # Steps
    ############################################################################

    def expand_files(self):
        # Log the start
        self.logger.info('Start expanding files in input directory')

        # Initialize the extensions
        # Reference: https://tex.stackexchange.com/a/424669
        extensions = ['tex', 'cls', 'clo', 'sty', 'bst']

        # Find all target files in the input directory
        target_files = find_files(self.input_dir, extensions=extensions)

        # Run latexpand and produce new files in the new temporary directory
        new_dir_obj, new_dir = self.latex_runner.run_latexpand(
            self.input_dir, target_files)

        # Return the final directory object and path
        return new_dir_obj, new_dir

    def create_temp_project(self):
        # Log the start
        self.logger.info('Start creating temporary project')

        # Create a temporary directory
        temp_dir_obj, temp_dir = create_temp_dir(name='temp_project')

        # Return the directory object and path
        return temp_dir_obj, temp_dir

    def copy_input_files_to_project(self, project_dir):
        # Log the start
        self.logger.info(
            'Start copying files from input directory to temporary project')

        # Copy the files from the input directory to project directory
        copy_files(self.relative_input_paths, self.input_dir, project_dir)

    def copy_expanded_files_to_project(self, expanded_dir, project_dir):
        # Log the start
        self.logger.info('Start copying files to temporary project')

        # Copy the files from the expanded directory to project directory
        copy_files(self.tex_files, expanded_dir, project_dir)

    def compile_tex_to_find_dependencies(self, project_dir):
        # Log the start
        self.logger.info('Start compiling latex to find dependencies')

        # Convert the relative input paths to set
        relative_input_paths = set(self.relative_input_paths)

        # Initialize the project dependencies
        project_deps = set()

        # Find dependencies for each TEX file
        for tex_file in self.tex_files:
            # Build the full path
            full_path = combine_paths(project_dir, tex_file)

            # Run the latex compiler to read the dependencies
            fls_deps = self.latex_runner.run_latex_compiler(
                project_dir, full_path)

            # Find the dependencies in the input directory
            deps = fls_deps.intersection(relative_input_paths)

            # Add the dependencies to the project dependencies
            project_deps.update(deps)

        # Return the project dependencies
        return project_deps

    def compile_bib_to_find_dependencies(self, project_dir):
        # Log the start
        self.logger.info('Start compiling bibliography to find dependencies')

        # Initialize the BBL dependencies
        bbl_deps = set()

        # Compile bibliography for each TEX file
        for tex_file in self.tex_files:
            # Build the full path
            full_path = combine_paths(project_dir, tex_file)

            # Run the bibliography compiler to read the BBL dependencies
            deps = self.latex_runner.run_bib_compiler(
                project_dir, full_path)

            # Add the dependencies to the project dependencies
            bbl_deps.update(deps)

        # Return the BBL dependencies
        return bbl_deps

    def copy_dependencies_to_output(self, project_deps):
        # Log the start
        self.logger.info('Start copying dependency files to output directory')

        # Copy the files from the input directory to output directory
        copy_files(project_deps, self.input_dir, self.output_dir)

    def copy_expanded_files_to_output(self, project_deps, expanded_dir):
        # Log the start
        self.logger.info('Start copying expanded files to output directory')

        # Copy the files from the expanded directory to output directory and
        # skip any nonexistent dependency file
        copy_files(project_deps, expanded_dir,
                   self.output_dir, skip_nonexistent=True)

        # Copy the files from the expanded directory to output directory
        copy_files(self.tex_files, expanded_dir, self.output_dir)

    def copy_bbl_files_to_output(self, bbl_deps, project_dir):
        # Log the start
        self.logger.info('Start copying BBL files to output directory')

        # Copy the files from the project directory to output directory
        copy_files(bbl_deps, project_dir, self.output_dir)

    def remove_unnecessary_blank_lines(self):
        # Log the start
        self.logger.info(
            'Start removing unnecessary blank lines in output directory')

        # Initialize the extensions
        # Reference: https://tex.stackexchange.com/a/424669
        extensions = ['tex', 'cls', 'clo', 'sty', 'bst']

        # Find all target files in the input directory
        target_files = find_files(self.output_dir, extensions=extensions)

        # Remove for each target file
        for target_file in target_files:
            remove_unnecessary_blank_lines(target_file)

    ############################################################################
    # Initialization
    ############################################################################

    def _init_logger(self):
        # Set the logging level
        level = 'INFO' if self.verbose else 'WARNING'

        # Create a logger
        self.logger = Logger('cleaner', level=level)

    def _init_input_files(self):
        # Find all files in the input directory and save
        self.input_files = find_files(self.input_dir)

        # Build relative paths for all input files and save
        self.relative_input_paths = [build_relative_path(
            f, self.input_dir) for f in self.input_files]

    def _init_tex_files(self, tex):
        # Parse the TEX files and save
        self.tex_files = tex.split(',')

        # Check whether the TEX files exist
        self._check_tex_files()

    def _init_latex_runner(self, command_options):
        # Create a latex runner and save
        self.latex_runner = LatexRunner(command_options)

    def _check_tex_files(self):
        # Check each TEX file
        for tex_file in self.tex_files:
            # Build the full path
            full_path = combine_paths(self.input_dir, tex_file)

            # Check whether the file exists
            if not does_file_exist(full_path):
                raise ValueError(('TEX file "{}" does not exist in the input' +
                                  ' directory "{}"').format(
                    tex_file, self.input_dir))
