import random

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point2, LColor

from goal_gate import GoalGate
from terrain_creator import Terrains
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

        self.ambient_light = BasicAmbientLight()
        self.ambient_light.reparent_to(self)
        self.directional_light = BasicDayLight()
        self.directional_light.reparent_to(self)

        self.sky = Sky()
        self.sky.reparent_to(self)

        self.terrains = Terrains(self.world)
        self.terrains.reparent_to(self)

        self.goal_gate = GoalGate(self.world)
        self.goal_gate.reparent_to(self)

        self.setup_scene()

    def setup_scene(self):
        pos, angle = self.decide_goal_pos()
        self.goal_gate.setup_gate(pos, angle)
        self.terrains.setup_nature()
        base.taskMgr.add(self.goal_gate.sensor.check_finish, 'check_finish')

    def cleanup_scene(self):
        self.terrains.natures.remove_from_terrain()
        self.goal_gate.cleanup_gate()

    def get_pos_on_terrain(self, x, y):
        ray_hit = self.terrains.check_position(x, y)
        pos = ray_hit.get_hit_pos()
        return pos

    def decide_goal_pos(self):
        candidates = [
            [Point2(230, 230), -45],
            [Point2(-230, -230), 135],
            [Point2(230, -230), -135],
            [Point2(-230, 230), 45],
        ]
        pt, angle = random.choice(candidates)
        pos = self.get_pos_on_terrain(*pt)
        return pos, angle

    def change_scene(self):
        self.terrains.replace_terrain()