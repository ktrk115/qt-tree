from Qt import QtCore, QtGui, QtWidgets
from .slot import SlotItem, ConnectionItem


class NodeItem(QtWidgets.QGraphicsItem):
    def __init__(self, data, config, pil_image):
        super().__init__()

        self.setZValue(1)

        # Storage
        self.data = data

        # Attributes storage.
        self.attrCount = 1

        self.slot_child = None
        self.slot_parent = None

        # Methods.
        self._createStyle(config)

        self.image = None
        if pil_image is not None:
            from PIL.ImageQt import ImageQt
            self.image = QtGui.QPixmap.fromImage(ImageQt(pil_image))

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
        self.baseWidth = config['node_width']
        self.baseHeight = config['node_height']
        self.attrHeight = config['node_attr_height']
        self.border = config['node_border']
        self.radius = config['node_radius']

        self.height = (self.baseHeight +
                       self.attrHeight * self.attrCount +
                       self.border +
                       0.5 * self.radius)

        self.nodeCenter = QtCore.QPointF()
        self.nodeCenter.setX(self.baseWidth / 2.0)
        self.nodeCenter.setY(self.height / 2.0)

        self._brush = QtGui.QBrush()
        self._brush.setStyle(QtCore.Qt.SolidPattern)
        self._brush.setColor(QtGui.QColor(*config['node']['bg']))

        self._pen = QtGui.QPen()
        self._pen.setStyle(QtCore.Qt.SolidLine)
        self._pen.setWidth(self.border)
        self._pen.setColor(QtGui.QColor(*config['node']['border']))

        self._penSel = QtGui.QPen()
        self._penSel.setStyle(QtCore.Qt.SolidLine)
        self._penSel.setWidth(self.border)
        self._penSel.setColor(QtGui.QColor(
            *config['node']['border_sel']))

        self._textPen = QtGui.QPen()
        self._textPen.setStyle(QtCore.Qt.SolidLine)
        self._textPen.setColor(QtGui.QColor(*config['node']['text']))

        self._nodeTextFont = QtGui.QFont(
            config['node_font'], config['node_font_size'], QtGui.QFont.Bold)
        self._attrTextFont = QtGui.QFont(
            config['attr_font'], config['attr_font_size'], QtGui.QFont.Normal)

        self._attrBrush = QtGui.QBrush()
        self._attrBrush.setStyle(QtCore.Qt.SolidPattern)

        self._attrBrushAlt = QtGui.QBrush()
        self._attrBrushAlt.setStyle(QtCore.Qt.SolidPattern)

        self._attrPen = QtGui.QPen()
        self._attrPen.setStyle(QtCore.Qt.SolidLine)

    def _createAttribute(self, slot_parent, slot_child):
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

        # Node label.
        painter.setPen(self._textPen)
        painter.setFont(self._nodeTextFont)

        metrics = QtGui.QFontMetrics(painter.font())
        text_width = metrics.boundingRect(self.name).width() + 14
        text_height = metrics.boundingRect(self.name).height() + 14
        margin = (text_width - self.baseWidth) * 0.5
        textRect = QtCore.QRect(-margin,
                                -text_height,
                                text_width,
                                text_height)

        painter.drawText(textRect,
                         QtCore.Qt.AlignCenter,
                         self.name)

        # Attributes.
        offset = 0
        view = self.scene().views()[0]
        config = view.config

        # Attribute rect.
        rect = QtCore.QRect(self.border / 2,
                            self.baseHeight - self.radius + offset,
                            self.baseWidth - self.border,
                            self.attrHeight)

        # Attribute base.
        self._attrBrush.setColor(QtGui.QColor(*config['attr']['bg']))

        self._attrPen.setColor(QtGui.QColor(0, 0, 0, 0))
        painter.setPen(self._attrPen)
        painter.setBrush(self._attrBrush)
        if (offset / self.attrHeight) % 2:
            painter.setBrush(self._attrBrushAlt)

        painter.drawRect(rect)

        # Attribute label.
        painter.setPen(QtGui.QColor(*config['attr']['text']))
        painter.setFont(self._attrTextFont)

        # Search non-connectable attributes.
        if view.drawingConnection:
            if self == view.currentHoveredNode:
                if view.sourceSlot.slotType == 'child' and self.slot_parent is None or \
                        view.sourceSlot.slotType == 'parent' and self.slot_child is None:
                    # Set non-connectable attributes color.
                    painter.setPen(QtGui.QColor(
                        *config['non_connectable_color']))

        textRect = QtCore.QRect(rect.left() + self.radius,
                                rect.top(),
                                rect.width() - 2 * self.radius,
                                rect.height())

        if self.image is not None:
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
