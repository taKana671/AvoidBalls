import pathlib
import random
from enum import Enum
from collections import deque

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletSphereShape, BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, BitMask32, Vec2
from panda3d.core import Filename, PNMImage
from panda3d.core import Shader
from panda3d.core import TextureStage, TransformState
from panda3d.core import GeoMipTerrain

from heightfield_tiles import Areas, HeightfieldCreator
from natures import WaterSurface, Rock, Shrubbery, Grass, Fir, Pine


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


class Natures(NodePath):

    def __init__(self, name, world):
        super().__init__(PandaNode(name))
        self.world = world

        self.bullet_nature = NodePath('bullet_nature')
        self.bullet_nature.reparent_to(self)
        self.nature = NodePath('nature')
        self.nature.reparent_to(self)

    def add_to_terrain(self, nature, bullet=False):
        if bullet:
            nature.reparent_to(self.bullet_nature)
            self.world.attach(nature.node())
        else:
            nature.reparent_to(self.nature)

    def remove_from_terrain(self):
        for np in self.bullet_nature.get_children():
            self.world.remove(np.node())
            np.remove_node()

        for np in self.nature.get_children():
            np.remove_node()


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
        # self.terrain.update()

    def make_geomip_terrain(self, texture_set):
        name = pathlib.Path(self.tile.file).stem
        self.terrain = GeoMipTerrain(f'terrain_{name}')
        self.terrain.set_heightfield(self.tile.file)
        self.terrain.setBruteforce(True)
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


class Terrains(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('terrain_root'))
        self.world = world
        self.height = 30

        self.terrains = NodePath('terrains')
        self.terrains.reparent_to(self)

        self.natures = Natures('natures_root', self.world)
        self.natures.reparent_to(self)

        self.test_shape = BulletSphereShape(4)

        self.bullet_terrains = []
        self.heightfield_tiles = HeightfieldCreator()
        self.initialize(TerrainImages)

        self.natures_q = deque()

    def load_texture_set(self, texture_set):
        for item in texture_set:
            tex = base.loader.load_texture(item.path)
            yield tex, item.tex_scale

    def replace_terrain(self, texture_set=None):
        self.heightfield_tiles.concat_from_files()
        texture_set = [(tex, scale) for tex, scale in self.load_texture_set(TerrainImages2)]

        for bullet_terrain in self.bullet_terrains:
            bullet_terrain.replace_heightfield()

            # bullet_terrain.terrain.update()

            if texture_set is not None:
                bullet_terrain.texture_to_terrain(texture_set)

        # base.taskMgr.do_method_later(0.2, self.setup_nature, 'setup_nature')

    def initialize(self, texture_set):
        self.heightfield_tiles.concat_from_files()
        texture_set = [(tex, scale) for tex, scale in self.load_texture_set(texture_set)]

        for i, tile in enumerate(self.heightfield_tiles):
            bullet_terrain = BulletTerrain(tile, self.height, i)
            bullet_terrain.make_geomip_terrain(texture_set)
            bullet_terrain.reparent_to(self.terrains)
            self.world.attach(bullet_terrain.node())
            self.bullet_terrains.append(bullet_terrain)

    def setup_nature(self):
        for i, terrain in enumerate(self.bullet_terrains):
            terrain.done_nature_setup = False
            if terrain.tile.count_pixels(0, 100) >= 1000:
                xy = terrain.tile.center - Vec2(terrain.tile.size / 2)
                z = terrain.root.get_z() + 2
                pos = Point3(xy, z)
                self.natures.add_to_terrain(WaterSurface(pos))

            self.add_nature(terrain.tile)

    def check_position(self, x, y):
        pt_from = Point3(x, y, 30)
        pt_to = Point3(x, y, -30)

        ts_from = TransformState.make_pos(pt_from)
        ts_to = TransformState.make_pos(pt_to)

        if not self.world.sweep_test_closest(
                self.test_shape, ts_from, ts_to, BitMask32.bit(2) | BitMask32.bit(5), 0.0).has_hit():
            result = self.world.ray_test_closest(pt_from, pt_to, mask=BitMask32.bit(1))
            if result.has_hit():
                return result
                # return result.get_hit_pos()
        return None

    def add_nature(self, tile): 
        for x, y, area in tile.get_nature_info():
            x += random.uniform(-10, 10)
            y += random.uniform(-10, 10)

            if ray_hit := self.check_position(x, y):
                pos = ray_hit.get_hit_pos()
                terrain_num = ray_hit.get_node().get_name().split('_')[-1]

                match area:
                    case Areas.LOWLAND:
                        self.natures.add_to_terrain(Rock(terrain_num, pos), True)
                    case Areas.PLAIN:
                        self.natures.add_to_terrain(Shrubbery(terrain_num, pos))
                    case Areas.MOUNTAIN:
                        self.natures.add_to_terrain(Pine(terrain_num, pos), True)
                    case Areas.SUBALPINE:
                        self.natures.add_to_terrain(Fir(terrain_num, pos), True)
                    case Areas.ALPINE:
                        self.natures.add_to_terrain(Grass(terrain_num, pos))

    def get_terrain_elevaton(self, pt, name):
        num = int(name.split('_')[-1])
        terrain = self.bullet_terrains[num]
        z = terrain.get_terrain_elevaton(pt)