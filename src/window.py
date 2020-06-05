from Qt import QtWidgets
from .base_node import BaseNode
from .view import NodeView


class TreeEditWindow(QtWidgets.QMainWindow):
    def __init__(self, root):
        assert isinstance(root, BaseNode)

        super(TreeEditWindow, self).__init__()
        view = NodeView(None)
        view.initialize()
        root.set_view(view)

        view.signal_Connected.connect(self.__call_connected_funcs)

        self.root = root
        self.view = view
        self.setCentralWidget(view)
        self.connected_funcs = []

    def set_connected_func(self, func):
        if func not in self.connected_funcs:
            self.connected_funcs.append(func)

    def __call_connected_funcs(self, parent_index, child_index):
        if parent_index is not None and child_index is not None:
            parent = self.root.idx2node[parent_index]
            child = self.root.idx2node[child_index]
            child.parent = parent
            for func in self.connected_funcs:
                func(parent_index, child_index)

    def show(self):
        super().show()
        self.view._focus()
