from panda3d.bullet import BulletRigidBodyNode, BulletConvexHullShape, BulletCylinderShape, ZUp
from panda3d.core import NodePath
from panda3d.core import TransformState
from panda3d.core import Point3, Vec3

from geomnode_maker import Cylinder


class GoalBanner(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('goal'))
        self.assemble()

    def assemble(self):
        for pos in [Point3(-1, 0, 0), Point3(1, 0, 0)]:
            model = Cylinder(radius=0.15, height=3, segs_a=6)
            model.set_pos(pos)
            model.reparent_to(self)
            shape = BulletConvexHullShape()
            shape.add_geom(model.node().get_geom(0))
            # ts = TransformState.make_pos_hpr_scale(pos, Vec3(0), Vec3(1, 1, 3))
            self.node().add_shape(shape, TransformState.make_pos(pos))

            tex = base.loader.load_texture('textures/iron.jpg')
            model.set_texture(tex)
