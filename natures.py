from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, BitMask32, TransformState
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletCylinderShape, ZUp
from panda3d.bullet import BulletBoxShape, BulletConvexHullShape

from geomnode_maker import Sphere


MASK = BitMask32(1) | BitMask32.bit(2)


class Tree(NodePath):

    def __init__(self, pos, angle, parent):
        super().__init__(BulletRigidBodyNode('tree'))
        model = base.loader.loadModel('models/plant6/plants6')
        model.set_scale(0.5)
        model.set_transform(TransformState.make_pos(Vec3(0, 0, -10)))
        model.reparent_to(self)

        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(1, height, ZUp)
        self.node().add_shape(shape)

        self.set_collide_mask(MASK)
        self.set_h(angle)
        self.set_pos(pos)
        self.reparent_to(parent)


class Rock(NodePath):

    def __init__(self, pos, hpr, parent):
        super().__init__(BulletRigidBodyNode('rock'))
        model = Sphere(segments=8)
        tex = base.loader.load_texture('textures/rock1.jpg')
        model.set_texture(tex)
        model.reparent_to(self)

        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))

        self.node().add_shape(shape)
        self.set_collide_mask(MASK)
        self.set_hpr(hpr)
        self.set_pos(pos)
        self.set_scale(Vec3(5, 3, 5))
        self.reparent_to(parent)


class Flower(NodePath):

    def __init__(self, pos, parent):
        super().__init__(PandaNode('flower'))
        model = base.loader.loadModel('models/shrubbery2/shrubbery2')
        model.set_scale(0.004)
        model.reparent_to(self)
        self.set_pos(pos)
        self.reparent_to(parent)


class Grass(NodePath):

    def __init__(self, pos, parent):
        super().__init__(PandaNode(f'grass{pos.x}'))
        model = base.loader.loadModel('models/shrubbery/shrubbery')
        model.set_scale(0.05)
        model.reparent_to(self)
        self.set_pos(pos)
        self.reparent_to(parent)