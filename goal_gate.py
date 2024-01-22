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

    def __init__(self, world, pos, rotation):
        super().__init__(PandaNode('goal'))
        self.world = world
        self.set_pos(pos)
        self.set_h(rotation)

        self.create_poles()
        self.create_banner()

        self.sensor = Sensor(Point3(0, 0, 1))
        self.world.attach_ghost(self.sensor.node())
        self.sensor.reparent_to(self)

    def create_poles(self):
        self.poles = Poles(Point3(-3, 0, 0), Point3(3, 0, 0))
        self.world.attach(self.poles.node())
        self.poles.reparent_to(self)

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

        banner = Cloth(info, corner00, corner10, corner01, corner11, resx, resy, fixeds, gendiags)
        self.world.attach_soft_body(banner.node())
        banner.reparent_to(self)


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
        tex = base.loader.load_texture('textures/bark1.jpg')
        cylinder.set_texture(tex)
        return cylinder


class Sensor(NodePath):

    def __init__(self, pos):
        super().__init__(BulletGhostNode('sensor'))
        shape = BulletBoxShape(Vec3(3, 0.2, 0.5))
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.bit(4))
        self.set_pos(pos)

    def sense(self, task):
        for nd in self.node().get_overlapping_nodes():
            print(nd)

        return task.cont