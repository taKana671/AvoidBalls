import random
from enum import Enum, auto

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point2, LColor

from goal_gate import GoalGate
from lights import BasicAmbientLight, BasicDayLight
from terrain_creator import Terrains


class Status(Enum):

    COMPLETE = auto()
    CLEANUP = auto()
    SETUP = auto()
    CHANGE = auto()


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
        self.state = None
        self.terrain_center = None

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

    def setup_scene(self):
        pos, angle = self.decide_goal_pos()
        self.goal_gate.setup_gate(pos, angle)
        self.terrains.setup_nature()
        base.taskMgr.add(self.goal_gate.sensor.check_finish, 'check_finish')

    def cleanup_scene(self):
        self.terrains.natures.remove_from_terrain()
        self.goal_gate.cleanup_gate()

    def decide_goal_pos(self):
        candidates = [
            [Point2(230, 230), -45],
            [Point2(-230, -230), 135],
            [Point2(230, -230), -135],
            [Point2(-230, 230), 45],
        ]
        pt, angle = random.choice(candidates)
        pos = self.terrains.check_position(*pt, sweep=False)
        return pos, angle

    def update(self):

        match self.state:

            case Status.COMPLETE:
                self.state = Status.CLEANUP

            case Status.CLEANUP:
                self.cleanup_scene()
                self.state = Status.CHANGE

            case Status.CHANGE:
                self.terrains.replace_terrain()
                self.terrain_center = self.terrains.check_position(0, 0, sweep=False)
                self.state = Status.SETUP

            case Status.SETUP:
                self.setup_scene()
                self.state = Status.COMPLETE
                return True

            case _:
                self.state = Status.SETUP
