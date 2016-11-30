from interactive import InteractiveModule, UserModule
from viewer import ViewerConstants
from screen import Screen
from viewport import Viewport
from editor import Editor
from status_line import StatusLine
import logging

log = logging.getLogger('simple_example')

class GM(InteractiveModule, UserModule):

    def __init__(self, vim, wsad):
        self._vim = vim
        self._wsad = wsad
        super(GM, self).__init__()

    def _handle_combo(self, viewer, buf):
        vp = viewer.get_submodule(Viewport)
        if "w" in buf:
            json_map = vp.serialize_features()
            # TODO: update save method
            self._save_handler(json_map)

    def _handle_help(self, viewer, buf):
        pass

    def _handle(self, viewer, ch):

        screen = viewer.get_submodule(Screen)
        viewport = viewer.get_submodule(Viewport)

        if self._vim and not self._wsad:
            if ch == ord("j"):
                self.down(viewer)

            elif ch == ord("k"):
                self.up(viewer)

            elif ch == ord("h"):
                self.left(viewer)

            elif ch == ord("l"):
                self.right(viewer)

            elif ch == ord("J"):
                self.vp_down(viewer)

            elif ch == ord("K"):
                self.vp_up(viewer)

            elif ch == ord("H"):
                self.vp_left(viewer)

            elif ch == ord("L"):
                self.vp_right(viewer)
        elif self._wsad:
            if ch == ord("s"):
                self.down(viewer)

            elif ch == ord("w"):
                self.up(viewer)

            elif ch == ord("a"):
                self.left(viewer)

            elif ch == ord("d"):
                self.right(viewer)

            elif ch == ord("S"):
                self.vp_down(viewer)

            elif ch == ord("W"):
                self.vp_up(viewer)

            elif ch == ord("A"):
                self.vp_left(viewer)

            elif ch == ord("D"):
                self.vp_right(viewer)


        if ch == ord("n"):
            self.edit_note(viewer)

        # some simple utilities
        # TODO: Move these utilities to a dev module
        elif ch == ord("p"):
            import curses
            try:
                for i in range(0, curses.COLORS*curses.COLORS):
                    viewer.screen.addstr(str(i), curses.color_pair(i))
            except:
                pass


        elif ch == ord("P"):
            for i in range(0, 1000):
                self.default_screen.addch(i)


    def up(self, viewer):
        vp = viewer.get_submodule(Viewport)
        vp.cursor_up()

    def down(self, viewer):
        vp = viewer.get_submodule(Viewport)
        vp.cursor_down()

    def left(self, viewer):
        vp = viewer.get_submodule(Viewport)
        vp.cursor_left()

    def right(self, viewer):
        vp = viewer.get_submodule(Viewport)
        vp.cursor_right()

    def vp_down(self, viewer):
        vp = viewer.get_submodule(Viewport)
        screen = viewer.get_submodule(Screen)
        editor = viewer.get_submodule(Editor)
        sl = viewer.get_submodule(StatusLine)
        vp.down()
        editor.down()
        sl.mark_dirty()
        screen.fix_cursor()

    def vp_up(self, viewer):
        vp = viewer.get_submodule(Viewport)
        screen = viewer.get_submodule(Screen)
        editor = viewer.get_submodule(Editor)
        sl = viewer.get_submodule(StatusLine)
        vp.up()
        editor.up()
        sl.mark_dirty()
        screen.fix_cursor()

    def vp_right(self, viewer):
        vp = viewer.get_submodule(Viewport)
        screen = viewer.get_submodule(Screen)
        editor = viewer.get_submodule(Editor)
        sl = viewer.get_submodule(StatusLine)
        vp.right()
        editor.right()
        sl.mark_dirty()
        screen.fix_cursor()

    def vp_left(self, viewer):
        vp = viewer.get_submodule(Viewport)
        screen = viewer.get_submodule(Screen)
        editor = viewer.get_submodule(Editor)
        sl = viewer.get_submodule(StatusLine)
        vp.left()
        editor.left()
        sl.mark_dirty()
        screen.fix_cursor()

    def edit_note(self, viewer):
        import sys, tempfile, os
        import subprocess


        vp = viewer.get_submodule(Viewport)
        screen = viewer.get_submodule(Screen)

        idx = vp.get_feature_idx(
                screen.y + vp.y - 1,
                screen.x + vp.x)

        if idx:
            feature = vp.get_feature(idx)
            notes = feature.notes

            EDITOR = os.environ.get('EDITOR','vim')
            with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
                text = notes.encode("UTF-8")
                tf.write(text)
                tf.flush()
                subprocess.call([EDITOR, tf.name])

                # do the parsing with `tf` using regular File operations.
                # for instance:
                tf.seek(0)
                text = tf.read().decode("UTF-8")

                # TODO: add a way to upload edited note to server
                feature.notes = text
                vp.update_feature(idx, feature)



