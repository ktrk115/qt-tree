import sys
from pathlib import Path
from Qt import QtWidgets
from .node import BaseNode

path = Path(__file__).with_name('Nodz')
sys.path.append(str(path))
import nodz_main


class TreeEditWindow(QtWidgets.QMainWindow):
    def __init__(self, root):
        assert isinstance(root, BaseNode)

        super(TreeEditWindow, self).__init__()
        nodz = nodz_main.Nodz(None)
        nodz.initialize()
        root.set_nodz(nodz)

        nodz.signal_PlugConnected.connect(self.__call_update_funcs)
        nodz.signal_SocketConnected.connect(self.__call_update_funcs)

        self.root = root
        self.nodz = nodz
        self.setCentralWidget(nodz)
        self.update_funcs = []

    def set_update_func(self, func):
        if func not in self.update_funcs:
            self.update_funcs.append(func)

    def __call_update_funcs(self, parent_index, _, child_index, __):
        if parent_index is not None and child_index is not None:
            parent = self.root.idx2node[parent_index]
            child = self.root.idx2node[child_index]
            child.parent = parent
            for func in self.update_funcs:
                func(parent_index, child_index)

    def show(self):
        super().show()
        self.nodz._focus()
