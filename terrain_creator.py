import itertools
import random
from enum import Enum, auto

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletSphereShape, BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, BitMask32, LColor, Vec2
from panda3d.core import Filename
from panda3d.core import PNMImage
from panda3d.core import Shader
from panda3d.core import CardMaker, TextureStage, Texture
from panda3d.core import TransparencyAttrib, TransformState
from panda3d.core import GeoMipTerrain

from heightfield_tiles import HeightfieldTiles
from utils import create_line_node
from natures import Rock, Flower, Grass, LeaflessTree, FirTree, PineTree, PalmTree, RedFlower


class Areas(Enum):

    LEAFLESS_TREE = auto()
    ROCK = auto()
    FLOWER = auto()
    GRASS = auto()
    FIR_TREE = auto()
    PINE_TREE = auto()
    PARM_TREE = auto()


class Images(Enum):

    WATER = 'water.png'
    NOISE = 'noise2.png'
    SMALL_STONES = 'small_stones.jpg'
    BROWNISH_GRASS = 'grass1.jpg'
    GREEN_GRASS = 'grass.png'
    DARK_GRASS = 'grass2.jpg'

    @property
    def path(self):
        return f'textures/{self.value}'


class WaterSurface(NodePath):

    def __init__(self, size, pos):
        super().__init__(NodePath('water'))
        card = CardMaker('surface')
        card.set_frame(0, size, 0, size)
        self.surface = self.attach_new_node(card.generate())
        self.surface.look_at(Vec3.down())
        self.surface.set_transparency(TransparencyAttrib.M_alpha)
        self.set_pos(pos)
        self.set_shader()

    def set_shader(self):
        tex = base.loader.load_texture(Images.WATER.path)
        tex.setWrapU(Texture.WMClamp)
        tex.setWrapV(Texture.WMClamp)
        self.surface.set_texture(tex)
        shader = Shader.load(Shader.SL_GLSL, 'shaders/water_v.glsl', 'shaders/water_f.glsl')
        self.surface.set_shader(shader)
        self.surface.set_shader_input('noise', base.loader.loadTexture(Images.NOISE.path))
        props = base.win.get_properties()
        self.surface.set_shader_input('u_resolution', props.get_size())


class BulletTerrain(NodePath):

    def __init__(self, pos):
        super().__init__(BulletRigidBodyNode('compoundTerrain'))
        self.set_pos(pos)
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))
        # self.node().set_kinematic(True)

    def compound(self, file_path, height, pos):
        img = PNMImage(Filename(file_path))
        shape = BulletHeightfieldShape(img, height, ZUp)
        shape.set_use_diamond_subdivision(True)
        # new_pos = Point3(pos.x + 128.5, pos.y + 128.5, 0)
        # new_pos = Point3(pos.x + 128, pos.y + 128, 0)
        self.node().add_shape(shape, TransformState.make_pos(pos))


