import os
import arxiv
import shutil


def retrieve_arxiv_metadata(path: str):
    """
    Retrieves metadata for a given arXiv document folder, the folder follows the pattern "****.****", where * is a digit.

    Args:
        path (str): The path of the arXiv document.

    Returns:
        Tuple[str, str]: A tuple containing the file name and the category of the arxiv document.

    Raises:
        FileNotFoundError: If the metadata of the document cannot be found in arxiv.
    """
    search = arxiv.Search(id_list=[path])

    file_name, category = None, None
    for result in search.results():
        file_name = result._get_default_filename(extension="")
        category = result.primary_category
        break

    if file_name is None or category is None:
        raise FileNotFoundError(f"metadata of {path} cannot be found in arXiv.")
    return file_name[:-1], category


def run(path):
    """
    Moves subfolders in the given path to a new location based on arxiv metadata.
    subfolders must have pattern "****.****", where * is a digit.

    Args:
        path (str): The path to the directory containing the subfolders.

    Returns:
        None

    Example:

    """
    subfolders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    filtered_subfolders = [
        f
        for f in subfolders
        if len(f) == 9 and f[:4].isdigit() and f[5:].isdigit() and f[4] == "."
    ]
    for dir_name in filtered_subfolders:
        new_dir_name, category = retrieve_arxiv_metadata(dir_name)
        if not os.path.exists(os.path.join(path, category)):
            os.makedirs(os.path.join(path, category))
        shutil.move(
            os.path.join(path, dir_name),
            os.path.join(path, category + "/" + new_dir_name),
        )
        print(f"Moved {dir_name} to {category}/{new_dir_name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="path to directory containing subfolders")
    args = parser.parse_args()

    run(args.path)
