from direct.gui.DirectGui import OnscreenText
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


class DrawText(OnscreenText):

    def __init__(self, parent, align, pos, fg, scale=0.1):
        font = base.loader.load_font('font/Candaral.ttf')
        self.text_root = parent

        super().__init__(
            text='',
            parent=parent,
            align=align,
            pos=pos,
            scale=scale,
            font=font,
            fg=fg,
            mayChange=True
        )