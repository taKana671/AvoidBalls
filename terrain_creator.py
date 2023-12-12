import random

from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from panda3d.bullet import BulletCylinderShape, BulletSphereShape

from panda3d.bullet import BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, BitMask32, LColor, Vec2
from panda3d.core import Filename
from panda3d.core import PNMImage
from panda3d.core import ShaderTerrainMesh, Shader, load_prc_file_data
from panda3d.core import SamplerState
from panda3d.core import CardMaker, TextureStage, Texture
from panda3d.core import TransparencyAttrib, TransformState
from panda3d.core import GeoMipTerrain

from heightfield_tiles import HeightfieldTiles


class Tree(NodePath):

    def __init__(self, pos, angle):
        super().__init__(BulletRigidBodyNode('tree'))
        model = base.loader.loadModel('models/plant6/plants6')
        # model = base.loader.load_model('models/Tree/tree.')
        model.set_scale(0.5)
        model.set_h(angle)
        # model.set_scale(10)
        end, tip = model.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(0.5, height, ZUp)
        self.node().add_shape(shape, TransformState.make_pos(Point3(0, 0, height / 2)))
        self.set_collide_mask(BitMask32.bit(1) | BitMask32.bit(2))
        model.reparent_to(self)

        self.set_pos(pos)
        self.reparent_to(base.render)


class CompoundTerrain(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('compoundterrain'))
        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_kinematic(True)

    def assemble(self, img, height, pos):
        shape = BulletHeightfieldShape(img, height, ZUp)
        shape.set_use_diamond_subdivision(True)
        new_pos = Point3(pos.x + 128.5, pos.y + 128.5, 0)
        # new_pos = Point3(pos.x + 128, pos.y + 128, 0)
        self.node().add_shape(shape, TransformState.make_pos(new_pos))
        # self.node().add_shape(shape, TransformState.make_pos(pos))


