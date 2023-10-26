from typing import Any, List, Dict
import re

import Levenshtein
from pdfminer.layout import LTTextContainer

from logger import logger
from config import config

log = logger.get_logger(__name__)


def find_closest_string(new_string: str, string_list: List[str]) -> str:
    """
    Find the closest string in a list to a given new string.

    Args:
        new_string (str): The new string for comparison.
        string_list (list): A list of strings to compare against.

    Returns:
        str: The closest string in the list to the new string.
    """
    distances = [Levenshtein.distance(new_string, s) for s in string_list]
    closest_index = distances.index(min(distances))
    closest_string = string_list[closest_index]
    return closest_string


def extract_image_paths(strings) -> List[str]:
    """
    Extracts image file paths from a list of strings
    containing the `includegraphics` command.

    Args:
        strings (list): A list of strings to search for image file paths.

    Returns:
        list: A list of extracted image file paths.
    """
    image_paths = []
    # Regular expression pattern
    pattern = r"\\includegraphics(?:\[.*?\])?\{(.*?)\}"

    for string in strings:
        matches = re.findall(pattern, string)
        image_paths.extend(matches)

    return image_paths


def generate_caption_annotation(
    geometry_infos: Dict[str, List[LTTextContainer]],
    category_infos: Dict[str, List[Dict]],
    reading_infos: Dict[str, List[Any]],
) -> Dict[str, List[Dict]]:
    """
    Generate annotations for captions based on geometry,
    category, and reading information.


    Args:
        geometry_infos (Dict[str, List[LTTextContainer]]):
            A dictionary mapping page indices to geometry information.
        category_infos (Dict[str, List[Dict]]):
            A dictionary mapping page indices to category information.
        reading_infos (Dict[str, List[Any]]):
            A dictionary mapping page indices to reading information.

    Returns:
        Dict[str, List[Dict]]:
        A dictionary representing the generated captions annotations.
    """
    result = {}

    captions = reading_infos["caption"]

    for page_index, page_elements in geometry_infos.items():
        result[page_index] = []
        category_info = category_infos[page_index]
        for index, element in enumerate(page_elements):
            if config.category2name[category_info[index]] != "Caption":
                continue

            source = find_closest_string(element.get_text(), captions)
            log.debug(f"element={element}, source={source}")
            result[int(page_index)].append(
                {
                    "id": index,
                    "image_id": page_index,
                    "category_id": category_info[index],
                    "bbox": list(element.bbox),
                    "content": [],
                    "source": source,
                }
            )

    return result


def generate_section_annotation(
    geometry_infos: Dict[str, List[LTTextContainer]],
    category_infos: Dict[str, List[Dict]],
    reading_infos: Dict[str, List[Any]],
) -> Dict[str, List[Dict]]:
    """
    Generate annotations for sections based on geometry,
    category, and reading information.


    Args:
        geometry_infos (Dict[str, List[LTTextContainer]]):
            A dictionary mapping page indices to geometry information.
        category_infos (Dict[str, List[Dict]]):
            A dictionary mapping page indices to category information.
        reading_infos (Dict[str, List[Any]]):
            A dictionary mapping page indices to reading information.

    Returns:
        Dict[str, List[Dict]]:
        A dictionary representing the generated section annotations.
    """
    result = {}

    sections = reading_infos["title"]

    for page_index, page_elements in geometry_infos.items():
        result[page_index] = []
        category_info = category_infos[page_index]
        for index, element in enumerate(page_elements):
            if config.category2name[category_info[index]] != "Title":
                continue

            source = find_closest_string(element.get_text(), sections)
            log.debug(f"element={element}, source={source}")
            result[int(page_index)].append(
                {
                    "id": index,
                    "image_id": page_index,
                    "category_id": category_info[index],
                    "bbox": list(element.bbox),
                    "content": [],
                    "source": source,
                }
            )
            continue

    return result


