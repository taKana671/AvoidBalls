import os

import cv2
import numpy as np
from PIL import Image
from panda3d.core import LineSegs, NodePath


def create_line_node(from_pos, to_pos, color, thickness=2.0):
    """Return a NodePath for line node.
       Args:
            from_pos (Vec3): the point where a line starts;
            to_pos (Vec3): the point where a line ends;
            color (LColor): the line color;
            thickness (float): the line thickness;
    """
    lines = LineSegs()
    lines.set_color(color)
    lines.move_to(from_pos)
    lines.draw_to(to_pos)
    lines.set_thickness(thickness)
    node = lines.create()
    return NodePath(node)


def make_noise(x=256, y=256):
    # byte_arr = bytearray(os.urandom(x * y))
    # arr = np.array(byte_arr)
    # arr = arr.astype(np.uint16)
    # img = np.array(byte_arr).reshape(x, y)
    # cv2.imwrite('noise.png', img)

    byte_arr = bytearray(os.urandom(x * y))
    arr = np.array(byte_arr)
    arr = arr.reshape(x, y)
    img = Image.fromarray(np.uint8(arr))
    img.save('noise.png')


if __name__ == '__main__':
    make_noise()