from functools import partial
import os
import arxiv
import shutil
import multiprocessing
import time

from vrdu import logger

log = logger.setup_app_level_logger(file_name="retrive_metadata.log")


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
    # wait for 5 seconds, see https://info.arxiv.org/help/api/tou.html Limitations
    time.sleep(5.0)

    file_name, category = None, None
    for result in search.results():
        file_name = result._get_default_filename(extension="")
        category = result.primary_category
        break

    if file_name is None or category is None:
        raise FileNotFoundError(f"metadata of {path} cannot be found in arXiv.")
    return file_name[:-1], category


def retrieve_subfolders(path, dir_name):
    new_dir_name, category = retrieve_arxiv_metadata(dir_name)
    if not os.path.exists(os.path.join(path, category)):
        os.makedirs(os.path.join(path, category))
        log.info("Created directory: {}".format(os.path.join(path, category)))
    try:
        shutil.move(
            os.path.join(path, dir_name),
            os.path.join(path, category + "/" + new_dir_name),
        )
        log.info("Moved directory: {}".format(os.path.join(path, dir_name)))
    except Exception as e:
        pass


def run(path, cpu_count):
    """
    Moves subfolders in the given path to a new location based on arxiv metadata.
    subfolders must have pattern "****.****", where * is a digit.

    Args:
        path (str): The path to the directory containing the subfolders.

    Returns:
        None

    Example:

    """
    log.info("Starting to move subfolders in {}".format(path))
    subfolders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    filtered_subfolders = [
        f
        for f in subfolders
        if len(f) == 9 and f[:4].isdigit() and f[5:].isdigit() and f[4] == "."
    ]
    log.info("There are {} subfolders".format(len(filtered_subfolders)))

    f = partial(retrieve_subfolders, path)
    with multiprocessing.Pool(processes=cpu_count) as p:
        p.map(f, filtered_subfolders)


def retrive_metadata_for_pdfs(path, file_format="pdf"):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    pdf_files = [f for f in files if f.endswith(file_format)]
    num_papers = len(pdf_files)
    log.info("There are {} subfolders".format(num_papers))
    big_slow_client = arxiv.Client(delay_seconds=5)
    slice_length = 50
    for i in range(0, num_papers, slice_length):
        slice_list = [
            pdf_file[: -(len(file_format) + 1)]
            for pdf_file in pdf_files[i : i + slice_length]
        ]
        for pdf_file, result in zip(
            slice_list,
            big_slow_client.results(arxiv.Search(id_list=slice_list)),
        ):
            category = result.primary_category
            if not os.path.exists(os.path.join(path, category)):
                os.makedirs(os.path.join(path, category))
                log.info("Created directory: {}".format(os.path.join(path, category)))
            try:
                old_path = os.path.join(path, pdf_file + "." + file_format)
                new_path = os.path.join(path, category)
                shutil.move(old_path, new_path)
                log.info(
                    "Move directory: {} to {}".format(
                        old_path,
                        new_path,
                    )
                )
            except Exception:
                log.exception(f"Error moving {old_path}")
                pass


def run_v2(path):
    subfolders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    filtered_subfolders = [
        f
        for f in subfolders
        if len(f) == 9 and f[:4].isdigit() and f[5:].isdigit() and f[4] == "."
    ]
    num_papers = len(filtered_subfolders)
    log.info("There are {} subfolders".format(num_papers))
    big_slow_client = arxiv.Client(delay_seconds=5)
    slice_length = 100
    for i in range(0, num_papers, slice_length):
        slice_list = filtered_subfolders[i : i + slice_length]
        for dir_name, result in zip(
            slice_list,
            big_slow_client.results(arxiv.Search(id_list=slice_list)),
        ):
            new_dir_name = result._get_default_filename(extension="")
            category = result.primary_category
            log.info(
                f"dir_name: {dir_name}, category: {category}, new_dir_name: {new_dir_name}"
            )
            if not os.path.exists(os.path.join(path, category)):
                os.makedirs(os.path.join(path, category))
                log.info("Created directory: {}".format(os.path.join(path, category)))
            try:
                old_path = os.path.join(path, dir_name)
                new_path = os.path.join(path, category + "/" + new_dir_name)
                if os.path.exists(new_path):
                    shutil.rmtree(new_path)
                shutil.move(old_path, new_path)
                log.info(
                    "Move directory: {} to {}".format(
                        old_path,
                        new_path,
                    )
                )
            except Exception:
                log.exception(f"Error moving {old_path}")
                pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="path to directory containing subfolders")
    parser.add_argument("-c", "--cpu_count", type=int, default=1)
    args = parser.parse_args()
    # run(args.path, args.cpu_count)
    # run_v2(args.path)
    retrive_metadata_for_pdfs(args.path, "docx")
