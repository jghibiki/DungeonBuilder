from interactive import VisibleModule, InteractiveModule
from features import FeatureType
from viewer import ViewerConstants
from state import State
import curses
import logging
import math

log = logging.getLogger('simple_example')


class StatusLine(VisibleModule):

    def __init__(self):
        self.initial_draw_priority = 99
        self.draw_priority = 99

        self.x = math.floor(curses.COLS/2)+1
        self.y = ViewerConstants.max_y-2
        self.h = 3
        self.w = math.floor(curses.COLS/2)-1

        self._dirty = True
        self._screen = curses.newwin(self.h, self.w, self.y, self.x)


    def draw(self, viewer, force=False):
        from editor import Editor
        from screen import Screen
        from viewport import Viewport

        if self._dirty or force:
            if force: log.debug("status_line.draw forced")

            editor = viewer.get_submodule(Editor)
            screen = viewer.get_submodule(Screen)
            vp = viewer.get_submodule(Viewport)
            state = viewer.get_submodule(State)
            self._screen.attrset(curses.color_pair(179))

            if state.get_state("easter_egg") is not None:
                self._screen.border(
                        curses.ACS_VLINE,
                        curses.ACS_VLINE,
                        curses.ACS_HLINE,
                        curses.ACS_HLINE,
                        curses.ACS_DIAMOND,
                        curses.ACS_DIAMOND,
                        curses.ACS_DIAMOND,
                        curses.ACS_DIAMOND
                )
            else:
                self._screen.border(
                        curses.ACS_VLINE,
                        curses.ACS_VLINE,
                        curses.ACS_HLINE,
                        curses.ACS_HLINE,
                        curses.ACS_ULCORNER,
                        curses.ACS_URCORNER,
                        curses.ACS_LLCORNER,
                        curses.ACS_LRCORNER,
                )

            self._screen.attroff(curses.color_pair(179))

            msg = "Status Line"
            padded_ln = msg.ljust(self.w-2)
            self._screen.addstr(1,1, padded_ln, curses.color_pair(179))



            self._screen.noutrefresh()

            self._dirty = False
            return True
        return False

    def mark_dirty(self):
        self._dirty = True

