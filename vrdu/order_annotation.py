import re
import os
from uuid import uuid4

from vrdu.block import Block
from vrdu.config import config
from vrdu import utils


class OrderAnnotation:
    def __init__(self, tex_file: str) -> None:
        self.tex_file = tex_file
        self.main_directory = os.path.dirname(tex_file)
        self.result_directory = os.path.join(self.main_directory, "output/result")
        layout_info_file = os.path.join(self.result_directory, "layout_info.json")
        layout_info_data = utils.load_json(layout_info_file)
        layout_info = {
            int(key): [Block.from_dict(item) for item in values]
            for key, values in layout_info_data.items()
        }

        # result
        self.annotations = {}
        self.annotations["annotations"] = [
            _block
            for page_index in layout_info.keys()
            for _block in layout_info[page_index]
        ]

    def annotate(self):
        self.annotations["orders"] = []
        self.generate_sortable_envs_order()

        self.generate_float_envs_order()

        self.generate_cross_reference_order()

        order_annotation_file = os.path.join(
            self.result_directory, "order_annotation.json"
        )

        transformed_annotations = {
            "annotations": [x.to_dict() for x in self.annotations["annotations"]],
            "orders": self.annotations["orders"],
        }

        utils.export_to_json(transformed_annotations, order_annotation_file)

    def generate_cross_reference_order(self):
        annotations = []

        # map from label to block_id
        label_to_block_id = {}
        for block in self.annotations["annotations"]:
            if not block.labels:
                continue
            for _label in block.labels:
                label_to_block_id[_label] = block.block_id

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
        # generate reference according to label
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] not in ["Text", "Text-EQ"]:
                continue
            block.references = [
                x
                for group in re.findall(ref_patterns, block.source_code)
                for x in group
                if x
            ]
            for _label in block.references:
                if _label in label_to_block_id:
                    annotations.append(
                        {
                            "type": "explicit-cite",
                            "from": block.block_id,
                            "to": label_to_block_id[_label],
                        }
                    )

        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Caption":
                continue
            if not block.references:
                continue
            for _label in block.references:
                if _label not in label_to_block_id:
                    continue
                annotations.append(
                    {
                        "type": "implicit-cite",
                        "from": block.block_id,
                        "to": label_to_block_id[_label],
                    }
                )

        self.annotations["orders"].extend(annotations)

    def generate_float_envs_order(self):
        # annotations = []
        pattern = r"\\label\{(.*?)\}"
        # 0, add labels for titles
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Title":
                continue
            block.labels = re.findall(pattern, block.source_code)

        # 1. add labels for equations
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Equation":
                continue
            block.labels = re.findall(pattern, block.source_code)

        # 2. match caption to tabulars and generate labels
        with open(self.tex_file, "r") as f:
            latex_content = f.read()
        # find the intetval of tables
        table_pattern = re.compile(
            r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", re.DOTALL
        )
        table_indices = []
        for _match in table_pattern.finditer(latex_content):
            table_indices.append((_match.start(), _match.end(), str(uuid4())))

        # find the interval of tabulars
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Table":
                continue
            start_index = latex_content.find(block.source_code)
            if start_index == -1:
                continue
            end_index = start_index + len(block.source_code)

            for table_index in table_indices:
                if start_index >= table_index[0] and end_index <= table_index[1]:
                    labels = re.findall(
                        pattern, latex_content[table_index[0] : table_index[1]]
                    )
                    block.labels = labels
                    if not block.labels:
                        block.labels = [table_index[2]]
        # find the interval of captions
        for block in self.annotations["annotations"]:
            if config.category2name[block.category] != "Caption":
                continue
            start_index = latex_content.find(block.source_code)
            if start_index == -1:
                continue
            end_index = start_index + len(block.source_code)
            for table_index in table_indices:
                if start_index >= table_index[0] and end_index <= table_index[1]:
                    labels = re.findall(
                        pattern, latex_content[table_index[0] : table_index[1]]
                    )
                    block.references = labels
                    if not block.references:
                        block.references = [table_index[2]]
        # match caption to tables and generate labels

        # 3. match caption to figure and generate labels
        # TODO: complete this
        # 4. match caption to algorithms and generate labels

        # 5. match caption to codings and generate labels

        # caption to env
        # label to env
        # 1. caption-env attach, implicit cite and add label
        # 2. equation-label attach, add label
        # self.annotations["orders"].extend(annotations)

    def generate_sortable_envs_order(self):
        annotations = []
        sortable_categories = [
            config.name2category[name] for name in config.sortable_categories
        ]

        sortable_elements = [
            _block
            for _block in self.annotations["annotations"]
            if _block.category in sortable_categories
        ]

        title_categories = [
            config.name2category[x] for x in ["Title", "PaperTitle", "Abstract"]
        ]

        text_categories = [
            config.name2category[x] for x in ["Text", "Text-EQ", "Equation", "List"]
        ]

        stack = []
        for index, element in enumerate(sortable_elements):
            if index == 0 or not stack:
                stack.append(element)
                continue

            # case 0: both corresponding to the same text, mark as identical
            if element.parent_block == stack[-1].block_id:
                annotations.append(
                    {
                        "type": "identical",
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                stack.pop()
                stack.append(element)
                continue

            # case 1: both in the text category, mark as adj
            if (
                element.category in text_categories
                and stack[-1].category in text_categories
            ):
                annotations.append(
                    {
                        "type": "adj",
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                stack.pop()
                stack.append(element)
                continue

            # case 2: current in text, prev in title, mark as sub
            if (
                element.category in text_categories
                and stack[-1].category in title_categories
            ):
                if element.category != stack[-1].category:
                    annotations.append(
                        {
                            "type": "sub",
                            "from": element.block_id,
                            "to": stack[-1].block_id,
                        }
                    )
                    stack.append(element)
                    continue

            # case 3: current in title, prev in text, find the most recent title
            if (
                element.category in title_categories
                and stack[-1].category in text_categories
            ):
                while stack and stack[-1].category not in title_categories:
                    stack.pop()

                if not stack:
                    stack.append(element)
                    continue

                annotations.append(
                    {
                        "type": "peer",
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                stack.append(element)
                continue

            # case 4: both in titles, mark as peer
            if (
                element.category in title_categories
                and stack[-1].category in title_categories
            ):
                annotations.append(
                    {
                        "type": "peer",
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                stack.pop()
                stack.append(element)
                continue

        self.annotations["orders"].extend(annotations)
