from typing import Dict, List
import os

from vrdu.block import Block
from vrdu import utils
from vrdu.config import config


def generate_quality_report(main_directory: str) -> None:
    """Generates a quality report based on the provided layout information.

    Args:
        layout_info (Dict[int, List[Block]]): A dictionary where the keys are page indices
            and the values are lists of blocks on each page.

    Returns:
        None
    """
    result_directory = os.path.join(main_directory, "output/result")

    layout_metadata_file = os.path.join(result_directory, "layout_metadata.json")
    layout_metadata = utils.load_json(layout_metadata_file)

    text_info_file = os.path.join(result_directory, "texts.json")
    text_info = utils.load_json(text_info_file)

    layout_info_file = os.path.join(result_directory, "layout_info.json")
    layout_info_data = utils.load_json(layout_info_file)
    # order_annotation_file = os.path.join(result_directory, "order_annotation.json")
    # order_annotation = utils.load_json(order_annotation_file)
    # layout_info_data = order_annotation["annotation"]
    layout_info = {
        int(key): [Block.from_dict(item) for item in values]
        for key, values in layout_info_data.items()
    }

    result = {}
    result["num_pages"] = max(layout_info.keys())
    result["num_columns"] = layout_metadata["num_columns"]
    result["category_quality"] = []

    total_reading, total_geometry = 0, 0
    for key, value in text_info.items():
        # currently, ignore graphics
        if key == config.name2category["Figure"]:
            continue

        reading_count = len(value)
        geometry_count = 0
        for page_index, blocks in layout_info.items():
            for block in blocks:
                # only major block is counted
                if (
                    block.category == config.name2category[key]
                    and block.parent_block is None
                ):
                    geometry_count += 1
        missing_rate = 0 if reading_count == 0 else 1 - geometry_count / reading_count
        result["category_quality"].append(
            {
                "category": key,
                "geometry_count": geometry_count,
                "reading_count": len(value),
                "missing_rate": missing_rate,
            }
        )

        total_reading += reading_count
        total_geometry += geometry_count
    result["category_quality"].append(
        {
            "category": "Total",
            "geometry_count": total_geometry,
            "reading_count": total_reading,
            "missing_rate": 1 - total_geometry / total_reading,
        }
    )

    result["page_quality"] = compute_overlap(layout_info)

    report_file = os.path.join(result_directory, "quality_report.json")
    utils.export_to_json(result, report_file)


def compute_overlap(layout_info: Dict[int, List[Block]]) -> List[Dict]:
    """Computes the overlap between blocks in a layout.

    Args:
        layout_info (Dict[int, List[Block]]): A dictionary where the keys are page indices
            and the values are lists of blocks on each page.

    Returns:
        List[Dict]: A list of dictionaries containing the overlap information for each page and
                    the total overlap information.

    """
    result = []
    total_area, total_overlap, total_blocks = 0, 0, 0
    for page_index in layout_info.keys():
        blocks = layout_info[page_index]
        blocks.sort(key=lambda block: block.bbox.x0)

        area, overlap = 0, 0
        for i in range(len(blocks)):
            area += blocks[i].bbox.area()
            for j in range(i + 1, len(blocks)):
                if blocks[j].bbox.x0 > blocks[i].bbox.x1:
                    break
                overlap += blocks[i].bbox.overlap(blocks[j].bbox)

        result.append(
            {
                "page": page_index,
                "num_blocks": len(blocks),
                "area": area,
                "overlap": overlap,
                "ratio": 0 if area == 0 else overlap / area,
            }
        )
        total_area += area
        total_overlap += overlap
        total_blocks += len(blocks)

    result.append(
        {
            "page": "total",
            "num_blocks": total_blocks,
            "area": total_area,
            "overlap": total_overlap,
            "ratio": 0 if total_area == 0 else total_overlap / total_area,
        }
    )

    return result
