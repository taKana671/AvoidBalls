from enum import Enum, auto

from direct.actor.Actor import Actor
from panda3d.bullet import BulletCapsuleShape, BulletCylinderShape, ZUp
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import PandaNode, NodePath, TransformState
from panda3d.core import Vec3, Point3, LColor, BitMask32

from utils import create_line_node


class Status(Enum):

    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()


class Walker(NodePath):

    RUN = 'run'
    WALK = 'walk'

    def __init__(self, world):
        super().__init__(BulletRigidBodyNode('wolker'))
        self.world = world

        h, w = 6, 1.2
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)
        self.node().add_shape(shape)
        self.node().set_kinematic(True)
        self.node().set_ccd_motion_threshold(1e-7)
        self.node().set_ccd_swept_sphere_radius(0.5)

        self.set_collide_mask(BitMask32.bit(1) | BitMask32.bit(4))
        # self.set_pos(Point3(-156, -28, 3.95079))
        # self.set_pos(Point3(0, -3, 2))
        # self.set_pos(Point3(230, 225, 10))

        self.set_scale(0.5)
        self.reparent_to(base.render)
        self.world.attach(self.node())

        self.direction_nd = NodePath(PandaNode('direction'))
        self.direction_nd.set_h(180)
        self.direction_nd.reparent_to(self)

        self.actor = Actor(
            'models/ralph/ralph.egg',
            {self.RUN: 'models/ralph/ralph-run.egg',
             self.WALK: 'models/ralph/ralph-walk.egg'}
        )
        self.actor.set_transform(TransformState.make_pos(Vec3(0, 0, -2.5)))  # -3
        self.actor.set_name('ralph')
        self.actor.reparent_to(self.direction_nd)

        self.front = NodePath('front')
        self.front.reparent_to(self.direction_nd)
        self.front.set_pos(0, -1.2, 1)

        self.under = NodePath('under')
        self.under.reparent_to(self.direction_nd)
        self.under.set_pos(0, -1.2, -10)

        self.state = None
        self.test_shape = BulletSphereShape(0.5)

        # draw ray cast lines for dubug
        self.debug_line_front = create_line_node(self.front.get_pos(), self.under.get_pos(), LColor(0, 0, 1, 1))
        self.debug_line_center = create_line_node(Point3(0, 0, 0), Point3(0, 0, -10), LColor(1, 0, 0, 1))

    def toggle_debug(self):
        if self.debug_line_front.has_parent():
            self.debug_line_front.detach_node()
            self.debug_line_center.detach_node()
        else:
            self.debug_line_front.reparent_to(self.direction_nd)
            self.debug_line_center.reparent_to(self.direction_nd)

    def navigate(self):
        """Return a relative point to enable camera to follow a character
           when camera's view is blocked by an object like walls.
        """
        return self.get_relative_point(self.direction_nd, Vec3(0, 10, 2))

    def get_terrain_contact_pos(self, pos=None):
        if not pos:
            pos = self.get_pos()

        below = pos - Vec3(0, 0, 30)
        ray_result = self.world.ray_test_closest(pos, below, BitMask32.bit(1) | BitMask32.bit(2))

        if ray_result.has_hit():
            return ray_result.get_hit_pos()
        return None

    def get_orientation(self):
        return self.direction_nd.get_quat(base.render).get_forward()

    def predict_collision(self, next_pos):
        ts_from = TransformState.make_pos(self.get_pos())
        ts_to = TransformState.make_pos(next_pos)
        result = self.world.sweep_test_closest(self.test_shape, ts_from, ts_to, BitMask32.bit(2), 0.0)
        return result.has_hit()

    def update(self, dt):
        direction = 0
        angle = 0

        if self.state == Status.FORWARD:
            direction += -1
        if self.state == Status.BACKWARD:
            direction += 1
        if self.state == Status.LEFT:
            angle += 100 * dt
        if self.state == Status.RIGHT:
            angle -= 100 * dt

        if angle:
            self.turn(angle)

        distance = 0

        if direction < 0:
            distance = direction * 10 * dt
        if direction > 0:
            distance = direction * 5 * dt

        if distance != 0:
            self.move(distance)

        self.play_anim()

    def turn(self, angle):
        self.direction_nd.set_h(self.direction_nd.get_h() + angle)

    def move(self, distance):
        temp_pos = self.get_pos() + self.get_orientation() * distance

        if contact_pos := self.get_terrain_contact_pos(temp_pos):
            next_pos = contact_pos + Vec3(0, 0, 1.5)
            if not self.predict_collision(next_pos):
                self.set_pos(next_pos)

    def play_anim(self):
        match self.state:
            case Status.FORWARD:
                anim = Walker.RUN
                rate = 1
            case Status.BACKWARD:
                anim = Walker.WALK
                rate = -1
            case Status.LEFT | Status.RIGHT:
                anim = Walker.WALK
                rate = 1
            case _:
                self.stop_anim()
                return

        if self.actor.get_current_anim() != anim:
            self.actor.loop(anim)
            self.actor.set_play_rate(rate, anim)

    def stop_anim(self):
        if self.actor.get_current_anim() is not None:
            self.actor.stop()
            self.actor.pose(self.WALK, 5)