class TerrainRoot(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('terrain_root'))
        self.world = world
        self.height = 30

        self.terrains = NodePath('terrains')
        self.terrains.reparent_to(self)

        self.bullet_terrain = BulletTerrain(Point3(0, 0, 0))
        self.bullet_terrain.reparent_to(self.terrains)
        self.world.attach(self.bullet_terrain.node())

        self.natures = NodePath('natures')
        self.natures.reparent_to(self)

        self.test_shape = BulletSphereShape(4)
        self.angles = [n for n in range(0, 360, 10)]

        self.terrain_roots = []
        self.heightfield_tiles = HeightfieldTiles()
        self.tiles_gen = itertools.chain(
            *[tile for tile in self.heightfield_tiles])

    def load_textures(self):
        files = [
            Images.SMALL_STONES,
            Images.BROWNISH_GRASS,
            Images.GREEN_GRASS,
            Images.DARK_GRASS
        ]

        for i, file in enumerate(files):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            texture = base.loader.load_texture(file.path)
            yield ts, texture

    def make_terrain(self):
        textures = [(ts, tex) for ts, tex in self.load_textures()]

        for i, tile in enumerate(self.heightfield_tiles):
            terrain = GeoMipTerrain(f'terrain{i}')
            terrain.set_heightfield(tile.file.path)
            # terrain.setBruteforce(True)
            terrain.set_border_stitching(True)
            # terrain.clear_color_map()
            # block_size 8 and min 2, or block_size 16 and min 3 is good.
            terrain.set_block_size(8)
            terrain.set_min_level(2)
            terrain.set_focal_point(base.camera)

            root = terrain.get_root()
            root.set_scale(1, 1, self.height)
            root.set_pos(Point3(tile.origin.x - 0.5, tile.origin.y - 0.5, -(self.height / 2)))
            # root.set_two_sided(True) <- opposite side is textured too.

            for ts, tex in textures:
                root.set_texture(ts, tex)

            root.reparent_to(self.terrains)
            terrain.generate()

            # Point3(pos.x + 128.5, pos.y + 128.5, 0)
            pos = Point3(root.get_x() + 128.5, root.get_y() + 128.5, 0)
            self.bullet_terrain.compound(tile.file.path, self.height, pos)

            terrain_shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
            root.set_shader(terrain_shader)

            for i in range(4):
                root.set_shader_input(f'tex_ScaleFactor{i}', 10.0)

            if tile.count_pixels(0, 100) >= 1000:
                self.setup_water(tile)

            self.terrain_roots.append(terrain)

    def setup_water(self, tile):
        z = -(self.height / 2) + 2
        pos = Point3(tile.origin, z)
        water = WaterSurface(256, pos)
        water.reparent_to(self)

    def find_position(self, x, y):
        pt_from = Point3(x, y, 30)
        pt_to = Point3(x, y, -30)

        ts_from = TransformState.make_pos(pt_from)
        ts_to = TransformState.make_pos(pt_to)

        if not self.world.sweep_test_closest(self.test_shape, ts_from, ts_to, BitMask32.bit(2), 0.0).has_hit():
            result = self.world.ray_test_closest(pt_from, pt_to, mask=BitMask32.bit(1))
            if result.has_hit():
                return result.get_hit_pos()
        return None

    def select_nature_area(self, color):
        match color:
            case 50:
                return Areas.ROCK
            case 100:
                return Areas.GRASS
            case 150:
                return Areas.FLOWER
            case 200:
                return Areas.FIR_TREE
            case 230:
                return Areas.PINE_TREE
            case _:
                return None

    def setup_nature(self, task):
        while True:
            try:
                x, y, color = next(self.tiles_gen)
            except StopIteration:
                print('nature, end')
                return task.done

            if area := self.select_nature_area(color):
                x += random.uniform(-6, 6)
                y += random.uniform(-6, 6)

                if pos := self.find_position(x, y):
                    # self.debug_line_center = create_line_node(Point3(wx, wy, 30), Point3(wx, wy, -30), LColor(1, 0, 0, 1))
                    # self.debug_line_center.reparent_to(base.render)

                    match area:
                        case Areas.ROCK:
                            self.rock(pos)
                        case Areas.PINE_TREE:
                            self.tree(PineTree, pos)
                        case Areas.FIR_TREE:
                            self.tree(FirTree, pos)
                        case Areas.FLOWER:
                            self.flower(RedFlower, pos)
                        case Areas.GRASS:
                            self.flower(Flower, pos)
                            # self.grass(pos)

                    return task.cont

    def tree(self, model, pos):
        h = random.choice(self.angles)
        tree = model(pos, Vec3(h, 0, 0))
        tree.reparent_to(self.natures)
        self.world.attach(tree.node())

    def rock(self, pos):
        hpr = Vec3(*random.sample(self.angles, 3))
        pos -= Vec3(0, 0, 3)
        scale = Vec3(random.randint(3, 5), 3, random.randint(3, 5))  # Vec3(5, 3, 5)
        rock = Rock(pos, scale, hpr)
        rock.reparent_to(self.natures)
        self.world.attach(rock.node())

    def flower(self, model, pos):
        h = random.choice(self.angles)
        flower = model(pos, Vec3(h, 0, 0))
        flower.reparent_to(self.natures)

    def grass(self, pos):
        h = random.choice(self.angles)
        grass = Grass(pos, Vec3(h, 0, 0))
        grass.reparent_to(self.natures)
