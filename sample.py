import sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.bullet import BulletWorld, BulletDebugNode, BulletRigidBodyNode, BulletSphereShape
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

from walker import Walker
from terrain_creator import TerrainCreator


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Walking In BulletWorld
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class Sphere(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('sphere'))
        model = base.loader.load_model('models/sphere/sphere')
        model.reparent_to(self)
        model.set_scale(0.2)
        model.setColor(LColor(1, 0, 0, 1))
        shape = BulletSphereShape(0.8)
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_mass(1)
        self.reparent_to(base.render)


class Sample(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.world = BulletWorld()
        self.world.set_gravity(0, 0, -9.81)

        self.debug_np = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug_np.node())

        self.walker = Walker(self.world)
        self.floater = NodePath('floater')
        self.floater.set_z(3.0)
        self.floater.reparent_to(self.walker)

        self.camera.reparent_to(self.walker)
        self.camera.set_pos(self.walker.navigate())
        self.camera.look_at(self.floater)
        self.camLens.set_fov(90)

        # *****when debug***************
        # self.camera.set_pos(0, 0, 100)
        # self.camera.look_at(self.walker)
        # *****when debug***************

        # self.make_terrain()
        self.terrain_creator = TerrainCreator(self.world)
        self.terrain_creator.make_terrain()
        # terrain_creator.make_geomip_terrain()
        # self.render.setShaderAuto()

        self.sphere = Sphere()
        self.sphere.set_pos(0, 0, 20)
        self.world.attach(self.sphere.node())

        inputState.watch_with_modifiers('forward', 'arrow_up')
        inputState.watch_with_modifiers('backward', 'arrow_down')
        inputState.watch_with_modifiers('left', 'arrow_left')
        inputState.watch_with_modifiers('right', 'arrow_right')

        self.accept('d', self.toggle_debug)
        self.accept('p', self.print_position)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

    def print_position(self):
        print(self.walker.get_pos())

    def toggle_debug(self):
        if self.debug_np.is_hidden():
            self.debug_np.show()
        else:
            self.debug_np.hide()

    def update(self, task):
        # self.terrain.update()
        dt = globalClock.get_dt()
        self.control_walker(dt)

        # self.terrain_creator.terrains.set_z(self.terrain_creator.terrains.get_z() - 10 * dt)
        self.world.do_physics(dt)
        return task.cont

    def control_walker(self, dt):
        # contol walker movement
        direction = 0
        angle = 0

        if inputState.is_set('forward'):
            direction += -1
        if inputState.is_set('backward'):
            direction += 1
        if inputState.is_set('left'):
            angle += 100 * dt
        if inputState.is_set('right'):
            angle += -100 * dt

        self.walker.update(dt, direction, angle)

        # play animation
        anim = None
        rate = 1

        if inputState.is_set('forward'):
            anim = self.walker.RUN
        elif inputState.is_set('backward'):
            anim, rate = self.walker.WALK, -1
        elif inputState.is_set('left') or inputState.is_set('right'):
            anim = self.walker.WALK

        self.walker.play_anim(anim, rate)



if __name__ == '__main__':
    app = Sample()
    app.run()