from Qt import QtCore, QtGui, QtWidgets
from .slot import SlotItem, ConnectionItem


class NodeItem(QtWidgets.QGraphicsItem):
    def __init__(self, view, data):
        super().__init__()

        self.setZValue(1)

        # Storage
        self.data = data
        self.slot_child = None
        self.slot_parent = None

        # Methods.
        self._createStyle(view.config)

        self.image = getattr(data, 'image', None)
        if self.image is not None:
            from PIL.ImageQt import ImageQt
            img_qt = ImageQt(self.image)
            self.image = QtGui.QPixmap.fromImage(img_qt)

        self.dialog = None
        if view.NodeDialog is not None:
            self.dialog = view.NodeDialog(data, parent=view)
            self.dialog.accepted.connect(view.signal_DialogAccepted)

    @property
    def name(self):
        return self.data.name

    @property
    def pen(self):
        if self.isSelected():
            return self._penSel
        else:
            return self._pen

    def _createStyle(self, config):
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        # Dimensions.
        self.baseWidth = config['node']['width']
        self.baseHeight = config['node']['height']
        self.border = config['node']['border']
        self.radius = config['node']['radius']

        self.height = (self.baseHeight +
                       self.border +
                       0.5 * self.radius)

        self.nodeCenter = QtCore.QPointF()
        self.nodeCenter.setX(self.baseWidth / 2.0)
        self.nodeCenter.setY(self.height / 2.0)

        self._brush = QtGui.QBrush()
        self._brush.setStyle(QtCore.Qt.SolidPattern)
        self._brush.setColor(QtGui.QColor(*config['node']['color']['main']))

        self._pen = QtGui.QPen()
        self._pen.setStyle(QtCore.Qt.SolidLine)
        self._pen.setWidth(self.border)
        self._pen.setColor(QtGui.QColor(*config['node']['color']['border']))

        self._penSel = QtGui.QPen()
        self._penSel.setStyle(QtCore.Qt.SolidLine)
        self._penSel.setWidth(self.border)
        self._penSel.setColor(
            QtGui.QColor(*config['node']['color']['border_sel'])
        )

        self._textPen = QtGui.QPen()
        self._textPen.setStyle(QtCore.Qt.SolidLine)
        self._textPen.setColor(QtGui.QColor(*config['text_color']))

        self._rootTextFont = QtGui.QFont(
            config['font'],
            config['root_font_size'],
            QtGui.QFont.Bold
        )
        self._nodeTextFont = QtGui.QFont(
            config['font'],
            config['node_font_size'],
            QtGui.QFont.Bold
        )

    def _createSlot(self, slot_parent=True, slot_child=True):
        if slot_parent:
            self.slot_parent = SlotItem(parent=self, slot_type='parent')

        if slot_child:
            self.slot_child = SlotItem(parent=self, slot_type='child')

    def _remove(self):
        self.scene().nodes.pop(id(self.data))

        # Remove all parent connections.
        if self.slot_parent is not None:
            connections = self.slot_parent.connections
            while len(connections) > 0:
                connections[0]._remove()

        # Remove all child connections.
        if self.slot_child is not None:
            connections = self.slot_child.connections
            while len(connections) > 0:
                connections[0]._remove()

        # Remove node.
        scene = self.scene()
        scene.removeItem(self)
        scene.update()

    def boundingRect(self):
        rect = QtCore.QRect(0, 0, self.baseWidth, self.height)
        rect = QtCore.QRectF(rect)
        return rect

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget):
        # Node base.
        painter.setBrush(self._brush)
        painter.setPen(self.pen)

        painter.drawRoundedRect(0, 0,
                                self.baseWidth,
                                self.height,
                                self.radius,
                                self.radius)

        # Root label
        if self.scene().root == self.data:
            label = 'Root'
            painter.setPen(self._textPen)
            painter.setFont(self._rootTextFont)

            metrics = QtGui.QFontMetrics(painter.font())
            text_width = metrics.boundingRect(label).width() + 14
            text_height = metrics.boundingRect(label).height() + 32
            margin = (self.baseWidth - text_width) * 0.5
            textRect = QtCore.QRect(margin,
                                    -text_height,
                                    text_width,
                                    text_height)

            painter.drawText(textRect,
                             QtCore.Qt.AlignCenter,
                             label)

        if self.image is None:
            painter.setPen(self._textPen)
            painter.setFont(self._nodeTextFont)

            metrics = QtGui.QFontMetrics(painter.font())
            rect = metrics.boundingRect(self.name)
            text_width = rect.width() + 14
            text_height = rect.height() + 14
            x = (self.baseWidth - text_width) * 0.5
            y = (self.height - text_height) * 0.5
            textRect = QtCore.QRect(x, y,
                                    text_width,
                                    text_height)

            painter.drawText(textRect,
                             QtCore.Qt.AlignCenter,
                             self.name)
        else:
            img = self.image.scaled(self.baseWidth - self.border * 2,
                                    self.height - self.border * 2, QtCore.Qt.KeepAspectRatio)
            x = (self.baseWidth - img.width()) / 2
            y = (self.height - img.height()) / 2
            painter.drawPixmap(x, y, img)

    def mousePressEvent(self, event):
        nodes = self.scene().nodes
        for node in nodes.values():
            node.setZValue(1)

        for item in self.scene().items():
            if isinstance(item, ConnectionItem):
                item.setZValue(1)

        self.setZValue(2)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.dialog is not None:
            self.dialog.exec_()
        super().mouseDoubleClickEvent(event)
        self.scene().parent().signal_NodeDoubleClicked.emit(self.name)

    def mouseMoveEvent(self, event):
        self.scene().updateScene()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.scene().signal_NodeMoved.emit(self.name, self.pos())
        super().mouseReleaseEvent(event)

    def hoverLeaveEvent(self, event):
        view = self.scene().views()[0]

        for item in view.scene().items():
            if isinstance(item, ConnectionItem):
                item.setZValue(0)

        super().hoverLeaveEvent(event)
