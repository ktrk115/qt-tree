
from Qt import QtCore, QtGui, QtWidgets
from .slot import ConnectionItem


class NodeScene(QtWidgets.QGraphicsScene):

    """
    The scene displaying all the nodes.

    """
    signal_NodeMoved = QtCore.Signal(str, object)

    def __init__(self, parent):
        """
        Initialize the class.

        """
        super(NodeScene, self).__init__(parent)

        # General.
        self.gridSize = parent.config['grid_size']

        # Nodes storage.
        self.nodes = dict()

    def dragEnterEvent(self, event):
        """
        Make the dragging of nodes into the scene possible.

        """
        event.setDropAction(QtCore.Qt.MoveAction)
        event.accept()

    def dragMoveEvent(self, event):
        """
        Make the dragging of nodes into the scene possible.

        """
        event.setDropAction(QtCore.Qt.MoveAction)
        event.accept()

    def dropEvent(self, event):
        """
        Create a node from the dropped item.

        """
        # Emit signal.
        self.signal_Dropped.emit(event.scenePos())

        event.accept()

    def drawBackground(self, painter, rect):
        """
        Draw a grid in the background.

        """
        config = self.parent().config

        self._brush = QtGui.QBrush()
        self._brush.setStyle(QtCore.Qt.SolidPattern)
        self._brush.setColor(QtGui.QColor(*config['bg_color']))

        painter.fillRect(rect, self._brush)

        if self.views()[0].gridVisToggle:
            leftLine = rect.left() - rect.left() % self.gridSize
            topLine = rect.top() - rect.top() % self.gridSize
            lines = list()

            i = int(leftLine)
            while i < int(rect.right()):
                lines.append(QtCore.QLineF(i, rect.top(), i, rect.bottom()))
                i += self.gridSize

            u = int(topLine)
            while u < int(rect.bottom()):
                lines.append(QtCore.QLineF(rect.left(), u, rect.right(), u))
                u += self.gridSize

            self.pen = QtGui.QPen()
            self.pen.setColor(QtGui.QColor(*config['grid_color']))
            self.pen.setWidth(0)
            painter.setPen(self.pen)
            painter.drawLines(lines)

    def updateScene(self):
        """
        Update the connections position.

        """
        for connection in [i for i in self.items() if isinstance(i, ConnectionItem)]:
            connection.target_point = connection.target.center()
            connection.source_point = connection.source.center()
            connection.updatePath()
