from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
from panda3d.bullet import BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, BitMask32, LColor
from panda3d.core import Filename
from panda3d.core import PNMImage
from panda3d.core import ShaderTerrainMesh, Shader, load_prc_file_data
from panda3d.core import SamplerState
from panda3d.core import CardMaker, TextureStage, Texture
from panda3d.core import TransparencyAttrib, TransformState
from panda3d.core import GeoMipTerrain


class CompoundTerrain(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('terrain'))
        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_kinematic(True)

    def assemble(self, img, height, pos):
        shape = BulletHeightfieldShape(img, height, ZUp)
        shape.set_use_diamond_subdivision(True)
        # new_pos = Point3(pos.x + 128.5, pos.y + 128.5, 0)
        new_pos = Point3(pos.x + 128, pos.y + 128, 0)
        self.node().add_shape(shape, TransformState.make_pos(new_pos))
        # self.node().add_shape(shape, TransformState.make_pos(pos))


class TerrainCreator:

    def __init__(self, world):
        self.world = world
        # *************************************
        # self.terrains = NodePath('terrains')
        # self.terrains.reparent_to(base.render)
        # *************************************

        self.terrains = NodePath('terrains')
        self.terrain = CompoundTerrain()
        self.terrain.set_pos(Point3(0, 0, 0))
        self.terrain.reparent_to(self.terrains)
        self.terrains.reparent_to(base.render)
        self.world.attach(self.terrain.node())

        self.terrain_roots = []


    def make_terrain(self):
        # files = ['14516_6446.png', '14516_6447.png', '14517_6447.png', '14517_6446.png']
        # files = ['terrain1.png', 'terrain2.png', 'terrain3.png', 'terrain4.png']
        files = ['top_left.png', 'bottom_left.png', 'bottom_right.png', 'top_right.png']
        pos = [(-1, 1), (-1, -1), (1, -1), (1, 1)]

        for file, (x, y) in zip(files, pos):
            self.make_geomip_terrain(f'terrains/{file}', x, y)

        # for file in ['14516_6446.png']:  #, '14516_6447.png', '14517_6447.png', '14517_6446.png']:
        #     self.make_geomip_terrain(f'terrains/{file}')

    def make_geomip_terrain(self, img_file, x, y):
        height = 50
        # img_file = 'terrains/heightfield7.png'
        # img_file = 'terrains/heightfield6.png'
        height_size = PNMImage(Filename(img_file)).get_x_size()
        print('height_size', height_size)
        terrain = GeoMipTerrain('terrain')
        terrain.set_heightfield(img_file)

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
        pos = Point3(x * (height_size / 2 - 0.5), y * (height_size / 2 - 0.5), -(height / 2))
        root.set_pos(pos)
        # root.set_h(90)
        print('root', root.get_pos())

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
        img = PNMImage(Filename(img_file))
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

        # terrain.update()
        self.terrain_roots.append(root)





    # def make_geomip_terrain1(self, img_file, x, y):
    #     height = 20
    #     # img_file = 'terrains/heightfield7.png'
    #     # img_file = 'terrains/heightfield6.png'
    #     height_size = PNMImage(Filename(img_file)).get_x_size()

    #     terrain = GeoMipTerrain('terrain')
    #     terrain.set_heightfield(img_file)

    #     #************************
    #     terrain.set_border_stitching(True)
    #     # terrain.clear_color_map()
    #     terrain.set_block_size(8)  # block_size 8 and min 2, # block_size 16 and min 3 is good.
    #     terrain.set_min_level(2)
       
    #     # terrain.set_block_size(128)
    #     # terrain.set_near(0)
    #     # terrain.set_far(1024)
    #     # terrain.set_focal_point(base.camera)

    #     root = terrain.get_root()
    #     # root.reparent_to(self.terrains)
    #     root.reparent_to(base.render)
    #     root.set_scale(1, 1, height)
    #     # self.root.set_h(90)
    #     # root.set_two_sided(True) <- opposite side is textured too.

    #     # pos = Point3(-height_size / 2, -(height_size / 2), -height / 2)
    #     pos = Point3(x * (height_size / 2 - 0.5), y * (height_size / 2 - 0.5), -(height / 2))
    #     root.set_pos(pos)
    #     # root.set_h(90)
    #     print('root', root.get_pos())

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

    #     # self.terrain.add_terrain(img, height, pos)
    #     #********************************************
    #     shape = BulletHeightfieldShape(img, height, ZUp)
    #     shape.set_use_diamond_subdivision(True)


    #     np = self.terrains.attach_new_node(BulletRigidBodyNode('height_field'))
        
    #     # new_pos = Point3(pos.x + 128.5, pos.y + 128.5, 0)
    #     new_pos = Point3(pos.x + 128, pos.y + 128, 0)
    #     np.node().add_shape(shape, TransformState.make_pos(new_pos))
        
        
        
    #     # np.node().add_shape(shape)
    #     # np.set_pos(pos)
    #     print('np', np.get_pos())
    #     np.set_collide_mask(BitMask32.bit(1))
    #     self.world.attach(np.node())
    #     #********************************************

    #     terrain_shader = Shader.load(Shader.SL_GLSL, "shaders/terrain_v.glsl", "shaders/terrain_f.glsl")
    #     root.set_shader(terrain_shader)
    #     root.set_shader_input('camera', base.camera)

    #     root.set_shader_input('tex_ScaleFactor0', 10.0)
    #     root.set_shader_input('tex_ScaleFactor1', 10.0)
    #     root.set_shader_input('tex_ScaleFactor2', 10.0)
    #     root.set_shader_input('tex_ScaleFactor3', 10.0)

    #     terrain.update()

    def make_terrain2(self):
        self.height = 20
        img_file = 'terrains/heightfield7.png'
        # img_file = 'terrains/vconcat.png'
        self.height_size = PNMImage(Filename(img_file)).get_x_size()

        self.terrain = GeoMipTerrain('terrain')
        self.terrain.set_heightfield(img_file)

        self.terrain.set_block_size(128)
        self.terrain.set_near(0)
        self.terrain.set_far(1024)
        self.terrain.set_focal_point(base.camera)

        self.root = self.terrain.get_root()
        self.root.reparent_to(base.render)
        self.root.set_scale(1, 1, self.height)
        # self.root.set_h(90)
        self.root.set_pos(-self.height_size / 2, -(self.height_size / 2), -self.height / 2)

        ts = TextureStage('ts0')
        ts.set_sort(0)
        texture = base.loader.load_texture('textures/small_stones.jpg')
        self.root.set_texture(ts, texture)
        # self.root.set_tex_scale(ts, 300, 300)

        ts = TextureStage('ts1')
        ts.set_sort(1)
        texture = base.loader.load_texture('textures/grass.png')
        self.root.set_texture(ts, texture)
        # self.root.set_tex_scale(ts, 300, 300)

        ts = TextureStage('ts2')
        ts.set_sort(2)
        texture = base.loader.load_texture('textures/red_ground.jpg')
        self.root.set_texture(ts, texture)
        # self.root.set_tex_scale(ts, 300, 300)

        self.ts = TextureStage('ts3')
        self.ts.set_sort(3)
        self.texture = base.loader.load_texture('textures/dark_green.jpg')
        self.root.set_texture(self.ts, self.texture)
        # self.root.set_texture(self.ts, self.detail_map)
        # self.root.set_tex_scale(self.ts, 300, 300)

        
        self.terrain.generate()
        img = PNMImage(Filename(img_file))
        shape = BulletHeightfieldShape(img, self.height, ZUp)
        shape.set_use_diamond_subdivision(True)

        np = base.render.attach_new_node(BulletRigidBodyNode('height_field'))
        np.node().add_shape(shape)
        # np.set_pos(0, 0, self.height / 2)
        np.set_collide_mask(BitMask32.bit(1))
        self.world.attach(np.node())

        terrain_shader = Shader.load(Shader.SL_GLSL, "shaders/terrain_v_1.glsl", "shaders/terrain_f_1.glsl")
        self.root.set_shader(terrain_shader)
        self.root.set_shader_input('camera', base.camera)

        self.root.set_shader_input('tex_ScaleFactor0', 10.0)
        self.root.set_shader_input('tex_ScaleFactor1', 4.0)
        self.root.set_shader_input('tex_ScaleFactor2', 4.0)
        self.root.set_shader_input('tex_ScaleFactor3', 4.0)

    # def make_terrain(self):
    #     img_file = 'terrains/heightfield7.png'
    #     self.terrains = NodePath('root')
    #     self.terrains.reparent_to(self.render)

    #     img = PNMImage(Filename(img_file))
    #     terrain_np = NodePath(BulletRigidBodyNode('terrain_shape'))
    #     shape = BulletHeightfieldShape(img, 10, ZUp)
    #     terrain_np.node().add_shape(shape)
    #     terrain_np.node().set_mass(0)
    #     terrain_np.set_collide_mask(BitMask32.bit(1))
    #     terrain_np.reparent_to(self.terrains)
    #     self.world.attach(terrain_np.node())

    #     terrain_nd = ShaderTerrainMesh()
    #     heightfield = base.loader.load_texture(img_file)
    #     heightfield.wrap_u = SamplerState.WM_clamp
    #     heightfield.wrap_v = SamplerState.WM_clamp
    #     terrain_nd.heightfield = heightfield
    #     terrain_nd.target_triangle_width = 10.0
    #     terrain_nd.generate()

    #     tarrain = self.terrains.attach_new_node(terrain_nd)
    #     tarrain.set_scale(256, 256, 10)
    #     offset = img.get_x_size() / 2.0 - 0.5
    #     tarrain.set_pos(-offset, -offset, -10 / 2.0)

    #     terrain_shader = Shader.load(Shader.SL_GLSL, "shaders/terrain.vert.glsl", "shaders/terrain.frag.glsl")
    #     tarrain.set_shader(terrain_shader)
    #     tarrain.set_shader_input('camera', self.camera)

    #     grass_tex = self.loader.load_texture('textures/grass.png')
    #     grass_tex.setMinfilter(SamplerState.FT_linear_mipmap_linear)
    #     grass_tex.set_anisotropic_degree(16)
    #     tarrain.set_texture(grass_tex)



    