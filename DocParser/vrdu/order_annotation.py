import re
from uuid import uuid4
from pathlib import Path
from typing import Dict, List, Any

from DocParser.vrdu.block import Block
from DocParser.vrdu.config import config
from DocParser.vrdu import utils


class OrderAnnotation:
    """Handles annotation of reading order relationships between document elements."""

    def __init__(self, tex_file: Path) -> None:
        """Initialize order annotation for a LaTeX file.

        Args:
            tex_file: Path to the LaTeX file
        """
        self.tex_file = tex_file
        self.main_directory = tex_file.parent
        self.result_directory = self.main_directory / "output/result"

        # Load layout info
        layout_info_file = self.result_directory / "layout_info.json"
        layout_info_data = utils.load_json(layout_info_file)
        layout_info = {
            int(key): [Block.from_dict(item) for item in values]
            for key, values in layout_info_data.items()
        }

        # Initialize annotations
        self.annotations: Dict[str, Any] = {
            "annotations": [
                block for page_blocks in layout_info.values() for block in page_blocks
            ],
            "orders": [],
        }

    def annotate(self) -> None:
        """Generate and save all order annotations."""
        # Generate different types of order relationships
        self.generate_sortable_envs_order()
        self.generate_float_envs_order()
        self.generate_cross_reference_order()

        # Save annotations
        order_annotation_file = self.result_directory / "order_annotation.json"
        transformed_annotations = {
            "annotations": [x.to_dict() for x in self.annotations["annotations"]],
            "orders": self.annotations["orders"],
        }
        utils.export_to_json(transformed_annotations, order_annotation_file)

    def generate_cross_reference_order(self) -> None:
        """Generate order annotations for cross-references."""
        annotations: List[Dict[str, str]] = []

        # Build label to block ID mapping
        label_to_block_id = {
            label: block.block_id
            for block in self.annotations["annotations"]
            if block.labels
            for label in block.labels
        }

        # Reference patterns to match
        ref_patterns = "|".join(
            [
                r"\\ref\{(.*?)\}",
                r"\\eqref\{(.*?)\}",
                r"\\pageref\{(.*?)\}",
                r"\\autoref\{(.*?)\}",
                r"\\vref\{(.*?)\}",
                r"\\cref\{(.*?)\}",
                r"\\labelcref\{(.*?)\}",
            ]
        )

        # Process text blocks
        for block in self.annotations["annotations"]:
            category = config.category2name[block.category]

            # Handle text and equation references
            if category in ["Text", "Text-EQ"]:
                block.references = self._extract_references(
                    block.source_code, ref_patterns
                )
                self._add_reference_annotations(
                    block, label_to_block_id, annotations, "explicit-cite"
                )

            # Handle caption references
            elif category == "Caption" and block.references:
                self._add_reference_annotations(
                    block, label_to_block_id, annotations, "implicit-cite"
                )

            # Handle table and algorithm references
            elif category in ["Table", "Algorithm"]:
                block.references = self._extract_references(
                    block.source_code, ref_patterns
                )
                self._add_reference_annotations(
                    block, label_to_block_id, annotations, "explicit-cite"
                )

        self.annotations["orders"].extend(annotations)

    def _extract_references(self, text: str, pattern: str) -> List[str]:
        """Extract reference labels from text using pattern."""
        return [x for group in re.findall(pattern, text) for x in group if x]

    def _add_reference_annotations(
        self,
        block: Block,
        label_map: Dict[str, str],
        annotations: List[Dict[str, str]],
        ref_type: str,
    ) -> None:
        """Add reference annotations for a block."""
        for label in block.references:
            if label in label_map:
                annotations.append(
                    {"type": ref_type, "from": block.block_id, "to": label_map[label]}
                )

    def generate_float_envs_order(self) -> None:
        """Generate order annotations for floating environments."""
        with open(self.tex_file, "r") as f:
            latex_content = f.read()

        # Process title labels
        self._process_title_labels(latex_content)

        # Process equation labels
        self._process_equation_labels()

        # Process float environment labels
        category_patterns = {
            "Table": r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}",
            "Figure": r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}",
            "Algorithm": r"\\begin\{algorithm\*?\}(.*?)\\end\{algorithm\*?\}",
        }

        category_indices = {
            category: [
                (match.start(), match.end(), str(uuid4()))
                for match in re.finditer(pattern, latex_content, re.DOTALL)
            ]
            for category, pattern in category_patterns.items()
        }

        label_pattern = r"\\label\{(.*?)\}"

        # Process each category
        for category, indices in category_indices.items():
            self._process_float_env_labels(
                category, indices, latex_content, label_pattern
            )

    def _process_title_labels(self, latex_content: str) -> None:
        """Process and add labels for title blocks."""
        label_pattern = r"\\label\{(.*?)\}"

        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Title":
                continue

            block.labels = re.findall(label_pattern, block.source_code)

            # Find additional labels after the title
            start_idx = latex_content.find(block.source_code)
            if start_idx == -1:
                continue

            end_idx = start_idx + len(block.source_code)
            matches = re.finditer(label_pattern, latex_content[end_idx:], re.DOTALL)

            for match in matches:
                label_start = match.start() + end_idx
                label_end = match.end() + end_idx
                label_content = latex_content[label_start:label_end]

                if latex_content[end_idx:label_start].isspace():
                    block.labels.extend(re.findall(label_pattern, label_content))
                break

    def _process_equation_labels(self) -> None:
        """Process and add labels for equation blocks."""
        label_pattern = r"\\label\{(.*?)\}"

        for block in self.annotations["annotations"]:
            if config.category2name[block.category] == "Equation":
                block.labels = re.findall(label_pattern, block.source_code)

    def _process_float_env_labels(
        self,
        category: str,
        indices: List[tuple],
        latex_content: str,
        label_pattern: str,
    ) -> None:
        """Process and add labels for floating environment blocks."""
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != category:
                continue

            start_idx = latex_content.find(block.source_code)
            if start_idx == -1:
                continue

            end_idx = start_idx + len(block.source_code)

            for idx_start, idx_end, uuid in indices:
                if not (start_idx >= idx_start and end_idx <= idx_end):
                    continue

                labels = re.findall(label_pattern, latex_content[idx_start:idx_end])
                block.labels = labels
                block.labels.append(uuid)

        # Process caption references
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Caption":
                continue

            start_idx = latex_content.find(block.source_code)
            if start_idx == -1:
                continue

            end_idx = start_idx + len(block.source_code)

            for idx_start, idx_end, uuid in indices:
                if start_idx >= idx_start and end_idx <= idx_end:
                    block.references = [uuid]

    def generate_sortable_envs_order(self) -> None:
        """Generate order annotations for sortable environments."""
        annotations: List[Dict[str, str]] = []

        # Get relevant category IDs
        sortable_cats = [
            config.name2category[name] for name in config.sortable_categories
        ]
        title_cats = [
            config.name2category[name] for name in ["Title", "PaperTitle", "Abstract"]
        ]
        text_cats = [
            config.name2category[name]
            for name in ["Text", "Text-EQ", "Equation", "List"]
        ]

        # Get sortable elements
        sortable_elements = [
            block
            for block in self.annotations["annotations"]
            if block.category in sortable_cats
        ]

        stack: List[Block] = []
        for idx, element in enumerate(sortable_elements):
            if idx == 0 or not stack:
                stack.append(element)
                continue

            # Handle different cases
            if element.parent_block == stack[-1].block_id:
                self._add_order_annotation(annotations, element, stack[-1], "identical")
                stack.pop()
                stack.append(element)

            elif element.category in text_cats and stack[-1].category in text_cats:
                self._add_order_annotation(annotations, element, stack[-1], "adj")
                stack.pop()
                stack.append(element)

            elif (
                element.category in text_cats
                and stack[-1].category in title_cats
                and element.category != stack[-1].category
            ):
                self._add_order_annotation(annotations, element, stack[-1], "sub")
                stack.append(element)

            elif element.category in title_cats and stack[-1].category in text_cats:
                while stack and stack[-1].category not in title_cats:
                    stack.pop()

                if stack:
                    self._add_order_annotation(annotations, element, stack[-1], "peer")
                stack.append(element)

            elif element.category in title_cats and stack[-1].category in title_cats:
                self._add_order_annotation(annotations, element, stack[-1], "peer")
                stack.pop()
                stack.append(element)

            elif element.category == config.name2category["Footnote"]:
                self._add_order_annotation(
                    annotations, element, stack[-1], "explicit-cite"
                )

        self.annotations["orders"].extend(annotations)

    def _add_order_annotation(
        self,
        annotations: List[Dict[str, str]],
        from_block: Block,
        to_block: Block,
        rel_type: str,
    ) -> None:
        """Add an order annotation between two blocks."""
        annotations.append(
            {"type": rel_type, "from": from_block.block_id, "to": to_block.block_id}
        )
