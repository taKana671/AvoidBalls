from panda3d.core import BitMask32


class ConstantsMeta(type):
    """Prohibit rebinding."""

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise TypeError(f'Cannot rebind ({name})')

            self.__setattr__(name, value)


class Config(metaclass=ConstantsMeta):

    angle = 100
    forward = -1
    backward = 1


class Mask(metaclass=ConstantsMeta):

    terrain = BitMask32.bit(1)
    nature = BitMask32.bit(2)
    ball = BitMask32.bit(3)
    sensor = BitMask32.bit(4)
    foundation = BitMask32.bit(5)
    almighty = BitMask32.all_on()

    environment = BitMask32.bit(1) | BitMask32.bit(2)


class FolderPath(metaclass=ConstantsMeta):

    terrains = 'terrains'