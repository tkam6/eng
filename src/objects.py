import dataclasses as dcs
import typing as ty

from src import general

if ty.TYPE_CHECKING:
    from src import renderer

type Dimen = int | ty.Callable[["renderer.Win"], int]
type Anchor = tuple[Dimen, Dimen]
type Range = tuple[Dimen, Dimen | float]


@dcs.dataclass
class BaseObj:
    name: str
    width: Dimen
    height: Dimen
    y: Dimen
    x: Dimen
    # note that you need to insert "\n"s in the content, wherever you like, to
    # make newlines
    content: list[str]
    line_range: Range
    col_range: Range

    def __eq__(self, other: object) -> bool:
        # TODO: just return False; this is for debugging and testing purposes
        if not isinstance(other, BaseObj):
            raise TypeError(f"Cannot compare {self.__class__.__name__} and {other.__class__.__name__} for equality")
        res = (self.buf == other.buf).all() if None not in (self.buf, other.buf) else False
        for attr in self.__annotations__:
            if attr == "buf":
                continue
            res = res and getattr(self, attr) == getattr(other, attr)
        return res


def anchor_vert_centre(win: "renderer.Win", obj: BaseObj) -> int:
    if callable(obj.height):
        return (win.term_sz[0] - obj.height(win, obj)) // 2
    return (win.term_sz[0] - obj.height) // 2


def anchor_hori_centre(win: "renderer.Win", obj: BaseObj) -> int:
    if callable(obj.width):
        return (win.term_sz[1] - obj.width(win, obj)) // 2
    return (win.term_sz[1] - obj.width) // 2


anchor_centre = (anchor_vert_centre, anchor_hori_centre)
