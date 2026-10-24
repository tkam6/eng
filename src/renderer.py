import atexit
import curses as cur
import math
import sys
import typing as ty

import numpy as np

from src import general

if ty.TYPE_CHECKING:
    from src import objects

np.set_printoptions(threshold=sys.maxsize)


class Win:
    def __init__(self, scr: cur.window) -> None:
        self.scr = scr
        cur.noecho()
        cur.cbreak()
        cur.curs_set(0)
        self.scr.nodelay(True)
        self.scr.keypad(True)

        self.term_sz = self.scr.getmaxyx()
        self.clear = self.scr.clear
        self.erase = self.scr.erase
        self.refresh = self.scr.refresh

        self.screen_buf = np.empty((0, 0), dtype="U1")
        self.attr_buf = np.empty((0, 0), dtype=np.int32)
        self.f = open("log.log", "a+")
        atexit.register(self.f.close)

    def addch(self, y: int, x: int, c: str, attr: int) -> None:
        try:
            self.scr.addch(y, x, c, attr)
        except cur.error:
            if y != self.term_sz[0] - 1 or x != self.term_sz[1] - 1:
                raise

    def addnstr(self, y: int, x: int, s: str, n: int, attr: int) -> None:
        try:
            self.scr.addnstr(y, x, s, n, attr)
        except cur.error:
            if y != self.term_sz[0] - 1:
                raise

    def chk_cell_visibility(self, y: int, x: int) -> bool:
        return 0 <= y < self.term_sz[0] and 0 <= x < self.term_sz[1]

    def get_bitwise_or(self, arr: ty.Iterable[int]) -> int | None:
        if not arr:
            return 0
        res = arr[0]
        for i in arr[1 :]:
            res = res | i
        return res

    def draw(self, obj_list: "dict[str, objects.BaseObj]") -> None:
        self.term_sz = self.scr.getmaxyx()
        if self.screen_buf.shape != self.term_sz or self.attr_buf.shape != self.term_sz:
            self.screen_buf = np.empty(self.term_sz, dtype="U1")
            self.attr_buf = np.empty(self.term_sz, dtype=np.int32)
        self.screen_buf.fill("\x00")
        self.attr_buf.fill(0)

        for obj in obj_list:
            name = obj.name
            width = obj.width(self, obj) if callable(obj.width) else obj.width
            height = obj.height(self, obj) if callable(obj.height) else obj.height
            y = obj.y(self, obj) if callable(obj.y) else obj.y
            x = obj.x(self, obj) if callable(obj.x) else obj.x
            line_range = (
                obj.line_range[0](self, obj) if callable(obj.line_range[0]) else obj.line_range[0],
                obj.line_range[1](self, obj) if callable(obj.line_range[1]) else obj.line_range[1],
            )
            col_range = (
                obj.col_range[0](self, obj) if callable(obj.col_range[0]) else obj.col_range[0],
                obj.col_range[1](self, obj) if callable(obj.col_range[1]) else obj.col_range[1],
            )
            line_range1 = line_range[1]
            col_range1 = col_range[1]
            new_buf = np.full((height, width), "\x00", dtype="U1")
            attr_new_buf = np.zeros((height, width), dtype=np.int32)

            # line and column ranges first indices aren't supposed to be inf
            if math.isinf(line_range[0]):
                raise RuntimeError(f"Object {name!r}: Line range first element cannot be inf")
            if math.isinf(col_range[0]):
                raise RuntimeError(f"Object {name!r}: Column range first element cannot be inf")
            # if line or column ranges second indices are inf, change them to
            # length of corresponding whatever
            if math.isinf(line_range1):
                line_range1 = len(obj.content)
            if math.isinf(col_range1):
                col_range1 = (
                    len(max([line for line, *attrs in obj.content], key=len))
                    if obj.content else 0
                )
            # extract lines and columns that are in range
            lines = obj.content[line_range[0] : line_range1]
            to_draw = [
                (line[col_range[0] : col_range1], attrs)
                for line, *attrs in lines
            ]

            # this block is to merge attributes
            # len_to_draw = len(to_draw)
            # idx = -1
            # while idx < len_to_draw - 1:
            #     idx += 1
            #     elem = to_draw[idx]
            #     string = elem[0]
            #     attrs = elem[1]
            #     if "\n" not in string:
            #         if idx == len_to_draw - 1:
            #             continue
            #         elem_next = to_draw[idx + 1]
            #         # check if attributes of current and next element are same,
            #         # in which case they can be clubbed together
            #         if attrs == elem_next[1]:
            #             to_draw[idx] = (string + elem_next[0], attrs)
            #             to_draw.pop(idx + 1)
            #             len_to_draw = len(to_draw)
            #         continue
            #     tmp = string.partition("\n")
            #     to_draw[idx] = (tmp[0], attrs)
            #     to_draw.insert(idx + 1, (tmp[2], attrs))
            #     len_to_draw = len(to_draw)

            idx = -1
            nl_count = 0
            start_idx = 0
            len_to_draw = len(to_draw)

            # draw only top-left-most part of extracted range lines and columns
            while idx < len_to_draw - 1:
                idx += 1
                print("nl_count =", nl_count, file=general.f) if idx == len_to_draw - 1 else None
                if nl_count >= height:
                    break
                if y + nl_count > self.term_sz[0] - 1:
                    break

                elem = to_draw[idx]
                string = elem[0]
                attrs = elem[1]
                exploded = string.split("\n")
                len_exploded_minus_1 = len(exploded) - 1

                for i, part in enumerate(exploded):
                    # carry over start_idx from previous to_draw element if
                    # it's the first element in exploded, because previous
                    # element might not have had a "\n" at end, intending to
                    # continue on same line
                    start_idx = 0 if i != 0 else start_idx
                    len_part = len(part)
                    # factor is amount of chars from current part that can be
                    # dislpayed; terrible naming, i know
                    factor = len_part
                    if start_idx >= width:
                        break
                    if width < start_idx + factor:
                        factor = width - start_idx
                    new_buf[nl_count, start_idx : start_idx + factor] = list(part)[: factor]
                    attr_new_buf[nl_count, start_idx : start_idx + factor] = self.get_bitwise_or(attrs)
                    start_idx += factor
                    # this crappy thing is done to ensure that nl_count is not
                    # incremented for the last element, because the next
                    # to_draw element may be intended to appear on the same
                    # line. if the last char is a "\n", since we're doing
                    # string.split("\n"), nl_count will be incremented as
                    # intended
                    nl_count += 1 if i != len_exploded_minus_1 else 0


            # for idx, (line, attrs) in enumerate(to_draw[: height]):
            #     if y + idx > self.term_sz[0] - 1:
            #         break

            #     line_trimmed = line[: width]

            #     new_buf[idx, : len(line_trimmed)] = list(line_trimmed)
            #     attr_new_buf[idx, : len(line_trimmed)] = self.get_bitwise_or(attrs)

            obj_y_start = max(0, -y)
            obj_x_start = max(0, -x)
            screen_y_start = max(0, y)
            screen_x_start = max(0, x)

            visible_y_len = min(height - obj_y_start, self.term_sz[0] - screen_y_start)
            visible_x_len = min(width - obj_x_start, self.term_sz[1] - screen_x_start)

            obj_y_end = obj_y_start + visible_y_len
            obj_x_end = obj_x_start + visible_x_len
            screen_y_end = screen_y_start + visible_y_len
            screen_x_end = screen_x_start + visible_x_len

            obj_part = new_buf[obj_y_start : obj_y_end, obj_x_start : obj_x_end]
            screen_part = self.screen_buf[screen_y_start : screen_y_end, screen_x_start : screen_x_end]
            mask = obj_part != "\x00"
            screen_part[:] = np.where(mask, obj_part, screen_part)

            # for attributes
            attr_obj_part = attr_new_buf[obj_y_start : obj_y_end, obj_x_start : obj_x_end]
            attr_screen_part = self.attr_buf[screen_y_start : screen_y_end, screen_x_start : screen_x_end]
            attr_mask = attr_obj_part != 0
            attr_screen_part[:] = np.where(attr_mask, attr_obj_part, attr_screen_part)

        for i in range(self.screen_buf.shape[0]):
            row = self.screen_buf[i]
            attr_row = self.attr_buf[i]
            row[row == "\x00"] = " "

            change_idxs = np.flatnonzero(np.diff(attr_row)) + 1
            starts = np.concatenate(([0], change_idxs))
            ends = np.concatenate((change_idxs, [len(attr_row)]))

            for start, end in zip(starts, ends):
                run_len = end - start
                s = row[start : end].view(f"U{run_len}")[0]
                self.addnstr(i, start, s, run_len, int(attr_row[start]))
