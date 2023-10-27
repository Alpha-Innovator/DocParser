import argparse

from rendering import render_simple_env
from rendering import render_complex_env
from logger import logger

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")


def parse_arguments() -> str:
    """
    Parses the command line arguments and returns the values of the input
    tex file, and debug mode.

    Returns:
        str: The path to the input tex file,
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_tex_file", type=str, required=True, help="Path to the input tex file"
    )

    args = parser.parse_args()
    origin_tex_file = args.input_tex_file

    return origin_tex_file


def main():
    origin_tex_file = parse_arguments()

    # render simple environment
    render_simple_env.run(origin_tex_file)

    # render complex environment
    render_complex_env.run(origin_tex_file)


if __name__ == "__main__":
    main()