def generate_footnote_annotation(
    geometry_infos: Dict[str, List[LTTextContainer]],
    category_infos: Dict[str, List[Dict]],
    reading_infos: Dict[str, List[Any]],
) -> Dict[str, List[Dict]]:
    """Generate annotations for footnotes in a document.

    This function takes in page layout information extracted from a
    document and generates annotation metadata for any footnotes found.

    It identifies footnote elements, looks up the footnote text, and
    returns a dictionary of annotations grouped by page number.

    Args:
        geometry_infos: Layout of text elements by page
        category_infos: Category of each element
        reading_infos: Additional page/footnote context

    Returns:
        Dict[str, List[Dict]]: Annotations of footnotes by page number
    """
    result = {}

    footnotes = reading_infos["footnote"]

    for page_index, page_elements in geometry_infos.items():
        result[page_index] = []
        category_info = category_infos[page_index]
        for index, element in enumerate(page_elements):
            if config.category2name[category_info[index]] != "Footnote":
                continue

            source = find_closest_string(element.get_text(), footnotes)
            log.debug(f"element={element}, source={source}")
            result[int(page_index)].append(
                {
                    "id": index,
                    "image_id": page_index,
                    "category_id": category_info[index],
                    "bbox": list(element.bbox),
                    "content": [],
                    "source": source,
                }
            )
            continue

    return result


def generate_figure_annotation(
    geometry_infos: Dict[str, List[LTTextContainer]],
    category_infos: Dict[str, List[Dict]],
    reading_infos: Dict[str, List[Any]],
) -> Dict[str, List[Dict]]:
    """Generate annotations for figures in a document.

    This function takes in page layout information and generates
    annotation metadata for any figures found.

    It identifies figure elements, extracts the image paths, and
    returns a dictionary of annotations grouped by page number.

    Args:
        geometry_infos: Layout of text elements by page
        category_infos: Category of each element
        reading_infos: Additional context including figures

    Returns:
        Dict[str, List[Dict]]: Annotations of figures by page number
    """
    figures: List[str] = extract_image_paths(reading_infos["figure"])
    figure_generator = (x for x in figures)

    result = {}
    for page_index, page_elements in geometry_infos.items():
        result[page_index] = []
        category_info = category_infos[page_index]

        for index, element in enumerate(page_elements):
            if config.category2name[category_info[index]] == "Figure":
                result[page_index].append(
                    {
                        "id": index,
                        "image_id": page_index,
                        "category_id": category_info[index],
                        "bbox": list(element.bbox),
                        "content": [],
                        "source": next(figure_generator),
                    }
                )
                continue

    return result


def generate_reading_annotation(
    geometry_infos: Dict[str, List[LTTextContainer]],
    category_infos: Dict[str, List[Dict]],
    reading_infos: Dict[str, List[Any]],
) -> Dict[str, List[Dict]]:
    """Generate overall reading annotations from sub-annotations.

    This function aggregates annotation metadata from:

    - Sections (generated by generate_section_annotation)
    - Captions (generate_caption_annotation)
    - Footnotes (generate_footnote_annotation)

    It returns a single dictionary with all annotations grouped
    by page.

    Args:
        geometry_infos: Layout of text elements by page
        category_infos: Category of each element
        reading_infos: Additional context

    Returns:
        Dict[str, List[Dict]]: Aggregated annotations by page
    """
    result = {key: [] for key in geometry_infos.keys()}

    title_annotation = generate_section_annotation(
        geometry_infos, category_infos, reading_infos
    )
    for key, value in result.items():
        value.extend(title_annotation[key])

    caption_annotation = generate_caption_annotation(
        geometry_infos, category_infos, reading_infos
    )
    for key, value in result.items():
        value.extend(caption_annotation[key])

    footnote_annotation = generate_footnote_annotation(
        geometry_infos, category_infos, reading_infos
    )
    for key, value in result.items():
        value.extend(footnote_annotation[key])

    return result
