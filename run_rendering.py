import argparse
import os

import rendering.utils as utils
import rendering.rendering as rendering
import logger.logger as logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_tex_file', type=str, required=True,
                        help='Path to the input tex file')
    parser.add_argument('--output_tex_file', type=str, required=True,
                        help='Path to the output tex file')
    parser.add_argument('--debug_mode', action='store_true', default=False,
                        help='Debug mode')

    args = parser.parse_args()
    origin_tex_file = args.input_tex_file
    rendered_tex_file = args.output_tex_file
    debug_mode = args.debug_mode

    # Read tex file and convert to texSoup
    data = utils.data_from_tex_file(origin_tex_file, debug_mode)

    rendering.add_usepackage_command(data, 'xcolor')
    rendering.add_usepackage_command(data, 'mdframed')  # used for figure

    # render title
    rendering.enclose_title(data)

    main_content = utils.get_main_content(data)

    rendering.enclose_section(main_content)

    rendering.enclose_list(main_content)

    rendering.enclose_caption(main_content)

    rendering.enclose_equation(main_content)

    rendering.enclosed_table(main_content)

    # very first version, need to be improved
    rendering.enclose_text(main_content)

    rendering.enclose_reference(main_content)

    rendering.enclose_figure(main_content)

    rendering.enclose_algorithm(main_content)

    # output tex file
    utils.tex_file_from_data(data, rendered_tex_file, debug_mode)


if __name__ == '__main__':
    main()
