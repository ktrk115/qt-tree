import json
import tempfile
import subprocess
from Qt import QtCore, QtGui, QtWidgets
from anytree import NodeMixin
from anytree.exporter import DotExporter
from .slot import ConnectionItem


class NodeScene(QtWidgets.QGraphicsScene):
    signal_NodeMoved = QtCore.Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = dict()

    def drawBackground(self, painter, rect):
        config = self.parent().config
        self._brush = QtGui.QBrush()
        self._brush.setStyle(QtCore.Qt.SolidPattern)
        self._brush.setColor(QtGui.QColor(*config['bg_color']))
        painter.fillRect(rect, self._brush)

    def updateScene(self):
        for item in self.items():
            if isinstance(item, ConnectionItem):
                item.target_point = item.target.center()
                item.source_point = item.source.center()
                item.updatePath()

    def setNodes(self, root):
        assert isinstance(root, NodeMixin)

        self.root = root
        view = self.views()[0]
        nodes = [root] + list(root.descendants)
        for n_data in nodes:
            image = getattr(n_data, 'image')
            view.createNode(n_data, pil_image=image)

        for n_data in nodes:
            if not n_data.is_root:
                view.createConnection(n_data.parent, n_data)

        self.setFormalPosition()

    def setFormalPosition(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = tmpdir + '/tree.dot'
            DotExporter(self.root,
                        nodenamefunc=lambda n: id(n),
                        ).to_dotfile(out_path)
            cmd = f'dot {out_path} -T json0'.split()
            res = subprocess.run(cmd, capture_output=True)

        objects = json.loads(res.stdout.decode())['objects']
        y_max = max([float(obj['pos'].split(',')[1]) for obj in objects])
        for obj in objects:
            pos = obj['pos'].split(',')
            x = float(pos[0]) * 5 + 1e+3
            y = (y_max - float(pos[1])) * 5 + 1e+3
            nodeItem = self.nodes[int(obj['name'])]
            position = QtCore.QPointF(x, y)
            nodeItem.setPos(position - nodeItem.nodeCenter)

            connections = nodeItem.slot_parent.connections.copy()
            connections += nodeItem.slot_child.connections
            for connection in connections:
                slot = connection.childSlotItem
                connection.source_point = slot.center()
                slot = connection.parentSlotItem
                connection.target_point = slot.center()
                connection.updatePath()
