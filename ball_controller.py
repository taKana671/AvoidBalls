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


class Colors(Enum):

    RED = LColor(1, 0, 0, 1)
    BLUE = LColor(0, 0, 1, 1)
    YELLOW = LColor(1, 1, 0, 1)
    MAGENDA = LColor(1, 0, 1, 1)
    LIME = LColor(0, 1, 0, 0)

    @classmethod
    def all_colors(cls):
        return [color.value for color in cls]


class Ball(NodePath):

    def __init__(self, sphere, color, start_pt, end_pt, scale=0.5):
        super().__init__(BulletRigidBodyNode('ball'))
        self.ball = sphere.copy_to(self)
        self.set_scale(scale)
        self.set_color(color)
        self.set_collide_mask(BitMask32.bit(3))
        self.node().set_kinematic(True)

        end, tip = self.ball.get_tight_bounds()
        size = tip - end
        self.node().add_shape(BulletSphereShape(size.z / 2))

        mid_pt = (start_pt + end_pt) / 2
        mid_pt.z += 20
        self.passing_pts = (start_pt, mid_pt, end_pt)
        self.total_dt = 0

    def make_splash(self, parent):
        start_pt = self.get_pos()
        color = self.get_color()

        for _ in range(10):
            ball = self.ball.copy_to(parent)
            ball.set_color(color)
            start_scale = random.uniform(0.2, 0.4)
            end_pt = start_pt + Vec3(random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(1, 4))
            para = Parallel(
                ProjectileInterval(ball, duration=0.5, startPos=start_pt, endPos=end_pt, gravityMult=1.0),
                ball.scaleInterval(0.5, Vec3(0.01), Vec3(start_scale))
            )
            yield para

    def splash(self):
        splash = NodePath('splash')
        splash.reparent_to(self.get_parent())

        return Sequence(
            Parallel(*[para for para in self.make_splash(splash)]),
            Func(lambda: splash.remove_node())
        )


class BallController:

    def __init__(self, world, walker, terrains):
        self.world = world
        self.walker = walker
        self.terrains = terrains
        self.ball = Sphere()
        self.moving_q = deque()
        self.colors = Colors.all_colors()

        self.balls = NodePath('balls')
        self.balls.reparent_to(base.render)

    def get_shoot_pos(self, walker_pos):
        hor_film_size = base.camLens.get_fov()[0]
        camera_front = int(base.camera.get_h() + hor_film_size)
        angle_range = (camera_front - 60, camera_front + 60)
        angle = random.randint(*angle_range)

        x = 100 * round(math.cos(math.radians(angle)), 2)
        y = 100 * round(math.sin(math.radians(angle)), 2)
        pt2 = Point2(x, y)

        z = self.terrains.get_terrain_elevaton(pt2)
        shoot_pos = Point3(pt2 + walker_pos.xy, z + 20)
        return shoot_pos

    def predict_walker_pos(self, walker_pos):
        predict_pos = walker_pos + self.walker.get_orientation() * -10 * 0.8
        # predict_pos.x += random.uniform(-1.0, 1.0)
        # predict_pos.y += random.uniform(-1.0, 1.0)
        return predict_pos

    def shoot(self):
        if location := self.walker.current_location():
            walker_pos = location.get_hit_pos()
            shoot_pos = self.get_shoot_pos(walker_pos)
            predicted_walker_pos = self.predict_walker_pos(walker_pos)

            color = random.choice(self.colors)
            ball = Ball(self.ball, color, shoot_pos, predicted_walker_pos)
            # ball = Ball(self.ball, color, shoot_pos, walker_pos)
            ball.reparent_to(self.balls)
            self.world.attach(ball.node())
            self.moving_q.append(ball)

    def bernstein(self, n, k, t):
        coef = math.factorial(n) / (math.factorial(k) * math.factorial(n - k))
        return coef * t ** k * (1 - t) ** (n - k)

    def bezier_curve(self, ball, dt):
        ball.total_dt += dt
        if ball.total_dt > 1:
            ball.total_dt = 1

        n = len(ball.passing_pts) - 1
        px = py = pz = 0

        for i, pt in enumerate(ball.passing_pts):
            b = self.bernstein(n, i, ball.total_dt)
            px += np.dot(b, pt[0])
            py += np.dot(b, pt[1])
            pz += np.dot(b, pt[2])

        return Point3(px, py, pz)

    def update(self, dt):
        for _ in range(len(self.moving_q)):
            ball = self.moving_q.popleft()
            next_pt = self.bezier_curve(ball, dt)

            if self.will_collide(ball.get_pos(), next_pt) or ball.total_dt == 1:
                splash = ball.splash()
                self.world.remove(ball.node())
                ball.remove_node()
                splash.start()
                continue

            ball.set_pos(next_pt)
            self.moving_q.append(ball)

    def will_collide(self, pt_from, pt_to):
        ts_from = TransformState.make_pos(pt_from)
        ts_to = TransformState.make_pos(pt_to)
        test_shape = BulletSphereShape(0.5)
        result = self.world.sweep_test_closest(test_shape, ts_from, ts_to, BitMask32.bit(1) | BitMask32.bit(2), 0.0)

        if result.has_hit():
            print('ball callid with', result.get_node(), result.get_hit_pos())
            return True