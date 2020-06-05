import sys
import tempfile
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from Qt import QtWidgets, QtGui
from anytree.exporter import DotExporter

from src.node import BaseNode
from src.window import TreeEditWindow

from IPython import embed


class MyNode(BaseNode):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)

    @property
    def image(self):
        img = Image.new('RGBA', (5, 10), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text(
            (0, 0),  # Coordinates
            self.name,  # Text
            (0, 0, 0, 255)  # Color
        )
        return img

    def _node_attr(self, out_dir):
        out_path = out_dir + f'/{self.index}.png'
        self.image.save(out_path)

        attrs = {
            'label': '""',
            'shape': 'rect',
            'image': f'"{out_path}"',
            'imagescale': 'true',
            'fixedsize': 'true',
            'width': 1.2,
            'height': 0.9,
            'style': 'filled',
            'fillcolor': '"#F0F0F0"',
        }
        return ' '.join(
            f'{k}={v}' for k, v in attrs.items()
        )

    def get_tree_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = tmpdir + '/tree.png'
            DotExporter(self.root,
                        nodeattrfunc=lambda n: n._node_attr(tmpdir),
                        ).to_picture(out_path)
            with open(out_path, 'rb') as f:
                return Image.open(f).copy()


class OutputLabel(QtWidgets.QLabel):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.set_image()

    def set_image(self, *args):
        img = self.root.get_tree_image().convert('RGBA')
        self.setPixmap(QtGui.QPixmap.fromImage(ImageQt(img)))
        self.setFixedSize(*img.size)


if __name__ == "__main__":
    root = MyNode(0)
    MyNode(1, root)
    MyNode(2, root)

    app = QtWidgets.QApplication(sys.argv)

    window = TreeEditWindow(root)
    output = OutputLabel(root)
    window.set_update_func(output.set_image)

    window.show()
    output.show()

    sys.exit(app.exec_())
