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
        scale = Vec3(random.randint(1, 3), 3, random.randint(1, 3))  # Vec3(5, 3, 5)
        rock = model(pos, scale, hpr)
        rock.reparent_to(self)
        self.world.attach(rock.node())


# class BulletTerrain(NodePath):

#     def __init__(self, pos):
#         super().__init__(BulletRigidBodyNode('compoundTerrain'))
#         self.set_pos(pos)
#         self.node().set_mass(0)
#         self.set_collide_mask(BitMask32.bit(1))
#         # self.node().set_kinematic(True)

#     def compound(self, file_path, height, pos):
#         img = PNMImage(Filename(file_path))
#         shape = BulletHeightfieldShape(img, height, ZUp)
#         shape.set_use_diamond_subdivision(True)
#         ts = TransformState.make_pos(Point3(pos.x + 128.5, pos.y + 128.5, 0))
#         self.node().add_shape(shape, ts)


class BulletTerrain(NodePath):

    def __init__(self, pos, root, file_path, height):
        super().__init__(BulletRigidBodyNode('compoundTerrain'))
        self.set_pos(pos)
        # self.set_pos(Point3(pos.x + 128.5, pos.y + 128.5, 0))
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))
        # self.node().set_kinematic(True)

        img = PNMImage(Filename(file_path))
        shape = BulletHeightfieldShape(img, height, ZUp)
        shape.set_use_diamond_subdivision(True)
        # ts = TransformState.make_pos(Point3(pos.x + 128.5, pos.y + -128.5, 0))
        # self.node().add_shape(shape, ts)
        self.node().add_shape(shape)

        self.root = root


