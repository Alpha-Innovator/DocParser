import argparse

import rendering.utils as utils
import rendering.rendering as rendering
import logger.logger as logger

log = logger.setup_app_level_logger(file_name="app_debug.log")

config = utils.load_json("config.json")
name2category = {name: category for category, name in config["category_name"]}
category2rgbcolor = {
    category: tuple(color) for category, color in config["category_color"]
}
name2rgbcolor = {
    name: category2rgbcolor[category] for name, category in name2category.items()
}


def parse_arguments():
    """
    Parses the command line arguments and returns the values of the input
    tex file, output tex file, and debug mode.

    Returns:
        Tuple[str, str, bool]: A tuple containing
        - the path to the input tex file,
        - the path to the output tex file,
        - a boolean representing the debug mode.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_tex_file", type=str, required=True, help="Path to the input tex file"
    )
    parser.add_argument(
        "--output_tex_file", type=str, required=True, help="Path to the output tex file"
    )
    parser.add_argument(
        "--debug_mode", action="store_true", default=False, help="Debug mode"
    )

    args = parser.parse_args()
    origin_tex_file = args.input_tex_file
    rendered_tex_file = args.output_tex_file
    debug_mode = args.debug_mode

    return origin_tex_file, rendered_tex_file, debug_mode


def render_tex_data(data):
    rendering.add_usepackage_command(data, "xcolor")
    rendering.add_usepackage_command(data, "mdframed")  # used for figure

    name2color = rendering.add_color_definition(data, name2rgbcolor)
    # render title
    rendering.enclose_title(data, color=name2color["Title"])
    # render abstract
    rendering.enclose_abstract(
        data, title_color=name2color["Title"], text_color=name2color["Text"]
    )

    main_content, index = utils.get_main_content(data)

    main_content = rendering.enclose_text(main_content, color=name2color["Text"])
    data[index]["document"][1] = main_content

    rendering.enclose_section(main_content, color=name2color["Title"])

    rendering.enclose_list(main_content, color=name2color["List"])

    rendering.enclose_caption(main_content, color=name2color["Caption"])

    rendering.enclose_equation(main_content, color=name2color["Equation"])

    rendering.enclosed_table(main_content, color=name2color["Table"])

    rendering.enclose_footnote(main_content, color=name2color["Footnote"])

    rendering.enclose_reference(main_content, color=name2color["Text"])

    rendering.enclose_algorithm(main_content, color=name2color["Algorithm"])


def main():
    origin_tex_file, rendered_tex_file, debug_mode = parse_arguments()

    # Read tex file and convert to texSoup
    data = utils.data_from_tex_file(origin_tex_file, debug_mode)

    render_tex_data(data)

    # save the text annotation information into json
    rendering.save_texts(config["text_elements_file"])

    # Convert data back to tex file
    utils.tex_file_from_data(data, rendered_tex_file, debug_mode)


if __name__ == "__main__":
    main()
