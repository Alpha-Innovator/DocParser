import re
import subprocess

from arxiv_cleaner.cli import run_command, check_command_results
from arxiv_cleaner.file_utils import (
    build_relative_path, change_extension, combine_paths, create_temp_dir,
    ensure_path_exist)


class LatexRunner:
    def __init__(self, command_options):
        # Save the arguments
        self.command_options = command_options

    def run_latexpand(self, root_dir, tex_files):
        # Create a temporary directory
        temp_dir_obj, temp_dir = create_temp_dir(name='latexpand_output')

        # Process each TEX file
        for tex_file in tex_files:
            # Build the relative path
            relative_path = build_relative_path(tex_file, root_dir)

            # Build the output path
            output_path = combine_paths(temp_dir, relative_path)

            # Ensure the output directory exists
            ensure_path_exist(output_path)

            # Build the command to run latexpand
            command = self._build_latexpand_command(output_path, relative_path)

            # Run the command
            return_code, stdout, stderr = run_command(command, cwd=root_dir)

            # Check return code and STDERR
            check_command_results(command, return_code, stdout, stderr)

        # Return the temporary directory object and path
        return temp_dir_obj, temp_dir

    def run_latex_compiler(self, root_dir, tex_file):
        # Build the command to run the compiler
        command = self._build_latex_compiler_command(tex_file)

        # Run the command
        return_code, stdout, stderr = run_command(command, cwd=root_dir)

        # Check return code and STDERR
        check_command_results(command, return_code, stdout, stderr)

        # Build the path to FLS file
        fls_path = change_extension(tex_file, '.fls')

        # Read the FLS file to get all dependencies and return
        return self._read_fls_dependencies(fls_path)

    def run_bib_compiler(self, root_dir, tex_file):
        # Build the relative path
        relative_path = build_relative_path(tex_file, root_dir)

        # Remove the file extension
        relative_path = change_extension(relative_path, '')

        # Build the command to run the compiler
        command = self._build_bib_compiler_command(relative_path)

        # Run the command
        return_code, _, _ = run_command(command, cwd=root_dir)

        # Check whether the result is successful
        if return_code == 0:
            # Build the path to BBL file
            bbl_file = change_extension(tex_file, '.bbl')

            # Build the relative path
            bbl_file = build_relative_path(bbl_file, root_dir)

            # Set the BBL dependencies by adding the BBL file
            deps = set([bbl_file])
        else:
            # Set the empty BBL dependencies
            deps = set()

        # Return the dependencies
        return deps

    def _read_fls_dependencies(self, fls_path):
        # Read all lines in the FLS file
        with open(fls_path) as fp:
            lines = fp.readlines()

        # Initialize the dependencies
        deps = set()

        # Initialize the pattern
        pattern = re.compile(r'INPUT\s+(?P<path>.+)\n')

        # Check input paths for each line
        for line in lines:
            # Find the full match
            match = pattern.fullmatch(line)

            # Check if there is a match
            if match:
                # Get the input path
                input_path = match.group('path')

                # Add the input path to the set
                deps.add(input_path)

        # Return the dependencies
        return deps

    def _build_latexpand_command(self, output_path, input_path):
        # Get the extra arguments
        extra_args = self.command_options['latexpand']['extra_args']

        # Build the command and return
        return ' '.join([
            'latexpand',
            '--output="{}"'.format(output_path),
            '--fatal',
            '--out-encoding="{}"'.format('encoding(UTF-8)'),
            extra_args,
            '"{}"'.format(input_path),
        ])

    def _build_latex_compiler_command(self, tex_file):
        # Get the compiler
        compiler = self.command_options['latex']['compiler']

        # Get the extra arguments
        extra_args = self.command_options['latex']['extra_args']

        # Build the command and return
        return ' '.join([
            compiler,
            '-interaction=nonstopmode',
            '-recorder',
            extra_args,
            '"{}"'.format(tex_file),
        ])

    def _build_bib_compiler_command(self, tex_file):
        # Get the compiler
        compiler = self.command_options['bib']['compiler']

        # Get the extra arguments
        extra_args = self.command_options['bib']['extra_args']

        # Build the command and return
        return ' '.join([
            compiler,
            extra_args,
            '"{}"'.format(tex_file),
        ])
