import random

from panda3d.core import NodePath, PandaNode
from panda3d.core import CardMaker, Texture, TextureStage
from panda3d.core import Vec3, BitMask32, TransformState
from panda3d.core import TransparencyAttrib
from panda3d.core import Shader
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletConvexHullShape, BulletCylinderShape, ZUp
from direct.interval.LerpInterval import LerpTexOffsetInterval

from geomnode_maker import Sphere


MASK = BitMask32(1) | BitMask32.bit(2)


class WaterSurface(NodePath):

    def __init__(self, pos, size=256):
        super().__init__(PandaNode('water_surface'))
        self.setup_water(pos, size)

    def setup_water(self, pos, size):
        card = CardMaker('card')
        card.set_frame(0, size, 0, size)
        surface = self.attach_new_node(card.generate())
        surface.look_at(Vec3.down())
        surface.set_transparency(TransparencyAttrib.M_alpha)
        surface.set_pos(pos)

        tex = base.loader.load_texture('textures/water.png')
        # tex.setWrapU(Texture.WMClamp)
        # tex.setWrapV(Texture.WMClamp)
        surface.set_texture(tex)
        surface.set_tex_scale(TextureStage.get_default(), 4)

        # self.set_water_shader(surface)
        surface.reparent_to(self)
        LerpTexOffsetInterval(surface, 200, (1, 0), (0, 0)).loop()

    # def set_water_shader(self, surface):
    #     shader = Shader.load(Shader.SL_GLSL, 'shaders/water_v.glsl', 'shaders/water_f.glsl')
    #     surface.set_shader(shader)
    #     surface.set_shader_input('noise', base.loader.loadTexture('textures/noise2.png'))
    #     props = base.win.get_properties()
    #     surface.set_shader_input('u_resolution', props.get_size())


class Trees(NodePath):

    def __init__(self, name, model, pos, scale):
        super().__init__(BulletRigidBodyNode(name))
        model.reparent_to(self)
        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(0.3, height, ZUp)
        self.node().add_shape(shape)
        self.set_collide_mask(MASK)

        self.setup_tree(pos, scale)

    def setup_tree(self, pos, scale):
        h = random.choice([n for n in range(0, 360, 20)])
        self.set_hpr(Vec3(h, 0, 0))
        self.set_pos(pos)
        self.set_scale(scale)


class Fir(Trees):

    def __init__(self, terrain_number, pos, scale=1.0):
        model = base.loader.loadModel('models/firtree/tree1.bam')
        model.set_transform(TransformState.make_pos(Vec3(-0.25, -0.15, 0)))
        name = f'fir_tree_{terrain_number}'
        super().__init__(name, model, pos, scale)


class Pine(Trees):

    def __init__(self, terrain_number, pos, scale=1.0):
        model = base.loader.loadModel('models/pinetree/tree2.bam')
        model.set_transform(TransformState.make_pos(Vec3(-0.1, 0.12, 0)))
        name = f'pine_tree_{terrain_number}'
        super().__init__(name, model, pos, scale)


class Palm(Trees):

    def __init__(self, terrain_number, pos, scale=1.5):
        model = base.loader.loadModel('models/palmtree/tree3.bam')
        model.set_transform(TransformState.make_pos(Vec3(-0.5, -0.03, 0)))
        name = f'palm_tree_{terrain_number}'
        super().__init__(name, model, pos, scale)


class LeaflessTree(Trees):

    def __init__(self, terrain_number, pos, scale=0.5):
        model = base.loader.loadModel('models/plant6/plants6')
        model.set_transform(TransformState.make_pos(Vec3(0, 0, -10)))
        name = f'leafless_tree_{terrain_number}'
        super().__init__(name, model, pos, scale)


class Rock(NodePath):

    def __init__(self, terrain_number, pos):
        super().__init__(BulletRigidBodyNode(f'rock_{terrain_number}'))
        model = Sphere(segments=8)
        tex = base.loader.load_texture('textures/rock1.jpg')
        model.set_texture(tex)
        model.reparent_to(self)

        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))
        self.node().add_shape(shape)
        self.set_collide_mask(MASK)

        self.setup_rock(pos)

    def setup_rock(self, pos):
        hpr = Vec3(*random.sample([n for n in range(0, 360, 20)], 3))
        pos -= Vec3(0, 0, 3)
        scale = Vec3(random.randint(1, 5), 3, random.randint(1, 5))  # Vec3(5, 3, 5)
        self.set_hpr(hpr)
        self.set_pos(pos)
        self.set_scale(scale)


class Flowers(NodePath):

    def __init__(self, name, model, pos, scale):
        super().__init__(PandaNode(name))
        model.reparent_to(self)
        self.setup_flower(pos, scale)

    def setup_flower(self, pos, scale):
        h = random.choice([n for n in range(0, 360, 20)])
        self.set_pos(pos)
        self.set_hpr(Vec3(h, 0, 0))
        self.set_scale(scale)


class Shrubbery(Flowers):

    def __init__(self, terrain_number, pos, scale=0.004):
        model = base.loader.loadModel('models/shrubbery2/shrubbery2')
        name = f'shrubbery_{terrain_number}'
        super().__init__(name, model, pos, scale)


class Grass(Flowers):

    def __init__(self, terrain_number, pos, scale=0.05):
        model = base.loader.loadModel('models/shrubbery/shrubbery')
        name = f'grass_{terrain_number}'
        super().__init__(name, model, pos, scale)


class RedFlower(Flowers):

    def __init__(self, terrain_number, pos, scale=3):
        model = base.loader.loadModel('models/tulip/Tulip')
        name = f'tulip_{terrain_number}'
        super().__init__(name, model, pos, scale)