class TerrainRoot(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('terrain_root'))
        self.world = world
        self.height = 30

        self.terrains_np = NodePath('terrains')
        self.terrains_np.reparent_to(self)

        # self.bullet_terrain_np = BulletTerrain(Point3(0, 0, 0))
        # self.bullet_terrain_np.reparent_to(self.terrains_np)
        # self.world.attach(self.bullet_terrain_np.node())

        self.water = WaterSurface()
        self.water.reparent_to(self)
        self.flowers = Flowers()
        self.flowers.reparent_to(self)
        self.trees = Trees(self.world)
        self.trees.reparent_to(self)
        self.rocks = Rocks(self.world)
        self.rocks.reparent_to(self)

        self.test_shape = BulletSphereShape(4)

        self.terrains = []
        self.heightfield_tiles = HeightfieldTiles()
        # self.tiles_gen = itertools.chain(
        #     *[tile for tile in self.heightfield_tiles])

        self.tiles_gen = itertools.chain(self.heightfield_tiles._tiles[0])


        self.setup_terrain()

    # def initialize(self):
    #     self.setup_terrain()
    #     self.set_tex_to_terrain(TerrainImages)
    #     self.set_shader_to_terrain()

    # def set_tex_to_terrain(self, images):
    #     for i, file in enumerate(TerrainImages):
    #         tex = base.loader.load_texture(file.path)
    #         ts = TextureStage(f'ts{i}')
    #         ts.set_sort(i)

    #         for terrain in self.terrains:
    #             root = terrain.get_root()
    #             root.set_texture(ts, tex)
      
    # def set_shader_to_terrain(self, images):
    #     terrain_shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
        
    #     for terrain in self.terrains:
    #         root = terrain.get_root()


    #         for i, file in enumerate(TerrainImages):
    #             root.set_shader_input(f'tex_ScaleFactor{i}', file.tex_scale)

    # def remove_natures(self):


    def load_textures(self):
        for i, file in enumerate(TerrainImages):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            texture = base.loader.load_texture(file.path)
            yield ts, texture

    def load_textures2(self):
        for i, file in enumerate(TerrainImages2):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            texture = base.loader.load_texture(file.path)
            yield ts, texture


    def replace_terrain(self):
        for nature in [self.water, self.trees, self.flowers, self.rocks]:
            nature.remove_from_terrain()

        for shape in self.bullet_terrain_np.node().get_shapes():
            self.bullet_terrain_np.node().remove_shape(shape)

        textures = [(ts, tex) for ts, tex in self.load_textures2()]

        for i, tile in enumerate(self.heightfield_tiles):
            terrain = self.terrains[i]
            terrain.set_heightfield(tile.file.path)
            root = terrain.get_root()
            self.bullet_terrain_np.compound(tile.file.path, self.height, root.get_pos())

            if tile.count_pixels(0, 100) >= 1000:
                self.water.add_to_terrain(Point3(tile.origin, root.get_z() + 2))

            root.clear_texture()
            for ts, tex in textures:
                # old_tex = root.get_texture()
                # root.replace_texture(old_tex, tex)
                # root.clear_texture(ts)
                root.set_texture(ts, tex)
            # terrain.generate()

            # terrain_shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
            # root.set_shader(terrain_shader)

            # for i, file in enumerate(TerrainImages2):
            #     root.set_shader_input(f'tex_ScaleFactor{i}', file.tex_scale)


    def setup_terrain(self):
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

            root_pos = Point3(tile.origin.x - 0.5, tile.origin.y - 0.5, -(self.height / 2))
            root = terrain.get_root()
            root.set_scale(Vec3(1, 1, self.height))
            root.set_pos(root_pos)
            # root.set_two_sided(True) <- opposite side is textured too.

            for ts, tex in textures:
                root.set_texture(ts, tex)

            root.reparent_to(self.terrains_np)
            terrain.generate()

            pos = Point3(tile.center.x, tile.center.y, 0)
            bullet_terrain = BulletTerrain(pos, root, tile.file.path, self.height)
            bullet_terrain.reparent_to(self.terrains_np)
            self.world.attach(bullet_terrain.node())

            # self.bullet_terrain_np.compound(tile.file.path, self.height, root_pos)

            terrain_shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
            root.set_shader(terrain_shader)

            for i, file in enumerate(TerrainImages):
                root.set_shader_input(f'tex_ScaleFactor{i}', file.tex_scale)

            if tile.count_pixels(0, 100) >= 1000:
                self.water.add_to_terrain(Point3(tile.origin, root_pos.z + 2))

            self.terrains.append(terrain)



    # def make_terrain(self):
    #     textures = [(ts, tex) for ts, tex in self.load_textures()]

    #     for i, tile in enumerate(self.heightfield_tiles):
    #         terrain = GeoMipTerrain(f'terrain{i}')
    #         terrain.set_heightfield(tile.file.path)
    #         # terrain.setBruteforce(True)
    #         terrain.set_border_stitching(True)
    #         # terrain.clear_color_map()
    #         # block_size 8 and min 2, or block_size 16 and min 3 is good.
    #         terrain.set_block_size(8)
    #         terrain.set_min_level(2)
    #         terrain.set_focal_point(base.camera)

    #         root = terrain.get_root()
    #         root.set_scale(1, 1, self.height)
    #         root.set_pos(Point3(tile.origin.x - 0.5, tile.origin.y - 0.5, -(self.height / 2)))
    #         # root.set_two_sided(True) <- opposite side is textured too.

    #         for ts, tex in textures:
    #             root.set_texture(ts, tex)

    #         root.reparent_to(self.terrains)
    #         terrain.generate()

    #         # Point3(pos.x + 128.5, pos.y + 128.5, 0)
    #         pos = Point3(root.get_x() + 128.5, root.get_y() + 128.5, 0)
    #         self.bullet_terrain.compound(tile.file.path, self.height, pos)

    #         terrain_shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
    #         root.set_shader(terrain_shader)

    #         for i, file in enumerate(TerrainImages):
    #             root.set_shader_input(f'tex_ScaleFactor{i}', file.tex_scale)

    #         if tile.count_pixels(0, 100) >= 1000:
    #             self.setup_water(tile)

    #         self.terrain_roots.append(terrain)

   
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

    def setup_nature(self, task):
        while True:
            try:
                x, y, area = next(self.tiles_gen)
            except StopIteration:
                print('nature, end')
                return task.done

            x += random.uniform(-10, 10)
            y += random.uniform(-10, 10)

            if pos := self.find_position(x, y):
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