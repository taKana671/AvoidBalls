import itertools
import pathlib
import random
from enum import Enum, auto

from datetime import datetime

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletSphereShape, BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, BitMask32, LColor, Vec2, Point2
from panda3d.core import Filename
from panda3d.core import PNMImage
from panda3d.core import Shader
from panda3d.core import CardMaker, TextureStage, Texture
from panda3d.core import TransparencyAttrib, TransformState
from panda3d.core import GeoMipTerrain

from heightfield_tiles import HeightfieldTiles, Areas
from utils import create_line_node
from natures import Rock, Flower, Grass, LeaflessTree, FirTree, PineTree, PalmTree, RedFlower


class Images(Enum):

    WATER = 'water.png'
    NOISE = 'noise2.png'
    # SMALL_STONES = 'small_stones.jpg'
    SMALL_STONES = 'riverbed.jpg'
    BROWNISH_GRASS = 'grass01.jpg'
    GREEN_GRASS = 'grass.png'
    DARK_GRASS = 'grass2.jpg'

    @property
    def path(self):
        return f'textures/{self.value}'


class TerrainImages(Enum):

    SMALL_STONES = ('small_stones.jpg', 30)
    # RIVERBED = ('layingrock.jpg', 100)
    BROWNISH_GRASS = ('grass0.jpg', 10)
    GREEN_GRASS = ('grass.png', 10)
    DARK_GRASS = ('grass2.jpg', 10)

    def __init__(self, file, tex_scale):
        super().__init__()
        self.file = file
        self.tex_scale = tex_scale

    @property
    def path(self):
        return f'textures/{self.file}'


class TerrainImages2(Enum):

    SMALL_STONES = ('sand1.jpg', 30)
    # RIVERBED = ('layingrock.jpg', 100)
    BROWNISH_GRASS = ('dark_green.jpg', 10)
    GREEN_GRASS = ('grass.png', 10)
    DARK_GRASS = ('grass2.jpg', 10)

    def __init__(self, file, tex_scale):
        super().__init__()
        self.file = file
        self.tex_scale = tex_scale

    @property
    def path(self):
        return f'textures/{self.file}'


class WaterSurface(NodePath):

    def __init__(self):
        super().__init__(PandaNode('surface_root'))

    def remove_from_terrain(self):
        for np in self.get_children():
            np.remove_node()

    def add_to_terrain(self, pos, size=256):
        np = NodePath('water_surface')
        card = CardMaker('card')
        card.set_frame(0, size, 0, size)
        surface = np.attach_new_node(card.generate())
        surface.look_at(Vec3.down())
        surface.set_transparency(TransparencyAttrib.M_alpha)
        surface.set_pos(pos)

        tex = base.loader.load_texture(Images.WATER.path)
        tex.setWrapU(Texture.WMClamp)
        tex.setWrapV(Texture.WMClamp)
        surface.set_texture(tex)

        self.set_water_shader(surface)
        surface.reparent_to(self)

    def set_water_shader(self, surface):
        shader = Shader.load(Shader.SL_GLSL, 'shaders/water_v.glsl', 'shaders/water_f.glsl')
        surface.set_shader(shader)
        surface.set_shader_input('noise', base.loader.loadTexture(Images.NOISE.path))
        props = base.win.get_properties()
        surface.set_shader_input('u_resolution', props.get_size())


class Flowers(NodePath):

    def __init__(self):
        super().__init__(PandaNode('flower_root'))
        self.angles = [n for n in range(0, 360, 10)]

    def remove_from_terrain(self):
        for np in self.get_children():
            np.remove_node()

    def add_to_terrain(self, model, pos):
        h = random.choice(self.angles)
        flower = model(pos, Vec3(h, 0, 0))
        flower.reparent_to(self)


class Trees(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('tree_root'))
        self.world = world
        self.angles = [n for n in range(0, 360, 10)]

    def remove_from_terrain(self):
        for np in self.get_children():
            self.world.remove(np.node())
            np.remove_node()

    def add_to_terrain(self, model, pos):
        h = random.choice(self.angles)
        tree = model(pos, Vec3(h, 0, 0))
        tree.reparent_to(self)
        self.world.attach(tree.node())


class Rocks(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('rock_root'))
        self.world = world
        self.angles = [n for n in range(0, 360, 10)]

    def remove_from_terrain(self):
        for np in self.get_children():
            self.world.remove(np.node())
            np.remove_node()

    def add_to_terrain(self, model, pos):
        hpr = Vec3(*random.sample(self.angles, 3))
        pos -= Vec3(0, 0, 3)
        scale = Vec3(random.randint(1, 5), 3, random.randint(1, 5))  # Vec3(5, 3, 5)
        rock = model(pos, scale, hpr)
        rock.reparent_to(self)
        self.world.attach(rock.node())


