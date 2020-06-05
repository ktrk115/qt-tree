import json
import tempfile
import subprocess
from Qt import QtCore
from anytree import NodeMixin
from anytree.exporter import DotExporter


class BaseNode(NodeMixin):
    index = 0

    def __init__(self, name, parent=None):
        self.name = str(name)
        self.parent = parent
        self.index = str(BaseNode.index)
        BaseNode.index += 1

    @property
    def image(self):
        return None

    def set_idx2node(self):
        idx2node = dict()
        nodes = [self.root] + list(self.root.descendants)
        for n in nodes:
            idx2node[n.index] = n
        self.root.idx2node = idx2node

    def set_formal_position(self):
        self.set_idx2node()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = tmpdir + '/tree.dot'
            DotExporter(self.root,
                        nodenamefunc=lambda n: n.index
                        ).to_dotfile(out_path)
            cmd = f'dot {out_path} -T json0'.split()
            res = subprocess.run(cmd, capture_output=True)

        objects = json.loads(res.stdout.decode())['objects']
        y_max = max([float(obj['pos'].split(',')[1]) for obj in objects])
        for obj in objects:
            pos = obj['pos'].split(',')
            x = float(pos[0]) * 5 + 1e+3
            y = (y_max - float(pos[1])) * 5 + 1e+3
            qt_pos = QtCore.QPointF(x, y)
            self.root.idx2node[obj['name']].qt_pos = qt_pos

    def set_view(self, view):
        self.set_formal_position()

        root = self.root
        nodes = [root] + list(root.descendants)
        for n in nodes:
            n_view = view.createNode(name=n.index,
                                     position=n.qt_pos, pil_image=n.image)
            if n.is_root:
                view.createAttribute(n_view, slot_parent=False)
            else:
                view.createAttribute(n_view)
                view.createConnection(n.parent.index, n.index)
