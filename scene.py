from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, LColor

from terrain_creator import TerrainRoot
from lights import BasicAmbientLight, BasicDayLight


class Sky(NodePath):

    def __init__(self):
        super().__init__(PandaNode('sky'))
        model = base.loader.load_model('models/blue-sky/blue-sky-sphere')
        model.set_color(LColor(2, 2, 2, 1))
        model.set_scale(0.2)
        model.set_z(0)
        model.reparent_to(self)
        self.set_shader_off()


class Scene(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('scene'))
        self.world = world
        self.setup_lights()
        self.sky = Sky()
        self.sky.reparent_to(self)

        self.terrain_root = TerrainRoot(self.world)
        # self.terrain_root.create_3d_terrain()
        self.terrain_root.reparent_to(self)

    def setup_lights(self):
        self.ambient_light = BasicAmbientLight()
        self.ambient_light.reparent_to(self)
        self.directional_light = BasicDayLight()
        self.directional_light.reparent_to(self)
