import os


import rendering.rendering as rendering
import rendering.utils as utils


def main():
    json_file = "example_paper_rendered.tex.json"
    text_annotation_file = "texts.json"
    json_data = utils.load_json(json_file)
    text_annotation = utils.load_json(text_annotation_file)

    num_algorithms = len(text_annotation["algorithm"])
    print(f"num_algorithms={num_algorithms}")

    base_name = os.path.splitext(json_file)[0]
    base_name = os.path.splitext(base_name)[0]
    for i in range(num_algorithms):
        # render i-th algorithm env
        rendering.enclose_algorithm(json_data, color="black", index=i)

        # store the result as a tex file
        output_file = base_name + "_" + "algorithm_" + str(i) + ".tex"
        utils.tex_file_from_data(json_data, output_file)
        # cancel the render operation
        rendering.enclose_algorithm(json_data, color="Algorithm_color", index=i)

    num_equations = len(text_annotation["equation"])
    print(f"num_equations={num_equations}")
    for i in range(num_equations):
        # render i-th algorithm env
        rendering.enclose_equation(json_data, color="black", index=i)

        # store the result as a tex file
        output_file = base_name + "_" + "equation_" + str(i) + ".tex"
        utils.tex_file_from_data(json_data, output_file)
        # cancel the render operation
        rendering.enclose_equation(json_data, color="Equation_color", index=i)

    num_tables = len(text_annotation["table"])
    print(f"num_tables={num_tables}")
    for i in range(num_tables):
        # render i-th algorithm env
        rendering.enclosed_table(json_data, color="black", index=i)

        # store the result as a tex file
        output_file = base_name + "_" + "table_" + str(i) + ".tex"
        utils.tex_file_from_data(json_data, output_file)
        # cancel the render operation
        rendering.enclosed_table(json_data, color="Table_color", index=i)


# 1. load the _rendered.tex.json file
# 2. load the statistic information of envs, such as table, equation, algorithm
# 3. render the env one by one
# 4. compile the pdf file
# 5. use layout_annotation_generator to generate annotation
# 6. delete redundant files

if __name__ == "__main__":
    main()
