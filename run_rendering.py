import argparse
import os

import rendering.utils as utils
import rendering.render_simple_env as render_simple_env
import logger.logger as logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


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


def render_tex_data(data, config):
    name2category = {name: category for category, name in config["category_name"]}
    category2rgbcolor = {
        category: tuple(color) for category, color in config["category_color"]
    }
    name2rgbcolor = {
        name: category2rgbcolor[category] for name, category in name2category.items()
    }
    name2color = render_simple_env.add_color_definition(data, name2rgbcolor)

    render_simple_env.add_usepackage_command(data, "xcolor")
    
    # render title
    render_simple_env.enclose_title(data, color=name2color["Title"])
    # render abstract
    render_simple_env.enclose_abstract(
        data, title_color=name2color["Title"], text_color=name2color["Text"]
    )

    main_content, index = utils.get_main_content(data)

    render_simple_env.enclose_section(main_content, color=name2color["Title"])

    render_simple_env.enclose_list(main_content, color=name2color["List"])

    render_simple_env.enclose_caption(main_content, color=name2color["Caption"])

    render_simple_env.enclose_equation(main_content, color=name2color["Equation"])

    render_simple_env.enclose_table(main_content, color=name2color["Table"])

    render_simple_env.enclose_footnote(main_content, color=name2color["Footnote"])

    render_simple_env.enclose_reference(main_content, color=name2color["Text"])

    render_simple_env.enclose_algorithm(main_content, color=name2color["Algorithm"])

    render_simple_env.enclose_figure(main_content, color=name2color["Figure"])

    main_content = render_simple_env.enclose_text(
        main_content, color=name2color["Text"]
    )
    data[index]["document"][1] = main_content


def main():
    origin_tex_file, rendered_tex_file, debug_mode = parse_arguments()
    origin_dir = os.path.dirname(origin_tex_file)

    # Read tex file and convert to texSoup
    data = utils.data_from_tex_file(origin_tex_file, debug_mode)

    # load color information for each category
    config = utils.load_json("config.json")

    render_tex_data(data, config)

    # save the text annotation information into json
    text_file = os.path.join(origin_dir, config["text_elements_file"])
    render_simple_env.save_texts(text_file)

    # Convert data back to tex file
    utils.tex_file_from_data(data, rendered_tex_file, debug_mode)


if __name__ == "__main__":
    main()
