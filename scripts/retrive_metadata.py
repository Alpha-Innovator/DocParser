import os
import arxiv
import shutil

from vrdu import logger

log = logger.setup_app_level_logger(file_name="retrive_metadata.log")


def retrive_metadata_for_files(path: str) -> None:
    """Retrieves metadata for files in a specified path.
    It first query the primary category by the file's name, then move the
    file to the path/{category}

    Args:
        path (str): The path to the directory containing the files.

    Returns:
        None

    Raises:
        None

    This function retrieves metadata for the files in the specified path.
    It filters the files based on a specific format, moves them to categorized directories, and logs the actions performed.

    Note:
        The function assumes that the files in the specified path are in the format 'xxxx.yyyy.ext',
        where 'xxxx' and 'yyyy' are digits, and `ext` is the extension format.

    Example:
        retrive_metadata_for_files('/path/to/directory')
    """
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    # filter the files have format xxxx.yyyy.ext
    filtered_files = [
        f for f in files if f[:4].isdigit() and f[5:].isdigit() and f[4] == "."
    ]
    num_papers = len(filtered_files)
    log.info("There are {} files".format(num_papers))
    client = arxiv.Client(delay_seconds=5)
    slice_length = 50

    for i in range(0, num_papers, slice_length):
        filename_without_extensions = [
            os.path.splitext(f)[0] for f in filtered_files[i : i + slice_length]
        ]

        for pdf_file, result in zip(
            filtered_files[i : i + slice_length],
            client.results(arxiv.Search(id_list=filename_without_extensions)),
        ):
            old_path = os.path.join(path, pdf_file)
            category = result.primary_category
            new_path = os.path.join(path, category)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                log.info("Created directory: {}".format(new_path))
            try:
                shutil.move(old_path, new_path)
                log.info(
                    "Move file: {} to {}".format(
                        old_path,
                        new_path,
                    )
                )
            except Exception:
                log.exception(f"Error moving {old_path}")


def retrive_metadata_for_folders(path: str) -> None:
    """Retrieves metadata for subfolders in a specified path.
    It first query the primary category by the file's name, then move the
    file to the path/{category}

    Args:
        path (str): The path to the directory containing the subfolders.

    Returns:
        None

    Raises:
        None

    This function retrieves metadata for the subfolders in the specified path.
    It filters the subfolders based on a specific format, moves them to categorized directories, and logs the actions performed.

    Note:
        The function assumes that the subfolders in the specified path are in the format 'xxxx.yyyy',
        where 'xxxx' and 'yyyy' are numeric values and the length of the subfolder name is 9 characters.

    Example:
        retrive_metadata_for_folders('/path/to/directory')
    """
    subfolders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    filtered_subfolders = [
        f for f in subfolders if f[:4].isdigit() and f[5:].isdigit() and f[4] == "."
    ]
    num_papers = len(filtered_subfolders)
    log.info("There are {} subfolders".format(num_papers))
    client = arxiv.Client(delay_seconds=5)
    slice_length = 100
    for i in range(0, num_papers, slice_length):
        slice_list = filtered_subfolders[i : i + slice_length]
        for dir_name, result in zip(
            slice_list,
            client.results(arxiv.Search(id_list=slice_list)),
        ):
            old_path = os.path.join(path, dir_name)
            category = result.primary_category
            log.info(f"dir_name: {dir_name}, category: {category}")
            new_path = os.path.join(path, category)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                log.info("Created directory: {}".format(new_path))
            try:
                shutil.move(old_path, new_path)
                log.info(
                    "Move directory: {} to {}".format(
                        old_path,
                        new_path,
                    )
                )
            except Exception:
                log.exception(f"Error moving {old_path}")


def retrive_metadata(path: str) -> None:
    retrive_metadata_for_folders(path)
    retrive_metadata_for_files(path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="path to directory containing subfolders")
    args = parser.parse_args()
    # run(args.path, args.cpu_count)
    # run_v2(args.path)
    retrive_metadata(args.path)
