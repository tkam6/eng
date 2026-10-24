#!/usr/bin/env -S python3 -BOO
import cProfile
import curses as cur
import datetime as dt
import io
import math
import pstats
import time

from src import general, objects, renderer

prof = cProfile.Profile()
total = 0
frames = 0


def start(scr: cur.window) -> list[int]:
    global total, frames

    win = renderer.Win(scr)
    obj_list = [
        objects.BaseObj(
            name="base-obj-test",
            height=lambda win, obj: 3,
            width=lambda win, obj: 11,
            y=objects.anchor_vert_centre,
            x=objects.anchor_hori_centre,
            content=[("hello",), ("world\nsneha", cur.A_REVERSE), ("thiru",)],
            line_range=[0, math.inf],
            col_range=[0, math.inf],
        ),
    ]

    frame_time = 1 / general.TARGET_FPS
    last = time.perf_counter()
    prof.enable()

    while True:
        key = win.scr.getch()
        if general.is_key(key, ("q", "Q")):
            break
        elif key == cur.KEY_RESIZE:
            win.term_sz = win.scr.getmaxyx()
            cur.resize_term(*win.term_sz)
        win.erase()
        win.draw(obj_list)
        # frame rate limiter
        # time.sleep(max(0, frame_time - (time.perf_counter() - last)))
        win.addnstr(1, 1, f"FRAME RATE {round(1 / (time.perf_counter() - last))}", win.term_sz[1], cur.A_NORMAL)
        win.refresh()

        # for frame rate calculation
        total += (now := time.perf_counter()) - last
        frames += 1
        last = now
        # if frames == 10000:
        #     break

    prof.disable()
    return (total, frames)


def main():
    global total, frames
    try:
        total, frames = cur.wrapper(start)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("TOTAL FRAMES", frames)
        print(f"TOTAL FRAME TIME {round(total, 3)}s")
        print("AVG FRAME RATE", "ud" if frames == 0 else round(frames / total))


if __name__ == "__main__":
    main()
    s = io.StringIO()
    ps = pstats.Stats(prof, stream=s).sort_stats("cumulative")
    ps.print_stats()
    filename = f"prof-{dt.datetime.now().strftime("%Y%m%d-%H%M%S")}.cprof"
    with open(filename, "w+") as f:
        f.write(s.getvalue())
    print(f"Wrote profiler output to {filename}")
