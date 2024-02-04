import random
from enum import Enum, auto

from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Point3, Point2, LColor

from goal_gate import GoalGate
from terrain_creator import Terrains
from lights import BasicAmbientLight, BasicDayLight


class Status(Enum):

    REPLACE = auto()
    SETUP = auto()
    ARRANGED = auto()


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

        self.terrains = Terrains(self.world)
        self.terrains.reparent_to(self)
        self.setup_goal_gate()
        self.terrains.setup_nature()

    def setup_lights(self):
        self.ambient_light = BasicAmbientLight()
        self.ambient_light.reparent_to(self)
        self.directional_light = BasicDayLight()
        self.directional_light.reparent_to(self)

    def get_pos_on_terrain(self, x, y):
        ray_hit = self.terrains.check_position(x, y)
        pos = ray_hit.get_hit_pos()
        return pos

    def setup_goal_gate(self):
        candidates = [
            [Point2(230, 230), -45],
            [Point2(-230, -230), 135],
            [Point2(230, -230), -135],
            [Point2(-230, 230), 45],
        ]
        candidate = random.choice(candidates)
        pt, angle = candidate
        print('goal_gate', pt, angle)
        ray_hit = self.terrains.check_position(*pt)
        pos = ray_hit.get_hit_pos()
        self.goal_gate = GoalGate(self.world, pos, angle)
        self.goal_gate.reparent_to(self)

    def clean_up(self):
        self.terrains.cleanup_nature()
        self.goal_gate.detach_node()

    def update(self):
        for bullet_terrain in self.terrains.bullet_terrains:
            bullet_terrain.terrain.update()


    def change_terrains(self):
        # folder = self.tile_folders.pop(0)
        # HeightfieldCreator().concat_from_files(folder.name)
        self.terrains.replace_terrain()
        # self.tile_folders.append(folder)