class BulletTerrain(NodePath):

    def __init__(self, tile, height, num):
        super().__init__(BulletRigidBodyNode(f'bullet_terrain_{num}'))
        self.tile = tile
        self.height = height

        self.set_pos(Point3(self.tile.center, 0))
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))
        self.add_terrain_shape()
        # self.node().set_kinematic(True)

    def add_terrain_shape(self):
        img = PNMImage(Filename(self.tile.file))
        shape = BulletHeightfieldShape(img, self.height, ZUp)
        shape.set_use_diamond_subdivision(True)
        self.node().add_shape(shape)

    def remove_terrain_shape(self):
        for shape in self.node().get_shapes():
            self.node().remove_shape(shape)

    def replace_heightfield(self):
        self.remove_terrain_shape()
        self.add_terrain_shape()
        self.terrain.set_heightfield(self.tile.file)
        self.terrain.generate()

    def make_geomip_terrain(self, texture_set):
        name = pathlib.Path(self.tile.file).stem
        self.terrain = GeoMipTerrain(f'terrain_{name}')
        self.terrain.set_heightfield(self.tile.file)
        # terrain.setBruteforce(True)
        self.terrain.set_border_stitching(True)
        # terrain.clear_color_map()
        # block_size 8 and min 2, or block_size 16 and min 3 is good.
        self.terrain.set_block_size(8)
        self.terrain.set_min_level(2)
        self.terrain.set_focal_point(base.camera)

        pos = Point3(-self.tile.size / 2, -self.tile.size / 2, -(self.height / 2))
        self.root = self.terrain.get_root()
        self.root.set_scale(Vec3(1, 1, self.height))
        self.root.set_pos(pos)
        self.terrain.generate()
        self.root.reparent_to(self)

        shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
        self.root.set_shader(shader)

        self.texture_to_terrain(texture_set)

    def texture_to_terrain(self, texture_set):
        self.root.clear_texture()
        for i, (tex, tex_scale) in enumerate(texture_set):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            self.root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
            self.root.set_texture(ts, tex)

    def get_terrain_elevaton(self, pt):
        return self.terrain.get_elevation(*pt) * self.root.get_sz()


class TerrainRoot(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('terrain_root'))
        self.world = world
        self.height = 30

        self.terrains = NodePath('terrains')
        self.terrains.reparent_to(self)

        self.water = WaterSurface()
        self.water.reparent_to(self)
        self.flowers = Flowers()
        self.flowers.reparent_to(self)
        self.trees = Trees(self.world)
        self.trees.reparent_to(self)
        self.rocks = Rocks(self.world)
        self.rocks.reparent_to(self)

        self.test_shape = BulletSphereShape(4)

        self.bullet_terrains = []
        self.heightfield_tiles = HeightfieldTiles()
        self.initialize(TerrainImages)

    def load_texture_set(self, texture_set):
        for item in texture_set:
            tex = base.loader.load_texture(item.path)
            yield tex, item.tex_scale

    def replace_terrain(self, texture_set=None):
        texture_set = [(tex, scale) for tex, scale in self.load_texture_set(TerrainImages2)]

        for nature in [self.water, self.trees, self.flowers, self.rocks]:
            nature.remove_from_terrain()

        for bullet_terrain in self.bullet_terrains:
            bullet_terrain.replace_heightfield()

            if texture_set is not None:
                bullet_terrain.texture_to_terrain(texture_set)

        base.taskMgr.do_method_later(0.2, self.setup_nature, 'setup_nature')

    def initialize(self, texture_set):
        texture_set = [(tex, scale) for tex, scale in self.load_texture_set(texture_set)]

        for i, tile in enumerate(self.heightfield_tiles):
            bullet_terrain = BulletTerrain(tile, self.height, i)
            bullet_terrain.make_geomip_terrain(texture_set)
            bullet_terrain.reparent_to(self.terrains)
            self.world.attach(bullet_terrain.node())
            self.bullet_terrains.append(bullet_terrain)

    def setup_nature(self, task):
        print(datetime.now())
        generators = []

        for i, terrain in enumerate(self.bullet_terrains):
            terrain.done_nature_setup = False
            if terrain.tile.count_pixels(0, 100) >= 1000:
                xy = terrain.tile.center - Vec2(terrain.tile.size / 2)
                z = terrain.root.get_z() + 2
                self.water.add_to_terrain(Point3(xy, z))

            generators.append(iter(terrain.tile))

        base.taskMgr.add(self.add_nature, f'add_nature_{i}', extraArgs=[generators], appendTask=True)
        return task.done

    def check_position(self, x, y):
        pt_from = Point3(x, y, 30)
        pt_to = Point3(x, y, -30)

        ts_from = TransformState.make_pos(pt_from)
        ts_to = TransformState.make_pos(pt_to)

        if not self.world.sweep_test_closest(self.test_shape, ts_from, ts_to, BitMask32.bit(2), 0.0).has_hit():
            result = self.world.ray_test_closest(pt_from, pt_to, mask=BitMask32.bit(1))
            if result.has_hit():
                return result.get_hit_pos()
        return None

    def add_nature(self, genedators, task):
        for i, gen in enumerate(genedators):
            try:
                if gen is not None:
                    x, y, area = next(gen)
            except StopIteration:
                print(f'nature, end {i}', datetime.now())
                genedators[i] = None

                if all(gen is None for gen in genedators):
                    base.messenger.send('done_setup_nature')
                    return task.done

        x += random.uniform(-10, 10)
        y += random.uniform(-10, 10)

        if pos := self.check_position(x, y):
            # self.debug_line_center = create_line_node(Point3(wx, wy, 30), Point3(wx, wy, -30), LColor(1, 0, 0, 1))
            # self.debug_line_center.reparent_to(base.render)

            match area:
                case Areas.LOWLAND:
                    self.rocks.add_to_terrain(Rock, pos)
                case Areas.PLAIN:
                    self.flowers.add_to_terrain(RedFlower, pos)
                case Areas.MOUNTAIN:
                    self.trees.add_to_terrain(PineTree, pos)
                case Areas.SUBALPINE:
                    self.trees.add_to_terrain(FirTree, pos)
                case Areas.ALPINE:
                    self.flowers.add_to_terrain(Grass, pos)

        return task.cont

    def get_terrain_elevaton(self, pt):
        x = -1 if pt.x <= 0 else 1
        y = -1 if pt.x <= 0 else 1

        for terrain in self.bullet_terrains:
            if terrain.tile.quadrant == Point2(x, y):
                z = terrain.get_terrain_elevaton(pt)
                return z