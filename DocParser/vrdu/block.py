from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, cast


@dataclass
class BoundingBox:
    """A bounding box representation with coordinates (x0,y0) for top-left and (x1,y1) for bottom-right.
    Origin is at top-left of the page."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Width of bounding box"""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Height of bounding box"""
        return self.y1 - self.y0

    def __len__(self) -> int:
        return 4

    def __repr__(self) -> str:
        return f"BoundingBox({self.x0}, {self.y0}, {self.x1}, {self.y1})"

    def __getitem__(self, index: int) -> float:
        return (self.x0, self.y0, self.x1, self.y1)[index]

    def area(self) -> float:
        """Calculate area of bounding box"""
        return abs(self.width * self.height)

    def overlap(self, other: "BoundingBox") -> float:
        """Calculate overlap area with another bounding box"""
        if (
            self.x0 > other.x1
            or self.x1 < other.x0
            or self.y0 > other.y1
            or self.y1 < other.y0
        ):
            return 0.0

        x_overlap = max(0, min(self.x1, other.x1) - max(self.x0, other.x0))
        y_overlap = max(0, min(self.y1, other.y1) - max(self.y0, other.y0))
        return x_overlap * y_overlap

    def to_dict(self) -> Dict[str, Tuple[float, float, float, float]]:
        """Convert to dictionary format"""
        return {"bbox": self.to_tuple()}

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Convert to tuple format"""
        return (self.x0, self.y0, self.x1, self.y1)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BoundingBox":
        """Create BoundingBox from dictionary"""
        bbox = data["bbox"]
        return cls(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3])

    @classmethod
    def from_list(
        cls, data: List[Tuple[float, float, float, float, float, float]]
    ) -> "BoundingBox":
        """Create bounding box that encompasses all points in list"""
        min_x = min(data, key=lambda x: x[1])[1]
        min_y = min(data, key=lambda x: x[0])[0]
        max_x = max(data, key=lambda x: x[4])[4]
        max_y = max(data, key=lambda x: x[3])[3]
        return cls(x0=min_x, y0=min_y, x1=max_x, y1=max_y)


class Block:
    """Represents a block of content with position and metadata"""

    current_id: int = 0

    def __init__(
        self,
        bounding_box: BoundingBox,
        block_id: Optional[int] = None,
        category: Optional[int] = None,
        page_index: Optional[int] = None,
        previous_block: Optional[int] = None,
        parent_block: Optional[int] = None,
        next_block: Optional[int] = None,
        source_code: Optional[str] = None,
        labels: Optional[List[str]] = None,
        references: Optional[List[str]] = None,
    ) -> None:
        self.id = block_id if block_id is not None else Block.current_id
        if block_id is None:
            Block.current_id += 1

        self._category: Optional[int] = category
        self._page_index: Optional[int] = page_index
        self._bounding_box: BoundingBox = bounding_box
        self._previous_block: Optional[int] = previous_block
        self._parent_block: Optional[int] = parent_block
        self._next_block: Optional[int] = next_block
        self._source_code: Optional[str] = source_code
        self._labels: Optional[List[str]] = labels or []
        self._references: Optional[List[str]] = references or []

    def __repr__(self) -> str:
        return (
            f"Block(id={self.id}, category={self.category}, "
            f"page_index={self.page_index}, bbox={self.bbox}, "
            f"source_code={self.source_code})"
        )

    @property
    def bbox(self) -> BoundingBox:
        return self._bounding_box

    @bbox.setter
    def bbox(self, value: BoundingBox) -> None:
        self._bounding_box = value

    @property
    def labels(self) -> List[str]:
        return cast(List[str], self._labels or [])

    @labels.setter
    def labels(self, value: List[str]) -> None:
        self._labels = value

    @property
    def references(self) -> List[str]:
        return cast(List[str], self._references or [])

    @references.setter
    def references(self, value: List[str]) -> None:
        self._references = value

    @property
    def block_id(self) -> int:
        return self.id

    @property
    def category(self) -> int:
        return cast(int, self._category or 0)

    @category.setter
    def category(self, value: int) -> None:
        self._category = value

    @property
    def page_index(self) -> int:
        return cast(int, self._page_index or 0)

    @page_index.setter
    def page_index(self, value: int) -> None:
        self._page_index = value

    @property
    def source_code(self) -> str:
        return cast(str, self._source_code or "")

    @source_code.setter
    def source_code(self, value: str) -> None:
        self._source_code = value

    @property
    def parent_block(self) -> int:
        return cast(int, self._parent_block or -1)

    @parent_block.setter
    def parent_block(self, value: int) -> None:
        self._parent_block = value

    @property
    def previous_block(self) -> int:
        return cast(int, self._previous_block or -1)

    @property
    def next_block(self) -> int:
        return cast(int, self._next_block or -1)

    @property
    def height(self) -> float:
        return self._bounding_box.height

    @property
    def width(self) -> float:
        return self._bounding_box.width

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary format"""
        data = {
            "block_id": self.block_id,
            "category": self.category,
            "page_index": self.page_index,
            "previous_block": self.previous_block,
            "parent_block": self.parent_block,
            "next_block": self.next_block,
            "source_code": self.source_code,
            "labels": self.labels,
            "references": self.references,
            "bbox": self._bounding_box.to_tuple(),
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        """Create Block from dictionary"""
        return cls(
            block_id=data["block_id"],
            bounding_box=BoundingBox.from_dict(data),
            category=data["category"],
            previous_block=data["previous_block"],
            parent_block=data["parent_block"],
            next_block=data["next_block"],
            source_code=data["source_code"],
            page_index=data["page_index"],
        )
