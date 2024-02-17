import random
import sys
from enum import Enum, auto

from direct.gui.DirectGui import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import NodePath, TextNode
from panda3d.core import BitMask32, Point2, Point3, Quat, Vec3, LColor, CardMaker
from panda3d.core import TransparencyAttrib
from panda3d.core import load_prc_file_data
from direct.interval.IntervalGlobal import Sequence, Func

from walker import Walker
from walker import Status as WalkingStatus
from scene import Scene
from ball_controller import BallController


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Walking In BulletWorld
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class Status(Enum):

    PLAY = auto()
    SETUP = auto()
    CLEANUP = auto()
    START = auto()
    CHANGE = auto()


class AvoidBalls(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.world = BulletWorld()
        self.world.set_gravity(0, 0, -9.81)

        self.scene = Scene(self.world)
        self.scene.reparent_to(self.render)

        self.debug_np = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug_np.node())

        self.walker = Walker(self.world)
        self.floater = NodePath('floater')
        self.floater.set_z(3.0)
        self.floater.reparent_to(self.walker)

        # pos = self.scene.goal_gate.poles.get_pos(self.render)
        pos = self.scene.get_pos_on_terrain(0, 0)
        self.walker.set_pos(pos + Point3(-2, -2, 0))

        # self.camera.reparent_to(base.render)
        # self.camera.set_pos(0, 0, 200)
        # self.camera.look_at(0, 0, 0)
        # self.camLens.set_fov(200)

        self.camera.reparent_to(self.walker)
        self.camera.set_pos(self.walker.navigate())
        self.camera.look_at(self.floater)
        self.camLens.set_fov(90)

        self.socre_display = ScoreDisplays()
        self.socre_display.show_score()
        self.ball_controller = BallController(self.world, self.walker, self.socre_display)
        self.timer = 0
        self.screen = Screen()
        self.screen.show_title_screen()
        # self.screen.show_white_screen()

        # *****when debug***************
        # self.camera.set_pos(0, 0, 30)
        # self.camera.look_at(self.walker)
        # *****when debug***************

        inputState.watch_with_modifiers('forward', 'arrow_up')
        inputState.watch_with_modifiers('backward', 'arrow_down')
        inputState.watch_with_modifiers('left', 'arrow_left')
        inputState.watch_with_modifiers('right', 'arrow_right')

        self.accept('d', self.toggle_debug)
        self.accept('p', self.print_position)
        self.accept('escape', sys.exit)
        # base.taskMgr.do_method_later(2, self.start_game, 'setup_nature')
        self.taskMgr.add(self.update, 'update')
        base.taskMgr.do_method_later(2, self.screen.hide_title_screen, 'hide_title_screen')
        # self.taskMgr.add(self.scene.goal_gate.check_finish, 'check_finish')
        self.state = Status.START

    def change_state(self):
        self.state = Status.CLEANUP

    def print_position(self):
        print('walker_pos: ', self.walker.get_pos(), ' camera_pos: ', self.camera.get_pos())

    def toggle_debug(self):
        if self.debug_np.is_hidden():
            self.debug_np.show()
        else:
            self.debug_np.hide()

    def start_game(self, task):
        self.state = Status.PLAY
        return task.done

    def ray_cast(self, from_pos, to_pos):
        result = self.world.ray_test_closest(from_pos, to_pos, BitMask32.bit(1) | BitMask32.bit(2))
        if result.has_hit():
            # if result.get_node() != self.walker.node():
            #     pass
                # print(result.get_node())
            return result.get_node()
        return None

    def find_camera_pos(self, walker_pos, next_pos):
        q = Quat()
        point = Point3(0, 0, 0)
        start = self.camera.get_pos()
        angle = r = None

        for i in range(36):
            camera_pos = next_pos + walker_pos
            if self.ray_cast(camera_pos, walker_pos) == self.walker.node():
                return next_pos

            times = i // 2 + 1
            angle = 10 * times if i % 2 == 0 else -10 * times
            q.set_from_axis_angle(angle, Vec3.up())
            r = q.xform(start - point)
            next_pos = point + r

        return None

    def control_camera(self):
        """Reposition the camera if the camera's view is blocked by other objects like terrain,
            rocks, trees.
        """
        # reposition
        walker_pos = self.walker.get_pos()
        camera_pos = self.camera.get_pos() + walker_pos

        if self.ray_cast(camera_pos, walker_pos) != self.walker.node():
            if next_pos := self.find_camera_pos(walker_pos, self.walker.navigate()):
                self.camera.set_pos(next_pos)
                self.camera.look_at(self.floater)

    def control_walker(self, dt):
        self.walker.state = None

        if inputState.is_set('forward'):
            self.walker.state = WalkingStatus.FORWARD
        if inputState.is_set('backward'):
            self.walker.state = WalkingStatus.BACKWARD
        if inputState.is_set('left'):
            self.walker.state = WalkingStatus.LEFT
        if inputState.is_set('right'):
            self.walker.state = WalkingStatus.RIGHT

        self.walker.update(dt)

    def update(self, task):
        dt = globalClock.get_dt()
        self.control_walker(dt)
        self.control_camera()
        self.ball_controller.update(dt)

        match self.state:

            case Status.PLAY:
                if task.time > self.timer:
                    self.ball_controller.shoot()
                    self.timer = task.time + random.randint(1, 10) / 10

                if self.scene.goal_gate.sensor.finish_line:
                    # self.screen.reparent_to(self.render2d)
                    self.screen.show_white_screen()
                    self.state = Status.CLEANUP

            case Status.CLEANUP:
                if self.screen.is_appear:
                    self.scene.cleanup_scene()
                    self.state = Status.CHANGE

            case Status.CHANGE:
                self.scene.change_scene()
                self.state = Status.SETUP

            case Status.SETUP:
                self.scene.setup_scene()

                # pos = self.scene.get_pos_on_terrain(230, 230)
                pos = self.scene.goal_gate.poles.get_pos(base.render)
                self.walker.set_pos(pos + Point3(-2, -2, 3))

                self.screen.hide_screen()
                self.state = Status.START

            case Status.START:
                if not self.screen.is_appear:
                    self.state = Status.PLAY

        self.world.do_physics(dt)
        return task.cont


