import random
import sys
from enum import Enum, auto

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.bullet import BulletWorld, BulletDebugNode, BulletRigidBodyNode, BulletSphereShape
from panda3d.core import NodePath
from panda3d.core import BitMask32, LColor, Point3, Quat, Vec3
from panda3d.core import load_prc_file_data

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

        # self.camera.reparent_to(base.render)
        # self.camera.set_pos(0, 0, 200)
        # self.camera.look_at(0, 0, 0)
        # self.camLens.set_fov(200)

        self.camera.reparent_to(self.walker)
        self.camera.set_pos(self.walker.navigate())
        self.camera.look_at(self.floater)
        self.camLens.set_fov(90)

        self.ball_controller = BallController(self.world, self.walker, self.scene.terrains)
        self.status = Status.SETUP
        self.timer = 0

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
        self.accept('done_setup_nature', self.start_game)
        self.taskMgr.add(self.update, 'update')
        self.taskMgr.do_method_later(0.2, self.scene.terrains.setup_nature, 'setup_nature')

    def print_position(self):
        print(self.camera.get_hpr())
        print(self.walker.get_pos())

    def toggle_debug(self):
        if self.debug_np.is_hidden():
            self.debug_np.show()
        else:
            self.debug_np.hide()

    def start_game(self):
        self.status = Status.PLAY

    def update(self, task):
        dt = globalClock.get_dt()
        self.control_walker(dt)
        self.control_camera()

        match self.status:

            case Status.PLAY:
                if task.time > self.timer:
                    self.ball_controller.shoot()
                    self.timer = task.time + random.randint(1, 10) / 10
                self.ball_controller.update(dt)

        # for t in self.scene.terrain_root.terrains:
        #     t.update()

        # self.terrain_creator.terrains.set_z(self.terrain_creator.terrains.get_z() - 10 * dt)
        self.world.do_physics(dt)
        return task.cont

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
        direction = 0
        angle = 0
        self.walker.state = WalkingStatus.STANDING

        if inputState.is_set('left'):
            self.walker.state = WalkingStatus.LEFT
            angle += 100 * dt
        if inputState.is_set('right'):
            self.walker.state = WalkingStatus.RIGHT
            angle += -100 * dt
        if inputState.is_set('forward'):
            self.walker.state = WalkingStatus.FORWARD
            direction += -1
        if inputState.is_set('backward'):
            self.walker.state = WalkingStatus.BACKWARD
            direction += 1

        self.walker.update(dt, direction, angle)


if __name__ == '__main__':
    app = AvoidBalls()
    app.run()