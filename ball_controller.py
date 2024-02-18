import math
import random
from collections import deque
from enum import Enum

import numpy as np
from direct.interval.IntervalGlobal import ProjectileInterval, Parallel, Sequence, Func
from panda3d.core import NodePath, TransformState
from panda3d.core import BitMask32, LColor, Point3, Vec3, Point2
from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape

from geomnode_maker import Sphere
from walker import Motions


class Colors(Enum):

    RED = LColor(1, 0, 0, 1)
    BLUE = LColor(0, 0, 1, 1)
    YELLOW = LColor(1, 1, 0, 1)
    MAGENDA = LColor(1, 0, 1, 1)
    LIME = LColor(0, 1, 0, 0)

    @classmethod
    def choice(cls):
        choice = random.choice(list(cls))
        return choice.value


class SplashSequence(Sequence):

    def __init__(self, np, model, color, pos):
        super().__init__()
        self.append(Parallel(*[para for para in self.make_splash(np, model, color, pos)]))
        self.append(Func(lambda: np.remove_node()))

    def make_splash(self, np, model, color, pos):
        for _ in range(10):
            ball = model.copy_to(np)
            ball.set_color(color)
            start_scale = random.uniform(0.2, 0.4)
            diff = Vec3(random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(1.5, 4))

            para = Parallel(
                ProjectileInterval(ball, duration=0.5, startPos=pos, endPos=pos + diff, gravityMult=1.0),
                ball.scaleInterval(0.5, Vec3(0.01), Vec3(start_scale))
            )

            yield para


class Ball(NodePath):

    def __init__(self, sphere, color, start_pt, end_pt, scale=0.5):
        super().__init__(BulletRigidBodyNode('ball'))
        self.ball = sphere.copy_to(self)
        self.ball.reparent_to(self)

        self.set_scale(scale)
        self.set_color(color)
        self.set_pos(start_pt)

        self.set_collide_mask(BitMask32.bit(3))
        self.node().set_kinematic(True)

        end, tip = self.ball.get_tight_bounds()
        size = tip - end
        self.node().add_shape(BulletSphereShape(size.z / 2))

        mid_pt = (start_pt + end_pt) / 2
        mid_pt.z += 20
        self.passing_pts = (start_pt, mid_pt, end_pt)
        self.total_dt = 0

    def bernstein(self, n, k):
        coef = math.factorial(n) / (math.factorial(k) * math.factorial(n - k))
        return coef * self.total_dt ** k * (1 - self.total_dt) ** (n - k)

    def bezier_curve(self, dt):
        self.total_dt += dt

        if self.total_dt > 1:
            self.total_dt = 1

        n = len(self.passing_pts) - 1
        px = py = pz = 0

        for i, pt in enumerate(self.passing_pts):
            b = self.bernstein(n, i)
            px += np.dot(b, pt[0])
            py += np.dot(b, pt[1])
            pz += np.dot(b, pt[2])

        return Point3(px, py, pz)

    def splash(self):
        np = NodePath('splash')
        np.reparent_to(self.get_parent())  # parent is balls.
        return SplashSequence(np, self.ball, self.get_color(), self.get_pos())


class BallController:

    def __init__(self, world, walker, display):
        self.world = world
        self.walker = walker
        self.display = display
        self.ball = Sphere()
        self.moving_q = deque()
        self.remove_q = deque()
        self.balls = NodePath('balls')
        self.balls.reparent_to(base.render)

    def get_shoot_pos(self, pos):
        """Returns the point where ball is thrown.
            Args:
                pos (Point3): point where Ralph contacts with the terrain now.
        """
        # the horizontal film size of the virtual film
        hor_film_size = base.camLens.get_hfov()
        camera_front = int(base.camera.get_h() + hor_film_size)
        angle_range = (camera_front - 60, camera_front + 60)
        angle = random.randint(*angle_range)

        x = 100 * round(math.cos(math.radians(angle)), 2)
        y = 100 * round(math.sin(math.radians(angle)), 2)
        pt2 = Point2(x, y) + pos.xy
        z = 30

        if (result := self.world.ray_test_closest(
                Point3(pt2, 30), Point3(pt2, -30), mask=BitMask32.bit(1))).has_hit():
            z = result.get_hit_pos().z + 35

        return Point3(pt2, z)

    def get_dest_pos(self, pos):
        """Returns the ball's destination poin.  
            Args:
                pos (Point3): point where Ralph contacts with the terrain now.
        """
        match self.walker.motion:
            case Motions.FORWARD:
                distance = random.uniform(0.7, 0.8) * -10
            case Motions.BACKWARD:
                distance = random.uniform(0.7, 0.8) * 6
            case _:
                distance = random.uniform(-0.03, 0.03)

        dest = pos + self.walker.get_orientation() * distance
        return dest

    def shoot(self):
        if contact_pos := self.walker.get_terrain_contact_pos():
            if shoot_pos := self.get_shoot_pos(contact_pos):
                dest = self.get_dest_pos(contact_pos)
                color = Colors.choice()
                ball = Ball(self.ball, color, shoot_pos, dest)
                ball.reparent_to(self.balls)
                self.world.attach(ball.node())
                self.moving_q.append(ball)

    def update(self, dt):
        for _ in range(len(self.remove_q)):
            ball = self.remove_q.popleft()
            splash = ball.splash()
            self.world.remove(ball.node())
            ball.remove_node()
            splash.start()

        for _ in range(len(self.moving_q)):
            ball = self.moving_q.popleft()
            current_pos = ball.get_pos()
            next_pt = ball.bezier_curve(dt)
            ball.set_pos(next_pt)

            if self.will_collide(current_pos, next_pt) or ball.total_dt == 1:
                self.remove_q.append(ball)
                continue

            self.moving_q.append(ball)

    def will_collide(self, pt_from, pt_to):
        ts_from = TransformState.make_pos(pt_from)
        ts_to = TransformState.make_pos(pt_to)
        test_shape = BulletSphereShape(0.5)
        result = self.world.sweep_test_closest(
            test_shape, ts_from, ts_to, BitMask32.bit(1) | BitMask32.bit(2), 0.0)

        if result.has_hit():
            if result.get_node() == self.walker.node():
                self.display.show_score(hit=1)
            else:
                self.display.show_score(avoid=1)

            return True