from dataclasses import dataclass
from typing import Dict, Optional

from pyparsing import Any


@dataclass
class BoundingBox:
    """A simple bounding box representation.
    The coordinates are in the form of (x0, y0, x1, y1)
    The origin is in the top left
     (x0, y0)+----------------+
             |                |
             |                |
             |                |
             +----------------+ (x1, y1)

    Returns:
        _type_: _description_
    """

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def __len__(self) -> int:
        return 4

    def __repr__(self) -> str:
        return f"BoundingBox({self.x0}, {self.y0}, {self.x1}, {self.y1})"

    def __getitem__(self, index: int) -> float:
        return (self.x0, self.y0, self.x1, self.y1)[index]

    def to_dict(self) -> Dict[str, Any]:
        return {"bbox": (self.x0, self.y0, self.x1, self.y1)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            x0=data["bbox"][0],
            y0=data["bbox"][1],
            x1=data["bbox"][2],
            y1=data["bbox"][3],
        )


class Block:
    current_id: int = 0

    def __init__(
        self,
        bounding_box: BoundingBox = None,
        category: int = None,
        page_index: int = None,
        previous_block: int = None,
        parent_block: int = None,
        next_block: int = None,
        source_code: str = None,
    ) -> None:
        self.id = Block.current_id
        Block.current_id += 1

        self._category = category
        self._page_index = page_index
        self._bounding_box = bounding_box
        self._previous_block = previous_block
        self._parent_block = parent_block
        self._next_block = next_block
        self._source_code = source_code

    @property
    def bbox(self):
        return self._bounding_box

    @bbox.setter
    def bbox(self, value: BoundingBox) -> None:
        self._bounding_box = value

    @property
    def block_id(self) -> int:
        return self.id

    @property
    def category(self) -> int:
        return self._category

    @category.setter
    def category(self, value: int) -> None:
        self._category = value

    @property
    def page_index(self) -> int:
        return self._page_index

    @page_index.setter
    def page_index(self, value: int) -> None:
        self._page_index = value

    @property
    def source_code(self) -> str:
        return self._source_code

    @property
    def parent_block(self) -> int:
        return self._parent_block

    @parent_block.setter
    def parent_block(self, value: int) -> None:
        self._parent_block = value

    @property
    def previous_block(self) -> int:
        return self._previous_block

    @property
    def next_block(self) -> int:
        return self._next_block

    @property
    def height(self) -> float:
        return self._bounding_box.height

    @property
    def width(self) -> float:
        return self._bounding_box.width

    def to_dict(self):
        data = self._bounding_box.to_dict()
        data.update(
            {
                "block_id": self.block_id,
                "category": self.category,
                "page_index": self.page_index,
                "previous_block": self.previous_block,
                "parent_block": self.parent_block,
                "next_block": self.next_block,
                "source_code": self.source_code,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            BoundingBox.from_dict(data["bbox"]),
            category=data["category"],
            previous_block=data["previous_block"],
            parent_block=data["parent_block"],
            next_block=data["next_block"],
            source_code=data["source_code"],
        )
