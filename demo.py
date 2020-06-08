import sys
import tempfile
from PIL import Image
from PIL.ImageQt import ImageQt
from Qt import QtWidgets, QtGui
from anytree import NodeMixin
from anytree.exporter import UniqueDotExporter

from src.view import NodeView

from IPython import embed


class MyNode(NodeMixin):
    shapes = ['rect', 'circle', 'diamond', 'star', 'box3d']

    def __init__(self, name, parent=None):
        self.name = str(name)
        self.parent = parent
        self.shape = 'rect'
        self.bold = False

    def _node_attr(self, out_dir):
        attrs = {
            'label': self.name,
            'shape': self.shape,
        }
        if self.bold:
            attrs['style'] = 'bold'
        return ' '.join(
            f'{k}={v}' for k, v in attrs.items()
        )

    def get_tree_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = tmpdir + '/tree.png'
            UniqueDotExporter(self.root,
                              nodeattrfunc=lambda n: n._node_attr(tmpdir),
                              ).to_picture(out_path)
            with open(out_path, 'rb') as f:
                return Image.open(f).copy()


class MyDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent=parent)
        self.data = data

        layout = QtWidgets.QFormLayout()

        self.form_name = QtWidgets.QLineEdit()
        self.form_name.setText(data.name)
        layout.addRow(QtWidgets.QLabel("Name:"), self.form_name)

        self.form_shape = QtWidgets.QComboBox()
        self.form_shape.addItems(MyNode.shapes)
        layout.addRow(QtWidgets.QLabel("Shape:"), self.form_shape)

        self.form_bold = QtWidgets.QCheckBox()
        self.form_bold.setChecked(data.bold)
        self.form_bold.setText('Set bold border')
        layout.addWidget(self.form_bold)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def accept(self):
        newName = self.form_name.text()
        if newName:
            self.data.name = newName

        newShape = self.form_shape.currentText()
        self.data.shape = newShape

        newBold = self.form_bold.isChecked()
        self.data.bold = newBold

        super().accept()


class MyLabel(QtWidgets.QLabel):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.set_image()

    def set_image(self, *args):
        root = self.scene.root
        img = root.get_tree_image().convert('RGBA')
        self.setPixmap(QtGui.QPixmap.fromImage(ImageQt(img)))
        self.setFixedSize(*img.size)


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, root):
        super().__init__()
        self.setWindowTitle("Debug")

        view = NodeView(root, MyDialog)
        label = MyLabel(view.scene())
        view.signal_RootUpdated.connect(label.set_image)
        view.signal_Connected.connect(label.set_image)
        view.signal_Disconnected.connect(label.set_image)
        view.signal_DialogAccepted.connect(label.set_image)

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