class Screen(NodePath):

    def __init__(self):
        cm = CardMaker('card')
        cm.set_frame_fullscreen_quad()
        super().__init__(cm.generate())
        self.set_transparency(TransparencyAttrib.MAlpha)
        self.is_appear = False
        self.reparent_to(base.render2d)
        self.transparent = LColor(.96, .96, .96, .0)
        self.white_smoke = LColor(.96, .96, .96, 1.0)
        self.gray = LColor(.5, .5, .5, 1.0)

    def change_flag(self):
        self.is_appear = not self.is_appear

    def show_white_screen(self):
        self.reparent_to(base.render2d)
        Sequence(
            self.colorInterval(2.0, self.white_smoke, self.transparent),
            Func(lambda: self.change_flag()),
        ).start()

    def hide_screen(self):
        Sequence(
            self.colorInterval(2.0, self.transparent, self.white_smoke),
            Func(lambda: self.change_flag()),
            Func(lambda: self.detach_node())
        ).start()

    def show_title_screen(self):
        self.change_flag()
        self.set_color(self.white_smoke)
        self.reparent_to(base.render2d)
        self.title = OnscreenText(
            text='Avoid Balls',
            parent=base.aspect2d,
            align=TextNode.ACenter,
            font=base.loader.load_font('font/Candaral.ttf'),
            scale=0.2,
            fg=self.gray,
            pos=(0, 0)
        )

    def hide_title_screen(self, task):
        Sequence(
            self.title.colorScaleInterval(1.0, LColor(.5, .5, .5, .0), blendType='easeInOut'),
            Func(self.hide_screen)
        ).start()
        return task.done


class ScoreDisplays:

    def __init__(self):
        font = base.loader.load_font('font/Candaral.ttf')
        self.avoid = Score(font, Point2(0.05, -0.1), 'avoid:')
        self.hit = Score(font, Point2(0.17, -0.2), 'hit:')
        self.avoid_score = 0
        self.hit_score = 0

    def show_score(self, avoid=0, hit=0):
        self.avoid.show_score(avoid)
        self.hit.show_score(hit)


class Score(OnscreenText):

    def __init__(self, font, pos, format, scale=0.1, fg=(1, 1, 1, 1), text=''):
        super().__init__(
            text=text,
            parent=base.a2dTopLeft,
            align=TextNode.ALeft,
            pos=pos,
            scale=scale,
            font=font,
            fg=fg,
            mayChange=True
        )
        self.score = 0
        self.fmt = format

    def show_score(self, score):
        self.score += score
        self.setText(f'{self.fmt} {self.score}')


if __name__ == '__main__':
    app = AvoidBalls()
    app.run()