class TerrainCreator:

    def __init__(self, world):
        self.world = world
        # *************************************
        # self.terrains = NodePath('terrains')
        # self.terrains.reparent_to(base.render)
        # *************************************
        self.scene = NodePath('scene')
        self.scene.reparent_to(base.render)



        self.terrains = NodePath('terrains')
        self.terrain = CompoundTerrain()
        self.terrain.set_pos(Point3(0, 0, 0))
        self.terrain.reparent_to(self.terrains)
        self.terrains.reparent_to(base.render)
        self.world.attach(self.terrain.node())

        self.terrain_roots = []
        self.heightfield_tiles = HeightfieldTiles()

    def make_terrain(self):
        for tile in self.heightfield_tiles:
            self.make_geomip_terrain(tile)

    def make_geomip_terrain(self, tile):
        height = 50
        
        height_size = PNMImage(Filename(tile.image.file_path)).get_x_size()
        # print('height_size', height_size)
        terrain = GeoMipTerrain('terrain')
        terrain.set_heightfield(tile.image.file_path)

        #************************
        terrain.set_border_stitching(True)
        terrain.clear_color_map()
        terrain.set_block_size(8)  # block_size 8 and min 2, # block_size 16 and min 3 is good.
        terrain.set_min_level(2)
       
        # terrain.set_block_size(128)
        # terrain.set_near(0)
        # terrain.set_far(1024)
        # terrain.set_focal_point(base.camera)

        root = terrain.get_root()
        root.reparent_to(self.terrains)
        # root.reparent_to(base.render)
        root.set_scale(1, 1, height)
        # self.root.set_h(90)
        # root.set_two_sided(True) <- opposite side is textured too.

        # pos = Point3(x * (height_size / 2), y * (height_size / 2), -height / 2)
        # pos = Point3(x * (height_size / 2 - 0.5), y * (height_size / 2 - 0.5), -(height / 2))
        pos = Point3(tile.origin.x - 0.5, tile.origin.y - 0.5, -(height / 2))
        root.set_pos(pos)
        # root.set_h(90)
        # print('root', root.get_pos())

        ts = TextureStage('ts0')
        ts.set_sort(0)
        texture = base.loader.load_texture('textures/small_stones.jpg')
        root.set_texture(ts, texture)
        # self.root.set_tex_scale(ts, 300, 300)

        ts = TextureStage('ts1')
        ts.set_sort(1)
        tex_grass = base.loader.load_texture('textures/grass.png')

        root.set_texture(ts, tex_grass)
        # self.root.set_tex_scale(ts, 300, 300)

        ts = TextureStage('ts2')
        ts.set_sort(2)
        tex_red = base.loader.load_texture('textures/red_ground.jpg')
        root.set_texture(ts, tex_red)
        # self.root.set_tex_scale(ts, 300, 300)

        ts = TextureStage('ts3')
        ts.set_sort(3)
        tex_dark = base.loader.load_texture('textures/dark_green.jpg')
        root.set_texture(ts, tex_dark)
        # self.root.set_texture(self.ts, self.detail_map)
        # self.root.set_tex_scale(self.ts, 300, 300)

        terrain.generate()
        img = PNMImage(Filename(tile.image.file_path))
        self.terrain.assemble(img, height, pos)
        #********************************************
        # shape = BulletHeightfieldShape(img, height, ZUp)
        # shape.set_use_diamond_subdivision(True)
        # np = self.terrains.attach_new_node(BulletRigidBodyNode('height_field'))
        # # new_pos = Point3(pos.x + 128.5, pos.y + 128.5, 0)
        # new_pos = Point3(pos.x + 128, pos.y + 128, 0)
        # np.node().add_shape(shape, TransformState.make_pos(new_pos))
        # # print('np', np.get_pos())
        # np.set_collide_mask(BitMask32.bit(1))
        # self.world.attach(np.node())
        #********************************************

        terrain_shader = Shader.load(Shader.SL_GLSL, "shaders/terrain_v.glsl", "shaders/terrain_f.glsl")
        root.set_shader(terrain_shader)
        root.set_shader_input('camera', base.camera)

        root.set_shader_input('tex_ScaleFactor0', 10.0)
        root.set_shader_input('tex_ScaleFactor1', 10.0)
        root.set_shader_input('tex_ScaleFactor2', 10.0)
        root.set_shader_input('tex_ScaleFactor3', 10.0)

        self.terrain_roots.append(terrain)

        # *******************************
        # tree = Tree()
        # z = terrain.get_elevation(10, 10) * root.get_sx()
        # tree.set_pos(10, 10, z)
        # self.world.attach(tree.node())
        # *******************************

        self.plant_trees(terrain, root, tile)

    def plant_trees(self, terrain, root, tile):
        for px, py in tile.convert_pixel_coords():
            if px % 2 == 0 and py % 2 == 0:
                wx = px + tile.center.x
                wy = py + tile.center.y
                wz = terrain.get_elevation(wx, wy) * root.get_sx()
                pos = Point3(wx, wy, wz)

                ts_from = TransformState.make_pos(pos + Vec3(0, 0, 18 * 2))
                ts_to = TransformState.make_pos(pos)
                shape = BulletSphereShape(2)
                penetration = 0.0

                result = self.world.sweep_test_closest(shape, ts_from, ts_to, BitMask32.bit(2), penetration)
                # import pdb; pdb.set_trace()
                if result.has_hit():
                    # print('hit', result.get_node())
                    continue

                angle = random.choice([0, 90, 180, 270])
                tree = Tree(pos, angle)
                self.world.attach(tree.node())

        
        




    # def make_geomip_terrain(self, img_file, x, y):
    #     height = 50
    #     # img_file = 'terrains/heightfield7.png'
    #     # img_file = 'terrains/heightfield6.png'
    #     height_size = PNMImage(Filename(img_file)).get_x_size()
    #     # print('height_size', height_size)
    #     terrain = GeoMipTerrain('terrain')
    #     terrain.set_heightfield(img_file)

    #     #************************
    #     terrain.set_border_stitching(True)
    #     terrain.clear_color_map()
    #     terrain.set_block_size(8)  # block_size 8 and min 2, # block_size 16 and min 3 is good.
    #     terrain.set_min_level(2)
       
    #     # terrain.set_block_size(128)
    #     # terrain.set_near(0)
    #     # terrain.set_far(1024)
    #     # terrain.set_focal_point(base.camera)

    #     root = terrain.get_root()
    #     root.reparent_to(self.terrains)
    #     # root.reparent_to(base.render)
    #     root.set_scale(1, 1, height)
    #     # self.root.set_h(90)
    #     # root.set_two_sided(True) <- opposite side is textured too.

    #     # pos = Point3(x * (height_size / 2), y * (height_size / 2), -height / 2)
    #     # pos = Point3(x * (height_size / 2 - 0.5), y * (height_size / 2 - 0.5), -(height / 2))
    #     pos = Point3(x - 0.5, y - 0.5, -(height / 2))
    #     root.set_pos(pos)
    #     # root.set_h(90)
    #     # print('root', root.get_pos())

    #     ts = TextureStage('ts0')
    #     ts.set_sort(0)
    #     texture = base.loader.load_texture('textures/small_stones.jpg')
    #     root.set_texture(ts, texture)
    #     # self.root.set_tex_scale(ts, 300, 300)

    #     ts = TextureStage('ts1')
    #     ts.set_sort(1)
    #     tex_grass = base.loader.load_texture('textures/grass.png')

    #     root.set_texture(ts, tex_grass)
    #     # self.root.set_tex_scale(ts, 300, 300)

    #     ts = TextureStage('ts2')
    #     ts.set_sort(2)
    #     tex_red = base.loader.load_texture('textures/red_ground.jpg')
    #     root.set_texture(ts, tex_red)
    #     # self.root.set_tex_scale(ts, 300, 300)

    #     ts = TextureStage('ts3')
    #     ts.set_sort(3)
    #     tex_dark = base.loader.load_texture('textures/dark_green.jpg')
    #     root.set_texture(ts, tex_dark)
    #     # self.root.set_texture(self.ts, self.detail_map)
    #     # self.root.set_tex_scale(self.ts, 300, 300)

    #     terrain.generate()
    #     img = PNMImage(Filename(img_file))
    #     self.terrain.assemble(img, height, pos)
    #     #********************************************
    #     # shape = BulletHeightfieldShape(img, height, ZUp)
    #     # shape.set_use_diamond_subdivision(True)
    #     # np = self.terrains.attach_new_node(BulletRigidBodyNode('height_field'))
    #     # # new_pos = Point3(pos.x + 128.5, pos.y + 128.5, 0)
    #     # new_pos = Point3(pos.x + 128, pos.y + 128, 0)
    #     # np.node().add_shape(shape, TransformState.make_pos(new_pos))
    #     # # print('np', np.get_pos())
    #     # np.set_collide_mask(BitMask32.bit(1))
    #     # self.world.attach(np.node())
    #     #********************************************

    #     terrain_shader = Shader.load(Shader.SL_GLSL, "shaders/terrain_v.glsl", "shaders/terrain_f.glsl")
    #     root.set_shader(terrain_shader)
    #     root.set_shader_input('camera', base.camera)

    #     root.set_shader_input('tex_ScaleFactor0', 10.0)
    #     root.set_shader_input('tex_ScaleFactor1', 10.0)
    #     root.set_shader_input('tex_ScaleFactor2', 10.0)
    #     root.set_shader_input('tex_ScaleFactor3', 10.0)

    #     # terrain.update()
    #     # self.terrain_roots.append(root)
    #     self.terrain_roots.append(terrain)

    #     # *******************************
    #     # tree = Tree()
    #     # z = terrain.get_elevation(10, 10) * root.get_sx()
    #     # tree.set_pos(10, 10, z)
    #     # self.world.attach(tree.node())
    #     # *******************************

    #     if img_file == 'terrains/top_left.png':
    #         # import pdb; pdb.set_trace()
    #         for i, (px, py) in enumerate(self.hf_maker.convert_pixel_coords(img_file)):
    #             if px % 2 == 0 and py % 2 == 0:
    #                 # wx = px + x * (height_size / 2)
    #                 # wy = py + y * (height_size / 2)
    #                 wx = px - 128
    #                 wy = py + 128

    #                 tree = Tree()
    #                 z = terrain.get_elevation(wx, wy) * root.get_sx()
    #                 print(wx, wy, z)
    #                 tree.set_pos(wx, wy, z)
    #                 self.world.attach(tree.node())



        