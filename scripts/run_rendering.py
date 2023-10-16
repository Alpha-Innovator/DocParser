import argparse

from rendering import utils
from rendering import render_simple_env
from rendering import render_complex_env
from logger import logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


def parse_arguments():
    """
    Parses the command line arguments and returns the values of the input
    tex file, and debug mode.

    Returns:
        Tuple[str, str, bool]: A tuple containing
        - the path to the input tex file,
        - a boolean representing the debug mode.
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

    config = utils.load_json("config/config.json")

    # render simple environment
    render_simple_env.run(origin_tex_file, config)

    # render complex environment
    render_complex_env.run(origin_tex_file, config)


if __name__ == "__main__":
    main()
