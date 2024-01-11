import math
import random
from collections import deque

import numpy as np
from direct.interval.IntervalGlobal import ProjectileInterval, Parallel, Sequence, Func
from panda3d.core import NodePath, TransformState
from panda3d.core import BitMask32, LColor, Point3, Vec3
from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape


from geomnode_maker import Sphere


class Ball(NodePath):

    def __init__(self, sphere, color, start_pt, end_pt, scale=0.5):
        super().__init__(BulletRigidBodyNode('ball'))
        self.ball = sphere.copy_to(self)
        self.set_scale(scale)
        self.set_color(color)
        self.set_collide_mask(BitMask32.bit(1))
        # self.node().set_mass(1)
        self.node().set_kinematic(True)

        end, tip = self.ball.get_tight_bounds()
        size = tip - end
        self.node().add_shape(BulletSphereShape(size.z / 2))

        self.calc_passing_point(start_pt, end_pt)

    def calc_passing_point(self, start_pt, end_pt):
        mid_pt = (start_pt + end_pt) / 2
        mid_pt.z += 10
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

    def __init__(self, world, walker):
        self.world = world
        self.walker = walker
        self.ball = Sphere()

        self.balls = NodePath('balls')
        self.balls.reparent_to(base.render)

        self.moving_q = deque()
        self.remove_q = deque()

    def shoot(self):
        if location := self.walker.current_location():
            start_pt = Point3(-256, 256, 20)
            end_pt = location.get_hit_pos()

            end_pt.x += random.uniform(-1.0, 1.0)
            end_pt.y += random.uniform(-1.0, 1.0)

            ball = Ball(self.ball, LColor(1, 0, 0, 1), start_pt, end_pt)
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
        for _ in range(len(self.remove_q)):
            ball = self.remove_q.popleft()
            splash = ball.splash()
            self.world.remove(ball.node())
            ball.remove_node()
            splash.start()

        if n := len(self.moving_q):
            for _ in range(n):
                ball = self.moving_q.popleft()
                next_pt = self.bezier_curve(ball, dt)

                if self.will_collide(ball.get_pos(), next_pt) or ball.total_dt == 1:
                    self.remove_q.append(ball)
                else:
                    self.moving_q.append(ball)

                ball.set_pos(next_pt)

    def will_collide(self, pt_from, pt_to):
        ts_from = TransformState.make_pos(pt_from)
        ts_to = TransformState.make_pos(pt_to)
        test_shape = BulletSphereShape(0.5)

        result = self.world.sweep_test_closest(test_shape, ts_from, ts_to, BitMask32.bit(2), 0.0)

        if result.has_hit():
            print(result.get_node(), result.get_hit_pos())
            # import pdb; pdb.set_trace()
            return True

        # print(self.balls.get_children())
        # for ball in self.root.get_children():
        #     for contact in set(self.world.contact_test(ball.node(), use_filter=True).get_contacts()):
        #         print('node0', contact.get_node0().get_name())
        #         print('node1', contact.get_node1().get_name())

        #     print('-------------------------------')
        #         # self.world.remove(ball.node())
        #         # ball.remove_node()
