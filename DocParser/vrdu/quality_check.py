"""Quality check module for analyzing layout and text information."""

from typing import Dict, List, Any
from pathlib import Path

from DocParser.vrdu.block import Block
from DocParser.vrdu import utils
from DocParser.vrdu.config import config


def generate_quality_report(main_directory: Path) -> None:
    """Generate a quality report analyzing layout and text information.

    Analyzes layout metadata, text content, and block positioning to generate
    a quality report with metrics like missing content rates and block overlaps.

    Args:
        main_directory: Base directory containing the input files
    """
    result_dir = main_directory / "output" / "result"

    # Load input files
    layout_metadata = utils.load_json(result_dir / "layout_metadata.json")
    text_info = utils.load_json(result_dir / "texts.json")
    layout_info_data = utils.load_json(result_dir / "layout_info.json")

    # Convert layout info to Block objects
    layout_info = _convert_layout_info(layout_info_data)

    # Generate report
    result = {
        "num_pages": max(layout_info.keys()),
        "num_columns": layout_metadata["num_columns"],
        "category_quality": _analyze_category_quality(layout_info, text_info),
        "page_quality": _analyze_page_quality(layout_info),
    }

    # Save report
    utils.export_to_json(result, result_dir / "quality_report.json")


def _convert_layout_info(layout_info_data: Dict) -> Dict[int, List[Block]]:
    """Convert raw layout info data to Block objects.

    Args:
        layout_info_data: Raw layout info dictionary from JSON

    Returns:
        Dictionary mapping page numbers to lists of Block objects
    """
    return {
        int(key): [Block.from_dict(item) for item in values]
        for key, values in layout_info_data.items()
    }


def _analyze_category_quality(
    layout_info: Dict[int, List[Block]], text_info: Dict[str, List[Any]]
) -> List[Dict[str, Any]]:
    """Analyze quality metrics for each content category.

    Compares text content vs geometric blocks to identify missing content.
    Calculates metrics like counts and missing rates for each category.

    Args:
        layout_info: Page index to list of Block objects mapping
        text_info: Category name to list of text content mapping

    Returns:
        List of quality metrics per category including totals
    """
    quality_metrics = []
    total_reading = total_geometry = 0

    for category, texts in text_info.items():
        # Skip figure analysis since they're handled differently
        if category == config.name2category["Figure"]:
            continue

        reading_count = len(texts)
        geometry_count = _count_category_blocks(layout_info, category)

        missing_rate = _calculate_missing_rate(reading_count, geometry_count)

        quality_metrics.append(
            {
                "category": category,
                "geometry_count": geometry_count,
                "reading_count": reading_count,
                "missing_rate": missing_rate,
            }
        )

        total_reading += reading_count
        total_geometry += geometry_count

    # Add aggregate metrics
    quality_metrics.append(
        {
            "category": "Total",
            "geometry_count": total_geometry,
            "reading_count": total_reading,
            "missing_rate": _calculate_missing_rate(total_reading, total_geometry),
        }
    )

    return quality_metrics


def _calculate_missing_rate(reading_count: int, geometry_count: int) -> float:
    """Calculate missing rate between reading and geometry counts.

    Args:
        reading_count: Number of text elements found
        geometry_count: Number of geometric blocks found

    Returns:
        Missing rate as a float between 0 and 1
    """
    return 0 if reading_count == 0 else 1 - geometry_count / reading_count


def _count_category_blocks(layout_info: Dict[int, List[Block]], category: str) -> int:
    """Count number of top-level blocks of a given category.

    Only counts blocks that don't have a parent block (top-level blocks).

    Args:
        layout_info: Page index to list of Block objects mapping
        category: Category to count

    Returns:
        Number of blocks found
    """
    count = 0
    for blocks in layout_info.values():
        count += sum(
            1
            for block in blocks
            if block.category == config.name2category[category]
            and block.parent_block is None
        )
    return count


def _analyze_page_quality(layout_info: Dict[int, List[Block]]) -> List[Dict[str, Any]]:
    """Analyze quality metrics for each page.

    Calculates area and overlap metrics for blocks on each page.
    Includes total metrics across all pages.

    Args:
        layout_info: Page index to list of Block objects mapping

    Returns:
        List of quality metrics per page including totals
    """
    metrics = []
    total_area = total_overlap = total_blocks = 0

    for page_index, blocks in layout_info.items():
        blocks.sort(key=lambda block: block.bbox.x0)

        area = sum(block.bbox.area() for block in blocks)
        overlap = _calculate_page_overlap(blocks)
        overlap_ratio = 0 if area == 0 else overlap / area

        metrics.append(
            {
                "page": page_index,
                "num_blocks": len(blocks),
                "area": area,
                "overlap": overlap,
                "ratio": overlap_ratio,
            }
        )

        total_area += area
        total_overlap += overlap
        total_blocks += len(blocks)

    # Add aggregate metrics
    metrics.append(
        {
            "page": "total",
            "num_blocks": total_blocks,
            "area": total_area,
            "overlap": total_overlap,
            "ratio": 0 if total_area == 0 else total_overlap / total_area,
        }
    )

    return metrics


def _calculate_page_overlap(blocks: List[Block]) -> float:
    """Calculate total overlap area between blocks on a page.

    Blocks must be sorted by x0 coordinate for early termination optimization.

    Args:
        blocks: List of blocks sorted by x0 coordinate

    Returns:
        Total overlap area between all blocks
    """
    overlap = 0
    for i, block in enumerate(blocks[:-1]):
        for other in blocks[i + 1 :]:
            # Early termination - no more overlaps possible
            if other.bbox.x0 > block.bbox.x1:
                break
            overlap += block.bbox.overlap(other.bbox)
    return overlap
