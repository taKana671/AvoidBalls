from panda3d.bullet import BulletSoftBodyNode
from panda3d.bullet import BulletRigidBodyNode, BulletGhostNode
from panda3d.bullet import BulletConvexHullShape, BulletBoxShape
from panda3d.bullet import BulletHelper
from panda3d.core import NodePath, PandaNode
from panda3d.core import GeomNode, GeomVertexFormat
from panda3d.core import TransformState
from panda3d.core import Point3, Vec3, BitMask32

from geomnode_maker import Cylinder


class GoalGate(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('goal'))
        self.world = world

        self.create_poles()
        self.create_sensor()
        self.create_foundation()

    def setup_gate(self, pos, angle):
        self.set_h(angle)
        self.poles.set_pos(base.render, pos)
        self.sensor.set_pos(base.render, pos + Vec3(0, 0, 1.5))
        self.foundation.set_pos(base.render, pos)
        self.create_banner()

        pole_l = self.poles.left.get_pos(base.render)
        pole_r = self.poles.right.get_pos(base.render)
        self.sensor.setup_sensor(pole_l, pole_r)

    def cleanup_gate(self):
        self.world.remove(self.banner.node())
        self.banner.remove_node()

    def create_poles(self):
        self.poles = Poles(Point3(-3, 0, 0), Point3(3, 0, 0))
        tex = base.loader.load_texture('textures/bark1.jpg')
        self.poles.set_texture(tex)
        self.poles.reparent_to(self)
        self.world.attach(self.poles.node())

    def create_sensor(self):
        self.sensor = Sensor(Point3(0, 0, 3))
        self.world.attach_ghost(self.sensor.node())
        self.sensor.reparent_to(self)

    def create_foundation(self):
        """Make box shape to prevent for natures, including trees and rocks,
           from being positioned around goal gate.
        """
        self.foundation = NodePath(BulletRigidBodyNode('foundation'))
        shape = BulletBoxShape(Vec3(3, 3, 0.25))
        self.foundation.node().add_shape(shape, TransformState.make_pos(Point3(0, 0, 0.25)))
        self.foundation.set_collide_mask(BitMask32.bit(5))
        self.foundation.reparent_to(self)
        self.world.attach(self.foundation.node())

    def create_banner(self):
        info = self.world.get_world_info()
        info.set_air_density(1.2)
        info.set_water_density(0)
        info.set_water_offset(0)
        info.set_water_normal(Vec3(0, 0, 0))

        resx = 4
        resy = 4

        left_w_pt = self.poles.left.get_pos(base.render)
        right_w_pt = self.poles.right.get_pos(base.render)

        corner00 = left_w_pt + Vec3(0, 0, 4)   # bottom left
        corner01 = right_w_pt + Vec3(0, 0, 4)  # top left
        corner10 = left_w_pt + Vec3(0, 0, 6)   # bottom right
        corner11 = right_w_pt + Vec3(0, 0, 6)  # top right

        fixeds = 1 + 2 + 4 + 8
        gendiags = True

        self.banner = Cloth(info, corner00, corner10, corner01, corner11, resx, resy, fixeds, gendiags)
        self.world.attach(self.banner.node())
        self.banner.reparent_to(self)


class Cloth(NodePath):

    def __init__(self, info, corner00, corner10, corner01, corner11, resx, resy, fixeds, gendiags):
        super().__init__(BulletSoftBodyNode.make_patch(info, corner00, corner10, corner01, corner11, resx, resy, fixeds, gendiags))
        material = self.node().append_material()
        material.set_linear_stiffness(0.4)
        self.node().generate_bending_constraints(2, material)
        self.node().set_total_mass(50.0)
        self.node().get_shape(0).set_margin(0.5)
        self.set_name('banner')
        self.set_collide_mask(BitMask32.all_on())

        fmt = GeomVertexFormat.getV3n3t2()
        geom = BulletHelper.make_geom_from_faces(self.node(), fmt, True)
        self.node().link_geom(geom)

        vis_nd = GeomNode('visualisation')
        vis_nd.add_geom(geom)
        vis_np = self.attach_new_node(vis_nd)
        vis_np.reparent_to(self)
        vis_np.set_texture(base.loader.load_texture('textures/finish3.png'))
        BulletHelper.make_texcoords_for_patch(geom, resx, resy)


class Poles(NodePath):

    def __init__(self, left_pt, right_pt):
        super().__init__(BulletRigidBodyNode('poles'))
        self.set_collide_mask(BitMask32.bit(1))
        self.left = self.assemble(left_pt)
        self.right = self.assemble(right_pt)

    def assemble(self, pos):
        cylinder = Cylinder(radius=0.15, height=6, segs_a=12)
        cylinder.set_pos(pos)
        cylinder.reparent_to(self)
        shape = BulletConvexHullShape()
        shape.add_geom(cylinder.node().get_geom(0))
        self.node().add_shape(shape, TransformState.make_pos(pos))
        return cylinder


class Sensor(NodePath):

    def __init__(self, pos):
        super().__init__(BulletGhostNode('sensor'))
        shape = BulletBoxShape(Vec3(3, 0.125, 0.125))
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.bit(4))

    def setup_sensor(self, pole_l, pole_r):
        """Make variables for sensor.
            Args:
                pole_l (Point3): the point where the left pole is placed.
                pole_r (Point3): the point where the right pole is placed.
        """
        self.pole_l = pole_l
        self.pole_r = pole_r
        self.finish_line = False
        self.in_pt = None
        self.out_pt = None

    def detect(self):
        for nd in self.node().get_overlapping_nodes():
            return nd

    def check_finish(self, task):
        if nd := self.detect():
            walker_pos = NodePath(nd).get_pos()
            if not self.in_pt:
                self.in_pt = walker_pos
                print('walker is near goal line:', self.in_pt)

            self.out_pt = walker_pos
            return task.cont

        if self.in_pt:
            print('walker is away from goal line:', self.out_pt)
            if self.judge_go_through():
                print('go throuth!!!!!!!!')
                base.messenger.send('finish')
                self.finish_line = True
                return task.done

            self.in_pt = None

        return task.cont

    def check_cross(self, a, b, c, d):
        min_ab = min(a, b)
        max_ab = max(a, b)

        min_cd = min(c, d)
        max_cd = max(c, d)

        if min_ab > max_cd or max_ab < min_cd:
            return False

        return True

    def judge_go_through(self):
        # check x
        if not self.check_cross(self.pole_l.x, self.pole_r.x, self.in_pt.x, self.out_pt.x):
            return False

        # check y
        if not self.check_cross(self.pole_l.y, self.pole_r.y, self.in_pt.y, self.out_pt.y):
            return False

        tc1 = (self.pole_l.x - self.pole_r.x) * (self.in_pt.y - self.pole_l.y) + (self.pole_l.y - self.pole_r.y) * (self.pole_l.x - self.in_pt.x)
        tc2 = (self.pole_l.x - self.pole_r.x) * (self.out_pt.y - self.pole_l.y) + (self.pole_l.y - self.pole_r.y) * (self.pole_l.x - self.out_pt.x)
        td1 = (self.in_pt.x - self.out_pt.x) * (self.pole_l.y - self.in_pt.y) + (self.in_pt.y - self.out_pt.y) * (self.in_pt.x - self.pole_l.x)
        td2 = (self.in_pt.x - self.out_pt.x) * (self.pole_r.y - self.in_pt.y) + (self.in_pt.y - self.out_pt.y) * (self.in_pt.x - self.pole_r.x)

        return tc1 * tc2 <= 0 and td1 * td2 <= 0
