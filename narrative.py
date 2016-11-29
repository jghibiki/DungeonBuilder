from interactive import VisibleModule, InteractiveModule
from viewer import ViewerConstants
import logging
import curses
import math

log = logging.getLogger('simple_example')


class Narrative(VisibleModule, InteractiveModule):

    def __init__(self):
        self.initial_draw_priority = -1
        self.draw_priority = 10

        self.x = 0
        self.y = 0
        self.h = ViewerConstants.max_y-1
        self.w = math.floor(ViewerConstants.max_x/3)

        self._screen = curses.newwin(self.h, self.w, self.y, self.x)

        self._dirty = True

    def draw(self, viewer, force=False):
        if self._dirty or force:
            if force: log.debug("narrative.draw forced")

            self._screen.attrset(curses.color_pair(179))
            self._screen.border(
                    curses.ACS_BOARD,
                    curses.ACS_BOARD,
                    curses.ACS_BOARD,
                    curses.ACS_BOARD,
                    curses.ACS_BOARD,
                    curses.ACS_BOARD,
                    curses.ACS_BOARD,
                    curses.ACS_BOARD
            )
            self._screen.addstr(1, 2, "Narrative Window")
            self._screen.attroff(curses.color_pair(179))
            self._screen.noutrefresh()
            self._dirty = False
            return True
        return False

    def _handle(self, viewer, ch):
        pass

    def _handle_combo(self, viewer, buff):
        pass

    def _handle_help(self, viewer, buff):
        pass

