from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, LColor

from goal_gate import GoalGate

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

        self.terrains = TerrainRoot(self.world)
        self.terrains.reparent_to(self)

        self.goal_gate = GoalGate(self.world, Point3(0, 0, -13), 30)
        self.goal_gate.reparent_to(self)
        # base.taskMgr.add(self.goal.sensor.sense, 'check_goal')
        # base.taskMgr.add(self.goal.check_finish, 'check_finish')

    def setup_lights(self):
        self.ambient_light = BasicAmbientLight()
        self.ambient_light.reparent_to(self)
        self.directional_light = BasicDayLight()
        self.directional_light.reparent_to(self)
