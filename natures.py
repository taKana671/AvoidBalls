from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, BitMask32, TransformState
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletCylinderShape, ZUp
from panda3d.bullet import BulletConvexHullShape

from geomnode_maker import Sphere


class Natures(NodePath):

    mask = BitMask32(1) | BitMask32.bit(2)

    def __init__(self, node, pos, scale, hpr):
        super().__init__(node)
        self.set_pos(pos)
        self.set_scale(scale)
        self.set_hpr(hpr)


class FirTree(Natures):

    def __init__(self, pos, hpr, scale=1.0):
        super().__init__(BulletRigidBodyNode('fir_tree'), pos, scale, hpr)
        model = base.loader.loadModel('models/firtree/tree1.bam')
        model.set_transform(TransformState.make_pos(Vec3(-0.25, -0.15, 0)))
        model.reparent_to(self)

        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(0.3, height, ZUp)
        self.node().add_shape(shape)
        self.set_collide_mask(Natures.mask)


class PineTree(Natures):

    def __init__(self, pos, hpr, scale=1.0):
        super().__init__(BulletRigidBodyNode('pine_tree'), pos, scale, hpr)
        model = base.loader.loadModel('models/pinetree/tree2.bam')
        model.set_transform(TransformState.make_pos(Vec3(-0.1, 0.12, 0)))
        model.reparent_to(self)

        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(0.3, height, ZUp)
        self.node().add_shape(shape)
        self.set_collide_mask(Natures.mask)


class PalmTree(Natures):

    def __init__(self, pos, hpr, scale=1.5):
        super().__init__(BulletRigidBodyNode('pine_tree'), pos, scale, hpr)
        model = base.loader.loadModel('models/palmtree/tree3.bam')
        model.set_transform(TransformState.make_pos(Vec3(-0.5, -0.03, 0)))
        model.reparent_to(self)

        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(0.3, height, ZUp)
        self.node().add_shape(shape)
        self.set_collide_mask(Natures.mask)


class LeaflessTree(Natures):

    def __init__(self, pos, hpr, scale=0.5):
        super().__init__(BulletRigidBodyNode('leafless_tree'), pos, scale, hpr)
        model = base.loader.loadModel('models/plant6/plants6')
        model.set_transform(TransformState.make_pos(Vec3(0, 0, -10)))
        model.reparent_to(self)

        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(1, height, ZUp)
        self.node().add_shape(shape)
        self.set_collide_mask(Natures.mask)


class Rock(Natures):

    def __init__(self, pos, scale, hpr):
        super().__init__(BulletRigidBodyNode('rock'), pos, scale, hpr)
        model = Sphere(segments=8)
        tex = base.loader.load_texture('textures/rock1.jpg')
        model.set_texture(tex)
        model.reparent_to(self)

        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))
        self.node().add_shape(shape)
        self.set_collide_mask(Natures.mask)


class Flower(Natures):

    def __init__(self, pos, hpr, scale=0.004):
        super().__init__(PandaNode('flower'), pos, scale, hpr)
        model = base.loader.loadModel('models/shrubbery2/shrubbery2')
        model.reparent_to(self)


class Grass(Natures):

    def __init__(self, pos, hpr, scale=0.05):
        super().__init__(PandaNode('flower'), pos, scale, hpr)
        model = base.loader.loadModel('models/shrubbery/shrubbery')
        model.reparent_to(self)


class RedFlower(Natures):

    def __init__(self, pos, hpr, scale=3):
        super().__init__(PandaNode('flower'), pos, scale, hpr)
        model = base.loader.loadModel('models/tulip/Tulip')
        model.reparent_to(self)