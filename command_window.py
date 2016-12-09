from interactive import VisibleModule, InteractiveModule, TextDisplayModule
from features import FeatureType, Feature, FeatureSerializer
from viewer import ViewerConstants
from viewport import Viewport
from client import Client
from state import State
import json
import logging
import curses
import math
import os
import subprocess
import tempfile

log = logging.getLogger('simple_example')

class CommandMode:
    default = 0
    build = 1
    fow = 2
    units = 3
    unit_move = 4


class CommandWindow(VisibleModule, InteractiveModule):
    def __init__(self):
        self.initial_draw_priority = -1
        self.draw_priority = 9

        self.x = math.floor(ViewerConstants.max_x/2) + math.floor(ViewerConstants.max_x/3)+1
        self.y = 0
        self.h = ViewerConstants.max_y-2
        self.w = ViewerConstants.max_x - math.floor(ViewerConstants.max_x/2) - math.floor(ViewerConstants.max_x/3) #TODO: fix sketchy math

        self._screen = curses.newwin(self.h, self.w, self.y, self.x)

        self._mode = CommandMode.default

        self._count = ""

        self._dirty = True

    def draw(self, viewer, force=False):
        if self._dirty or force:
            if force: log.debug("command_window.draw forced")

            self._screen.clear()

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
                        curses.ACS_BOARD,
                        curses.ACS_BOARD,
                        curses.ACS_BOARD,
                        curses.ACS_BOARD,
                        curses.ACS_BOARD,
                        curses.ACS_BOARD,
                        curses.ACS_BOARD,
                        curses.ACS_BOARD
                )
            self._screen.attroff(curses.color_pair(179))

            state = viewer.get_submodule(State)
            role = state.get_state("role")

            if self._mode is CommandMode.default:
                if role == "pc":
                    self._draw_pc_default_screen()
                elif role == "gm":
                    self._draw_gm_default_screen()
            if self._mode is CommandMode.build: self._draw_build_screen()
            if self._mode is CommandMode.fow: self._draw_fow_screen()
            if self._mode is CommandMode.units: self._draw_units_screen(viewer)
            if self._mode is CommandMode.unit_move: self._draw_unit_move_screen(viewer)

            self._screen.noutrefresh()
            self._dirty = False
            return True
        return False

    def _handle(self, viewer, ch):
        state = viewer.get_submodule(State)
        role = state.get_state("role")
        if self._mode is CommandMode.default:
            if ch == ord("b") and role == "gm":
                self._mode = CommandMode.build
                self._dirty = True

            if ch == ord("c"):
                from chat import Chat
                chat = viewer.get_submodule(Chat)
                viewer.apply_to_submodules(TextDisplayModule, lambda x: x._hide(viewer))
                chat._show(viewer)

            if ch == ord("n") and role == "gm":
                from narrative import Narrative
                narrative = viewer.get_submodule(Narrative)
                viewer.apply_to_submodules(TextDisplayModule, lambda x: x._hide(viewer))
                narrative._show(viewer)

            if ch == ord("f") and role == "gm":
                vp = viewer.get_submodule(Viewport)
                current = state.get_state("fow")
                if current == "on":
                    state.set_state("fow", "off")
                else:
                    state.set_state("fow", "on")
                vp._dirty = True
                viewer._draw(force=True)

            if ch == ord("F") and role == "gm":
                self._mode = CommandMode.fow
                self._dirty = True

            if ch == ord("u"):
                state = viewer.get_submodule(State)
                state.set_state("ignore_direction_keys", "on")
                self._mode = CommandMode.units
                self._dirty = True


        elif self._mode is CommandMode.build: #gm only
            if ch == 27 or ch == curses.ascii.ESC: # escape
                self._mode = CommandMode.default
                self._dirty = True


            elif ch == ord("w"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.wall)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("c"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.chair)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("d"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.door)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("t"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.table)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord(">"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.up_stair)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("<"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.down_stair)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("%"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.lantern)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("#"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.chest)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("*"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.point_of_interest)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("r"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.road)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("G"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.gate)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("W"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.water)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("T"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.tree)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("o"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.bush)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("."):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.grass)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)


            elif ch == ord("^"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.hill)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("b"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.bed)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("&"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                feature = Feature(vp.cursor_y,
                                  vp.cursor_x,
                                  FeatureType.statue)
                raw_feature = FeatureSerializer.toDict(feature)
                c.make_request("/map/add", payload=raw_feature)

            elif ch == ord("x"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                c.make_request("/map/rm", payload={
                    "x": vp.cursor_x,
                    "y": vp.cursor_y
                })


        elif self._mode is CommandMode.units:
            if ch == 27 or ch == curses.ascii.ESC:
                self._mode = CommandMode.default
                state = viewer.get_submodule(State)
                state.set_state("ignore_direction_keys", "off")
                self._dirty = True

            elif ch == ord("a"):

                unit_text = """
# Name: Name of the unit
# Max Health: the unit's maximum health
# Current Health: the unit's current health, must be less than or equal to max health
# Controller: The owner of the unit. Only the owner and the gm can move the unit.
# Type: The type of the unit, must be one of the following. If not set defaults to neutral.
#   - pc: a unit that will be controllable by the pc owner. Displayed as blue to the owner and green to others.
#   - enemy: a unit that will be controllable by a gm. Displayed as red.
#   - neutral: a unit that will be controllable by a gm. Displayed as grey.
# Do not edit anything above this line
{
    "name": "",
    "current_health": 0,
    "max_health": 0,
    "controller": "",
    "type": ""
}
                """

                valid_json = False

                while not valid_json:

                    EDITOR = os.environ.get('EDITOR','vim')
                    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
                        tf.write(unit_text.encode("UTF-8"))
                        tf.flush()
                        subprocess.call([EDITOR, tf.name])

                        # do the parsing with `tf` using regular File operations.
                        # for instance:
                        tf.seek(0)
                        unit_text = tf.read().decode("UTF-8")

                        # fix cursor mode
                        curses.curs_set(1)
                        curses.curs_set(0)
                    viewer._draw(force=True) # force redraw after closing vim

                    try:
                        lines = unit_text.splitlines()
                        lines = lines[10:]
                        text = ''.join(lines)
                        unit = json.loads(text)
                        valid_json = True
                    except:
                        pass

                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)

                unit["x"] = vp.cursor_x
                unit["y"] = vp.cursor_y

                c.make_request("/unit/add", payload=unit)

            elif ch == ord("r"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)

                unit = vp.get_current_unit()


                c.make_request('/unit/rm', payload={
                    "id": unit.id
                })

            elif ch == ord("m"):
                self._mode = CommandMode.unit_move
                self._dirty = True


        elif self._mode is CommandMode.unit_move:
            state = viewer.get_submodule(State)

            if ch == 27 or ch == curses.ascii.ESC: # escape
                self._mode = CommandMode.units
                self._dirty = True

            elif state.get_state("direction_scheme") == "vim":

                vp = viewer.get_submodule(Viewport)
                unit = vp.get_current_unit()

                if ( unit != None and
                        ( unit.controller == state.get_state("username") or
                          state.get_state("role") == "gm" )):
                    if ch == ord("j"):
                        log.error("move unit down")
                        c = viewer.get_submodule(Client)

                        if unit.y+1 <= vp.h:
                            unit.y += 1
                            c.make_request('/unit/update', payload=unit.toDict())
                            vp._dirty = True

                    elif ch == ord("k"):
                        c = viewer.get_submodule(Client)

                        if unit.y-1 >= 1:
                            unit.y -= 1
                            c.make_request('/unit/update', payload=unit.toDict())

                    elif ch == ord("h"):
                        c = viewer.get_submodule(Client)

                        if unit.x-1 >= 1:
                            unit.x -= 1
                            c.make_request('/unit/update', payload=unit.toDict())

                    elif ch == ord("l"):
                        c = viewer.get_submodule(Client)

                        if unit.x+1 <= vp.w:
                            unit.x += 1
                            c.make_request('/unit/update', payload=unit.toDict())
                else:
                    if ch == ord("j"):
                        vp.cursor_up()
                    elif ch == ord("k"):
                        vp.cursor_down()
                    elif ch == ord("h"):
                        vp.cursor_right()
                    elif ch == ord("l"):
                        vp.cursor_left()

            elif state.get_state("direction_scheme") == "wsad":

                vp = viewer.get_submodule(Viewport)
                unit = vp.get_current_unit()

                if ( unit != None and
                        ( unit.controller == state.get_state("username") or
                          state.get_state("role") == "gm" )):
                    if ch == ord("s"):
                        c = viewer.get_submodule(Client)

                        if unit.y+1 <= vp.h:
                            unit.y += 1
                            c.make_request('/unit/update', payload=unit.toDict())
                            vp._dirty = True

                    elif ch == ord("w"):
                        c = viewer.get_submodule(Client)

                        if unit.y-1 >= 1:
                            unit.y -= 1
                            c.make_request('/unit/update', payload=unit.toDict())

                    elif ch == ord("a"):
                        c = viewer.get_submodule(Client)

                        if unit.x-1 >= 1:
                            unit.x -= 1
                            c.make_request('/unit/update', payload=unit.toDict())

                    elif ch == ord("d"):
                        c = viewer.get_submodule(Client)

                        if unit.x+1 <= vp.w:
                            unit.x += 1
                            c.make_request('/unit/update', payload=unit.toDict())
                else:
                    if ch == ord("s"):
                        vp.cursor_up()
                    elif ch == ord("w"):
                        vp.cursor_down()
                    elif ch == ord("a"):
                        vp.cursor_right()
                    elif ch == ord("d"):
                        vp.cursor_left()





        elif self._mode is CommandMode.fow: #gm only
            if ch == 27 or ch == curses.ascii.ESC: # escape
                self._mode = CommandMode.default
                self._dirty = True

            elif ch == ord("f"):
                vp = viewer.get_submodule(Viewport)
                current = state.get_state("fow")
                if current == "on":
                    state.set_state("fow", "off")
                else:
                    state.set_state("fow", "on")
                vp._dirty = True
                viewer._draw(force=True)

            elif ch == ord("a"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                c.make_request("/fow/add", payload={
                    "x": vp.cursor_x,
                    "y": vp.cursor_y
                })

            elif ch == ord("r"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                c.make_request("/fow/rm", payload={
                    "x": vp.cursor_x,
                    "y": vp.cursor_y
                })

            elif ch == ord("A"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                c.make_request("/fow/fill")

            elif ch == ord("R"):
                vp = viewer.get_submodule(Viewport)
                c = viewer.get_submodule(Client)
                c.make_request("/fow/clear")


    def _handle_combo(self, viewer, buff):
            pass

    def _handle_help(self, viewer, buff):
        pass


    def _draw_gm_default_screen(self):
        self._screen.addstr(1, 2, "Commands:", curses.color_pair(179))

        # build menu
        self._screen.addstr(2, 2, "b", curses.color_pair(179))
        self._screen.addstr(2, 3, ": Build", )

        # show chat
        self._screen.addstr(3, 2, "c", curses.color_pair(179))
        self._screen.addstr(3, 3, ": Chat", )

        # show narrative
        self._screen.addstr(4, 2, "n", curses.color_pair(179))
        self._screen.addstr(4, 3, ": Narrative", )

        # show fow toggle
        self._screen.addstr(5, 2, "f", curses.color_pair(179))
        self._screen.addstr(5, 3, ": Toggle Fog of War for GM")

        # fow menu
        self._screen.addstr(6, 2, "F", curses.color_pair(179))
        self._screen.addstr(6, 3, ": Edit Fog of War")

        # unit menu
        self._screen.addstr(7, 2, "u", curses.color_pair(179))
        self._screen.addstr(7, 3, ": Units")

    def _draw_pc_default_screen(self):
        self._screen.addstr(1, 2, "Commands:", curses.color_pair(179))

        # show chat
        self._screen.addstr(2, 2, "c", curses.color_pair(179))
        self._screen.addstr(2, 3, ": Chat", )

        # unit menu
        self._screen.addstr(3, 2, "u", curses.color_pair(179))
        self._screen.addstr(3, 3, ": Units")

    def _draw_fow_screen(self):
        self._screen.addstr(1, 2, "Fog of War Commands:", curses.color_pair(179))

        # toggle gm fow view
        self._screen.addstr(2, 2, "f", curses.color_pair(179))
        self._screen.addstr(2, 3, ": Toggle FoW for GM", )

        # add fow
        self._screen.addstr(3, 2, "a", curses.color_pair(179))
        self._screen.addstr(3, 3, ": Add FoW", )

        # rm fow
        self._screen.addstr(4, 2, "r", curses.color_pair(179))
        self._screen.addstr(4, 3, ": Remove FoW", )

        # fill fow
        self._screen.addstr(5, 2, "A", curses.color_pair(179))
        self._screen.addstr(5, 3, ": Fill Map with FoW", )

        # clear fow
        self._screen.addstr(6, 2, "R", curses.color_pair(179))
        self._screen.addstr(6, 3, ": Clear FoW", )

        # esc
        self._screen.addstr(8, 2, "esc", curses.color_pair(179))
        self._screen.addstr(8, 5, ": Back", )

    def _draw_units_screen(self, viewer):
        state = viewer.get_submodule(State)
        role = state.get_state("role")
        vp = viewer.get_submodule(Viewport)

        current_unit = vp.get_current_unit()

        if role == "gm":
            self._screen.addstr(1, 2, "Units:", curses.color_pair(179))

            self._screen.addstr(2, 2, "a", curses.color_pair(179))
            self._screen.addstr(2, 3, ": Add Unit", )

            if current_unit != None:
                self._screen.addstr(3, 2, "r", curses.color_pair(179))
                self._screen.addstr(3, 3, ": Remove Unit", )

                self._screen.addstr(4, 2, "m", curses.color_pair(179))
                self._screen.addstr(4, 3, ": Move Unit", )

                self._screen.addstr(5, 2, "e", curses.color_pair(179))
                self._screen.addstr(5, 3, ": Edit Unit", )

                self._screen.addstr(6, 2, "+", curses.color_pair(179))
                self._screen.addstr(6, 3, ": Increase Unit Health", )

                self._screen.addstr(7, 2, "-", curses.color_pair(179))
                self._screen.addstr(7, 3, ": Decrease Unit Health", )
            else:

                self._screen.addstr(3, 2, "r", curses.color_pair(60))
                self._screen.addstr(3, 3, ": Remove Unit", )

                self._screen.addstr(4, 2, "m", curses.color_pair(60))
                self._screen.addstr(4, 3, ": Move Unit", )

                self._screen.addstr(5, 2, "e", curses.color_pair(60))
                self._screen.addstr(5, 3, ": Edit Unit", )

                self._screen.addstr(6, 2, "+", curses.color_pair(60))
                self._screen.addstr(6, 3, ": Increase Unit Health", )

                self._screen.addstr(7, 2, "-", curses.color_pair(60))
                self._screen.addstr(7, 3, ": Decrease Unit Health", )

            # esc
            self._screen.addstr(10, 2, "esc", curses.color_pair(179))
            self._screen.addstr(10, 6, ": Back")

        elif role == "pc":
            if current_unit != None:
                self._screen.addstr(2, 2, "m", curses.color_pair(179))
                self._screen.addstr(2, 3, ": Move Unit", )
            else:
                self._screen.addstr(2, 2, "m", curses.color_pair(60))
                self._screen.addstr(2, 3, ": Move Unit", curses.color_pair(60) )

            # esc
            self._screen.addstr(24, 2, "esc", curses.color_pair(179))
            self._screen.addstr(24, 6, ": Back")

    def _draw_unit_move_screen(self, viewer):

        state = viewer.get_submodule(State)

        direction_scheme = state.get_state("direction_scheme")

        self._screen.addstr(1, 2, "Move Units:", curses.color_pair(179))

        if direction_scheme == "vim":
            self._screen.addstr(2, 2, "j", curses.color_pair(179))
            self._screen.addstr(2, 3, ": Down", )

            self._screen.addstr(3, 2, "k", curses.color_pair(179))
            self._screen.addstr(3, 3, ": Up", )

            self._screen.addstr(4, 2, "h", curses.color_pair(179))
            self._screen.addstr(4, 3, ": Left", )

            self._screen.addstr(5, 2, "l", curses.color_pair(179))
            self._screen.addstr(5, 3, ": Right", )


        elif direction_scheme == "wsad":
            self._screen.addstr(2, 2, "s", curses.color_pair(179))
            self._screen.addstr(2, 3, ": Down", )

            self._screen.addstr(3, 2, "w", curses.color_pair(179))
            self._screen.addstr(3, 3, ": Up", )

            self._screen.addstr(4, 2, "a", curses.color_pair(179))
            self._screen.addstr(4, 3, ": Left", )

            self._screen.addstr(5, 2, "d", curses.color_pair(179))
            self._screen.addstr(5, 3, ": Right", )

        # esc
        self._screen.addstr(24, 2, "esc", curses.color_pair(179))
        self._screen.addstr(24, 6, ": Back")





    def _draw_build_screen(self):
        self._screen.addstr(1, 2, "Build:", curses.color_pair(179))


        # wall
        self._screen.addstr(2, 2, "w", curses.color_pair(179))
        self._screen.addstr(2, 3, ": Wall(")
        self._screen.addstr(2, 10,
                FeatureType.toSymbol(
                    FeatureType.wall),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.wall)))
        self._screen.addstr(2, 11, ")")

        # water
        self._screen.addstr(3, 2, "W", curses.color_pair(179))
        self._screen.addstr(3, 3, ": Water(")
        self._screen.addstr(3, 11,
                FeatureType.toSymbol( FeatureType.water ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.water)))
        self._screen.addstr(3, 12, ")")

        # door
        self._screen.addstr(4, 2, "d", curses.color_pair(179))
        self._screen.addstr(4, 3, ": Door(")
        self._screen.addstr(4, 10,
                FeatureType.toSymbol( FeatureType.door ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.door)))
        self._screen.addstr(4, 11, ")")

        # gate
        self._screen.addstr(5, 2, "G", curses.color_pair(179))
        self._screen.addstr(5, 3, ": Gate(")
        self._screen.addstr(5, 10,
                FeatureType.toSymbol( FeatureType.gate ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.gate)))
        self._screen.addstr(5, 11, ")")

        # Road
        self._screen.addstr(6, 2, "r", curses.color_pair(179))
        self._screen.addstr(6, 3, ": Road(")
        self._screen.addstr(6, 10,
                FeatureType.toSymbol( FeatureType.road ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.road)))
        self._screen.addstr(6, 11, ")")

        # bush
        self._screen.addstr(7, 2, "o", curses.color_pair(179))
        self._screen.addstr(7, 3, ": Bush(")
        self._screen.addstr(7, 10,
                FeatureType.toSymbol( FeatureType.bush ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.bush)))
        self._screen.addstr(7, 11, ")")

        # grass
        self._screen.addstr(8, 2, ".", curses.color_pair(179))
        self._screen.addstr(8, 3, ": Grass(")
        self._screen.addstr(8, 11,
                FeatureType.toSymbol( FeatureType.grass ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.grass)))
        self._screen.addstr(8, 12, ")")

        # table
        self._screen.addstr(9, 2, "t", curses.color_pair(179))
        self._screen.addstr(9, 3, ": Table(")
        self._screen.addstr(9, 11,
                FeatureType.toSymbol( FeatureType.table ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.table)))
        self._screen.addstr(9, 12, ")")

        # chair
        self._screen.addstr(10, 2, "t", curses.color_pair(179))
        self._screen.addstr(10, 3, ": Chair(")
        self._screen.addstr(10, 11,
                FeatureType.toSymbol( FeatureType.chair),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.chair)))
        self._screen.addstr(10, 12, ")")

        # tree
        self._screen.addstr(11, 2, "T", curses.color_pair(179))
        self._screen.addstr(11, 3, ": Tree(")
        self._screen.addstr(11, 10,
                FeatureType.toSymbol( FeatureType.tree ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.tree)))
        self._screen.addstr(11, 11, ")")

        # hill
        self._screen.addstr(12, 2, "^", curses.color_pair(179))
        self._screen.addstr(12, 3, ": Hill(")
        self._screen.addstr(12, 10,
                FeatureType.toSymbol( FeatureType.hill ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.hill)))
        self._screen.addstr(12, 11, ")")

        # Up stair/Ladder
        self._screen.addstr(13, 2, ">", curses.color_pair(179))
        self._screen.addstr(13, 3, ": Up Stair/Ladder(")
        self._screen.addstr(13, 21,
                FeatureType.toSymbol( FeatureType.up_stair ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.up_stair)))
        self._screen.addstr(13, 22, ")")

        # Down stair/ladder
        self._screen.addstr(14, 2, "<", curses.color_pair(179))
        self._screen.addstr(14, 3, ": Down Stair/Ladder(")
        self._screen.addstr(14, 23,
                FeatureType.toSymbol( FeatureType.down_stair ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.down_stair)))
        self._screen.addstr(14, 24, ")")

        # lantern
        self._screen.addstr(15, 2, "%", curses.color_pair(179))
        self._screen.addstr(15, 3, ": Lantern(")
        self._screen.addstr(15, 13,
                FeatureType.toSymbol( FeatureType.lantern ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.lantern)))
        self._screen.addstr(15, 14, ")")

        # chest
        self._screen.addstr(16, 2, "#", curses.color_pair(179))
        self._screen.addstr(16, 3, ": Chest(")
        self._screen.addstr(16, 11,
                FeatureType.toSymbol( FeatureType.lantern ),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.lantern)))
        self._screen.addstr(16, 12, ")")

        # point of interest *
        self._screen.addstr(17, 2, "*", curses.color_pair(179))
        self._screen.addstr(17, 3, ": Point Of Interest(")
        self._screen.addstr(17, 23,
                FeatureType.toSymbol( FeatureType.point_of_interest),
                FeatureType.modFromName(
                    FeatureType.toName(
                        FeatureType.point_of_interest)))
        self._screen.addstr(17, 24, ")")


        self._screen.addstr(19, 2, "x", curses.color_pair(179))
        self._screen.addstr(19, 3, ": Remove Object")

        # esc
        self._screen.addstr(20, 2, "esc", curses.color_pair(179))
        self._screen.addstr(20, 6, ": Back")

