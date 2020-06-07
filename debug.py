import sys
import tempfile
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from Qt import QtWidgets, QtGui
from anytree import NodeMixin
from anytree.exporter import DotExporter

from src.view import NodeView

from IPython import embed


class MyNode(NodeMixin):
    def __init__(self, name, parent=None):
        self.name = str(name)
        self.parent = parent

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
        out_path = out_dir + f'/{self.name}.png'
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


class MyLabel(QtWidgets.QLabel):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.set_image()

    def set_image(self, *args):
        img = self.root.get_tree_image().convert('RGBA')
        self.setPixmap(QtGui.QPixmap.fromImage(ImageQt(img)))
        self.setFixedSize(*img.size)


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, root):
        super().__init__()
        self.setWindowTitle("Debug")

        view = NodeView(root)
        label = MyLabel(root)
        view.signal_Connected.connect(label.set_image)
        view.signal_Disconnected.connect(label.set_image)

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(view)
        layout.addWidget(label)
        widget.setLayout(layout)
        self.setCentralWidget(widget)


if __name__ == "__main__":
    root = MyNode(0)
    MyNode(1, root)
    MyNode(2, root)

    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow(root)
    window.show()

    sys.exit(app.exec_())
