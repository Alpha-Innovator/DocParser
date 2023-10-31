import shlex
import subprocess


def run_command(command, stdout=None, stderr=None, cwd=None):
    # Split the command into a sequence of arguments
    args = shlex.split(command)

    try:
        # Run the command
        p_obj = subprocess.Popen(
            args, stdout=stdout, stderr=stderr, cwd=cwd)

        # Wait the process to finish
        p_obj.wait()

        # Read return code
        return_code = p_obj.returncode

        # Read stdout and stderr
        stdout_result, stderr_result = p_obj.communicate()

        # Decode the stdout or set the result to none
        if stdout == subprocess.PIPE:
            stdout_result = decode_output(stdout_result)
        else:
            stdout_result = None

        # Decode the stderr or set the result to none
        if stderr == subprocess.PIPE:
            stderr_result = decode_output(stderr_result)
        else:
            stderr_result = None

        # Return the return code, stdout and stderr
        return return_code, stdout_result, stderr_result
    except subprocess.CalledProcessError as e:
        message = ('Could not run the command "{}"'.format(command) +
                   'RETURN_CODE: {}'.format(e.returncode) +
                   'STDOUT=>\n{}'.format(decode_output(e.stdout)) +
                   'STDERR=>\n{}'.format(decode_output(e.stderr)))
        raise ValueError(message)
    except:
        raise ValueError('Unknown error occurred')


def check_command_results(command, return_code, stdout, stderr):
    # There are errors if the return code is nonzero or the STDERR is nonempty
    if return_code != 0 or (isinstance(stderr, str) and len(stderr) > 0):
        # Check whether to convert none to instruction
        if stdout is None:
            stdout = '(See conole output above)'

        if stderr is None:
            stderr = '(See console output above)'

        # Raise the error
        raise ValueError(('Failed to run the command "{}"\n' +
                          'Return code: {}\n' +
                          'STDOUT->\n{}\n' +
                          'STDERR->\n{}').format(
            command, return_code, stdout, stderr))


def decode_output(output):
    try:
        return output.decode('utf-8')
    except UnicodeDecodeError:
        return output
