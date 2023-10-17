from typing import Dict, List
from PIL import Image

from pdfminer.layout import LTComponent, LTFigure
from logger import logger

log = logger.get_logger(__name__)


def intersects_bb(element1: LTComponent, element2: LTComponent) -> bool:
    """
    Check if two elements with bounding boxes intersect.

    Args:
        element1 (LTComponent): The first element with a bounding box.
        element2 (LTComponent): The second element with a bounding box.

    Returns:
        bool: True if the two elements intersect, False otherwise.
    """
    if element1.bbox[0] > element2.bbox[2] or element1.bbox[2] < element2.bbox[0]:
        return False
    if element1.bbox[1] > element2.bbox[3] or element1.bbox[3] < element2.bbox[1]:
        return False
    return True


def inside_bb(element1: LTComponent, element2: LTComponent) -> bool:
    """
    Check if element1 is completely inside element2's bounding box.

    Parameters:
        element1 (LTComponent): The first element to check.
        element2 (LTComponent): The second element to check against.

    Returns:
        bool: True if element1 is completely inside element2's bounding box,
            False otherwise.
    """
    return (
        element1.bbox[0] >= element2.bbox[0]
        and element1.bbox[1] >= element2.bbox[1]
        and element1.bbox[2] <= element2.bbox[2]
        and element1.bbox[3] <= element2.bbox[3]
    )


def on_same_side(
    element1: LTComponent, element2: LTComponent, page_width: float
) -> bool:
    """
    Check if two elements are on the same side of the page.

    Args:
        element1 (LTComponent): The first element.
        element2 (LTComponent): The second element.
        page_width (float): The width of the page.

    Returns:
        bool: True if the elements are on the same side of the page,
            False otherwise.
    """
    if element1.bbox[0] > page_width / 2 and element2.bbox[2] < page_width / 2:
        return False
    if element2.bbox[0] > page_width / 2 and element1.bbox[2] < page_width / 2:
        return False

    return True


def is_two_column(page_elements: List[LTComponent], threshold: float) -> bool:
    """
    Determines if the given page elements are arranged in a two-column layout.

    Args:
        page_elements (List[LTComponent]): A list of page elements.
        threshold (float): The threshold used to determine if an
            element belongs to a column.

    Returns:
        bool: True if the page elements are arranged in a
            two-column layout, False otherwise.
    """
    page_layout = page_elements[0]
    page_width = page_layout.bbox[2] - page_layout.bbox[0]
    one_side_elements = []
    for element in page_elements:
        if (
            element.bbox[2] < page_width / 2 - threshold  # left side
            or element.bbox[0] > page_width / 2 + threshold  # right side
        ):
            one_side_elements.append(element)

    return len(one_side_elements) > len(page_elements) / 2


def overlap_in_y_axis(
    element1: LTComponent, element2: LTComponent, is_two_column: bool, page_width: float
) -> bool:
    """
    Check if two elements overlap in the y-axis.

    Args:
        element1 (LTComponent): The first element.
        element2 (LTComponent): The second element.
        is_two_column (bool): Indicates if the elements are in a two-column layout.
        page_width (float): The width of the page.

    Returns:
        bool: True if the elements overlap in the y-axis, False otherwise.
    """
    if is_two_column and not on_same_side(element1, element2, page_width):
        return False

    # overlap on y_axis
    if element1.bbox[3] < element2.bbox[1]:
        return False
    if element2.bbox[3] < element1.bbox[1]:
        return False

    # not too far in x axis
    # if abs(element1.bbox[0] - element2.bbox[0]) > page_width / 4:
    #     return False

    return True


def merge_bb(
    file_elements: Dict[int, List[LTComponent]]
) -> Dict[int, List[LTComponent]]:
    """
    Merge bounding boxes in the given elements dictionary.

    Parameters:
    - file_elements (Dict[int, List[LTComponent]]): A dictionary where the keys
        are page indices and the values are lists of elements.

    Method:
    - delete one bb if it is inside another bb
    - merge two bb if they intersect
    - merge two bb if they are on the same side of the page and
        overlap in y axis

    Returns:
    - result (Dict[int, List[LTComponent]]): A dictionary where the keys are
        page indices and the values are lists of merged elements.
    """
    result = {}
    threshold = 0.1  # TODO: move this to config
    for page_index, page_elements in file_elements.items():
        two_column_flag = is_two_column(page_elements, threshold)
        # sort the elements by y coordinate then by x coordinate
        sorted_elements = sorted(
            page_elements, key=lambda element: (element.bbox[1], element.bbox[0])
        )
        result[page_index] = [sorted_elements[0], sorted_elements[1]]
        for index, element in enumerate(sorted_elements):
            if index <= 1:
                continue

            if isinstance(element, LTFigure):
                result[page_index].append(element)
                continue

            should_merge = False
            for i, p_e in enumerate(result[page_index]):
                if i == 0:
                    continue
                if inside_bb(element, p_e):
                    should_merge = True
                    break

                if intersects_bb(element, p_e):
                    result[page_index][i].bbox = (
                        min(p_e.bbox[0], element.bbox[0]),
                        min(p_e.bbox[1], element.bbox[1]),
                        max(p_e.bbox[2], element.bbox[2]),
                        max(p_e.bbox[3], element.bbox[3]),
                    )
                    should_merge = True

                if overlap_in_y_axis(
                    element, p_e, two_column_flag, sorted_elements[0].bbox[2]
                ):
                    result[page_index][i].bbox = (
                        min(p_e.bbox[0], element.bbox[0]),
                        min(p_e.bbox[1], element.bbox[1]),
                        max(p_e.bbox[2], element.bbox[2]),
                        max(p_e.bbox[3], element.bbox[3]),
                    )
                    should_merge = True

            if not should_merge:
                result[page_index].append(element)

    # 1. delete an element if this element is inside another element
    # 2. merge two elements if there is an overlap
    # 3. merge two elements if they lie on the same side
    #    and horizontally overlap
    return result


def transform(elements: List[LTComponent], image: Image.Image) -> List[LTComponent]:
    """
    Transform the coordinates of elements based on the size of an image.

    Method:
        It first flip the y-axis, then scale the width and height of the page
        to match the image

    Args:
        elements (List[LTComponent]): A list of elements representing bounding boxes.
        image (Image.Image): The image to use for scaling.

    Returns:
        List: A list of elements with transformed coordinates.

    Note:
        The origin of the coordinate system is the lower-left corner of the page

        However the COCO-format is the upper-left corner, so we need to flip the y-axis.

    See:
        https://cocodataset.org/#format-data (Section 1 Object detection)
    """
    image_width, image_height = image.size
    page_width, page_height = elements[0].bbox[2], elements[0].bbox[3]

    if abs(image_width / page_width - image_height / page_height) > 0.001:
        log.error(
            f"image size {(image_width, image_height)} and page size {(page_width, page_height)} are not scaled"
        )
        raise Exception("image size and page size are not scaled")

    scale = image_width / page_width
    for index, element in enumerate(elements):
        x0, y0, x1, y1 = element.bbox
        # flip the y-axis
        y0, y1 = page_height - y1, page_height - y0
        # scale
        element_width = x1 - x0
        element_height = y1 - y0
        x0 = x0 * scale
        y0 = y0 * scale
        y1 = y0 + element_height * scale
        x1 = x0 + element_width * scale
        elements[index].bbox = (x0, y0, x1, y1)
    return elements
