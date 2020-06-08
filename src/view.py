import json
from pathlib import Path
from anytree import NodeMixin
from Qt import QtGui, QtCore, QtWidgets
from .scene import NodeScene
from .node import NodeItem
from .slot import ConnectionItem

defaultConfigPath = Path(__file__).with_name('default_config.json')


class NodeView(QtWidgets.QGraphicsView):
    signal_NodeCreated = QtCore.Signal(object)
    signal_NodeDeleted = QtCore.Signal(object)
    signal_NodeSelected = QtCore.Signal(object)
    signal_NodeMoved = QtCore.Signal(str, object)
    signal_NodeDoubleClicked = QtCore.Signal(str)

    signal_RootUpdated = QtCore.Signal(object)
    signal_Connected = QtCore.Signal(object, object)
    signal_Disconnected = QtCore.Signal(object, object)
    signal_DialogAccepted = QtCore.Signal()

    signal_KeyPressed = QtCore.Signal(object)
    signal_Dropped = QtCore.Signal()

    def __init__(self, root, NodeDialog=None, parent=None,
                 configPath=defaultConfigPath):
        super().__init__(parent)

        # Load configuration.
        self.loadConfig(configPath)
        self.NodeDialog = NodeDialog

        # General data.
        self.selectedNodes = None

        # Connections data.
        self.drawingConnection = False
        self.currentHoveredNode = None
        self.sourceSlot = None

        # Display options.
        self.currentState = 'DEFAULT'
        self.pressedKeys = list()

        self.initialize(root)
        self._focus()

    def wheelEvent(self, event):
        self.currentState = 'ZOOM_VIEW'
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        inFactor = 1.15
        outFactor = 1 / inFactor

        if event.delta() > 0:
            zoomFactor = inFactor
        else:
            zoomFactor = outFactor

        self.scale(zoomFactor, zoomFactor)
        self.currentState = 'DEFAULT'

    def mousePressEvent(self, event):
        # Tablet zoom
        if (event.button() == QtCore.Qt.RightButton and
                event.modifiers() == QtCore.Qt.AltModifier):
            self.currentState = 'ZOOM_VIEW'
            self.initMousePos = event.pos()
            self.zoomInitialPos = event.pos()
            self.initMouse = QtGui.QCursor.pos()
            self.setInteractive(False)

        # Drag view
        elif (event.button() == QtCore.Qt.MiddleButton and
              event.modifiers() == QtCore.Qt.AltModifier):
            self.currentState = 'DRAG_VIEW'
            self.prevPos = event.pos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self.setInteractive(False)

        # Rubber band selection
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.NoModifier and
              self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is None):
            self.currentState = 'SELECTION'
            self._initRubberband(event.pos())
            self.setInteractive(False)

        # Drag Item
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.NoModifier and
              self.scene().itemAt(self.mapToScene(event.pos()), QtGui.QTransform()) is not None):
            self.currentState = 'DRAG_ITEM'
            self.setInteractive(True)

        # Add selection
        elif (event.button() == QtCore.Qt.LeftButton and
              QtCore.Qt.Key_Shift in self.pressedKeys and
              QtCore.Qt.Key_Control in self.pressedKeys):
            self.currentState = 'ADD_SELECTION'
            self._initRubberband(event.pos())
            self.setInteractive(False)

        # Subtract selection
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.ControlModifier):
            self.currentState = 'SUBTRACT_SELECTION'
            self._initRubberband(event.pos())
            self.setInteractive(False)

        # Toggle selection
        elif (event.button() == QtCore.Qt.LeftButton and
              event.modifiers() == QtCore.Qt.ShiftModifier):
            self.currentState = 'TOGGLE_SELECTION'
            self._initRubberband(event.pos())
            self.setInteractive(False)

        else:
            self.currentState = 'DEFAULT'

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Zoom.
        if self.currentState == 'ZOOM_VIEW':
            offset = self.zoomInitialPos.x() - event.pos().x()

            if offset > self.previousMouseOffset:
                self.previousMouseOffset = offset
                self.zoomDirection = -1
                self.zoomIncr -= 1

            elif offset == self.previousMouseOffset:
                self.previousMouseOffset = offset
                if self.zoomDirection == -1:
                    self.zoomDirection = -1
                else:
                    self.zoomDirection = 1

            else:
                self.previousMouseOffset = offset
                self.zoomDirection = 1
                self.zoomIncr += 1

            if self.zoomDirection == 1:
                zoomFactor = 1.03
            else:
                zoomFactor = 1 / 1.03

            # Perform zoom and re-center on initial click position.
            pBefore = self.mapToScene(self.initMousePos)
            self.setTransformationAnchor(
                QtWidgets.QGraphicsView.AnchorViewCenter)
            self.scale(zoomFactor, zoomFactor)
            pAfter = self.mapToScene(self.initMousePos)
            diff = pAfter - pBefore

            self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
            self.translate(diff.x(), diff.y())

        # Drag canvas.
        elif self.currentState == 'DRAG_VIEW':
            offset = self.prevPos - event.pos()
            self.prevPos = event.pos()
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() + offset.x())

        # RuberBand selection.
        elif (self.currentState == 'SELECTION' or
              self.currentState == 'ADD_SELECTION' or
              self.currentState == 'SUBTRACT_SELECTION' or
              self.currentState == 'TOGGLE_SELECTION'):
            self.rubberband.setGeometry(QtCore.QRect(
                self.origin, event.pos()).normalized())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Zoom the View.
        if self.currentState == '.ZOOM_VIEW':
            self.offset = 0
            self.zoomDirection = 0
            self.zoomIncr = 0
            self.setInteractive(True)

        # Drag View.
        elif self.currentState == 'DRAG_VIEW':
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.setInteractive(True)

        # Selection.
        elif self.currentState == 'SELECTION':
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberband()
            self.setInteractive(True)
            self.scene().setSelectionArea(painterPath)

        # Add Selection.
        elif self.currentState == 'ADD_SELECTION':
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberband()
            self.setInteractive(True)
            for item in self.scene().items(painterPath):
                item.setSelected(True)

        # Subtract Selection.
        elif self.currentState == 'SUBTRACT_SELECTION':
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberband()
            self.setInteractive(True)
            for item in self.scene().items(painterPath):
                item.setSelected(False)

        # Toggle Selection
        elif self.currentState == 'TOGGLE_SELECTION':
            self.rubberband.setGeometry(QtCore.QRect(self.origin,
                                                     event.pos()).normalized())
            painterPath = self._releaseRubberband()
            self.setInteractive(True)
            for item in self.scene().items(painterPath):
                if item.isSelected():
                    item.setSelected(False)
                else:
                    item.setSelected(True)

        self.currentState = 'DEFAULT'

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        scene = self.scene()

        if event.key() not in self.pressedKeys:
            self.pressedKeys.append(event.key())

        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self._deleteSelectedNodes()

        if event.key() == QtCore.Qt.Key_F:
            if event.modifiers() == QtCore.Qt.ShiftModifier:
                scene.setFormalPosition()
                scene.clearSelection()
            self._focus()

        items = scene.selectedItems()
        if items and (event.key() == QtCore.Qt.Key_R):
            for item in items:
                if isinstance(item, NodeItem):
                    self.setNodeAsRoot(item)

        # Emit signal.
        self.signal_KeyPressed.emit(event.key())

    def keyReleaseEvent(self, event):
        if event.key() in self.pressedKeys:
            self.pressedKeys.remove(event.key())

    def setNodeAsRoot(self, node):
        self.scene().root = node.data
        for connection in node.slot_parent.connections:
            connection._remove()
        node.update()

        # Emit signal
        self.signal_RootUpdated.emit(node)

    def _initRubberband(self, position):
        self.rubberBandStart = position
        self.origin = position
        self.rubberband.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
        self.rubberband.show()

    def _releaseRubberband(self):
        painterPath = QtGui.QPainterPath()
        rect = self.mapToScene(self.rubberband.geometry())
        painterPath.addPolygon(rect)
        self.rubberband.hide()
        return painterPath

    def _focus(self, padding=50):
        if self.scene().selectedItems():
            itemsArea = self._getSelectionBoundingbox()
            self.fitInView(itemsArea, QtCore.Qt.KeepAspectRatio)
        else:
            itemsArea = self.scene().itemsBoundingRect()
            itemsArea.setX(itemsArea.x() - padding)
            itemsArea.setY(itemsArea.y() - padding -
                           self.config['root_font_size'])
            itemsArea.setWidth(itemsArea.width() + padding)
            itemsArea.setHeight(itemsArea.height() + padding)
            self.fitInView(itemsArea, QtCore.Qt.KeepAspectRatio)

    def _getSelectionBoundingbox(self):
        bbx_min = None
        bbx_max = None
        bby_min = None
        bby_max = None
        bbw = 0
        bbh = 0
        for item in self.scene().selectedItems():
            pos = item.scenePos()
            x = pos.x()
            y = pos.y()
            w = x + item.boundingRect().width()
            h = y + item.boundingRect().height()

            # bbx min
            if bbx_min is None:
                bbx_min = x
            elif x < bbx_min:
                bbx_min = x
            # end if

            # bbx max
            if bbx_max is None:
                bbx_max = w
            elif w > bbx_max:
                bbx_max = w
            # end if

            # bby min
            if bby_min is None:
                bby_min = y
            elif y < bby_min:
                bby_min = y
            # end if

            # bby max
            if bby_max is None:
                bby_max = h
            elif h > bby_max:
                bby_max = h
            # end if
        # end if
        bbw = bbx_max - bbx_min
        bbh = bby_max - bby_min
        return QtCore.QRectF(QtCore.QRect(bbx_min, bby_min, bbw, bbh))

    def _deleteSelectedNodes(self):
        selected_nodes = list()
        for node in self.scene().selectedItems():
            selected_nodes.append(node.name)
            node._remove()

        # Emit signal.
        self.signal_NodeDeleted.emit(selected_nodes)

    def _returnSelection(self):
        selected_nodes = list()
        if self.scene().selectedItems():
            for node in self.scene().selectedItems():
                selected_nodes.append(node.name)

        # Emit signal.
        self.signal_NodeSelected.emit(selected_nodes)

    def loadConfig(self, filePath):
        with filePath.open() as f:
            self.config = json.load(f)

    def initialize(self, root=None):
        # Setup view.
        config = self.config
        self.setRenderHint(
            QtGui.QPainter.Antialiasing,
            config['antialiasing']
        )
        self.setRenderHint(
            QtGui.QPainter.TextAntialiasing,
            config['antialiasing']
        )
        self.setRenderHint(
            QtGui.QPainter.HighQualityAntialiasing,
            config['antialiasing_boost']
        )
        self.setRenderHint(
            QtGui.QPainter.SmoothPixmapTransform,
            config['smooth_pixmap']
        )
        self.setRenderHint(QtGui.QPainter.NonCosmeticDefaultPen, True)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.rubberband = QtWidgets.QRubberBand(
            QtWidgets.QRubberBand.Rectangle,
            self
        )

        # Setup scene.
        scene = NodeScene(self)
        sceneWidth = config['scene_width']
        sceneHeight = config['scene_height']
        scene.setSceneRect(0, 0, sceneWidth, sceneHeight)
        self.setScene(scene)
        scene.setNodes(root)

        # Tablet zoom.
        self.previousMouseOffset = 0
        self.zoomDirection = 0
        self.zoomIncr = 0

        # Connect signals.
        self.scene().selectionChanged.connect(self._returnSelection)

    def createNode(self, data, position=None):
        nodeItem = NodeItem(self, data)

        # Store node in scene.
        self.scene().nodes[id(data)] = nodeItem

        if not position:
            # Get the center of the view.
            position = self.mapToScene(self.viewport().rect().center())

        # Set node position.
        self.scene().addItem(nodeItem)
        nodeItem.setPos(position - nodeItem.nodeCenter)
        nodeItem._createSlot()

        # Emit signal.
        self.signal_NodeCreated.emit(data.name)

        return nodeItem

    def deleteNode(self, node):
        if node in self.scene().nodes.values():
            nodeName = node.name
            node._remove()

            # Emit signal.
            self.signal_NodeDeleted.emit([nodeName])

    def createConnection(self, sourceData, targetData):
        id_source = id(sourceData)
        id_target = id(targetData)
        slot_child = self.scene().nodes[id_source].slot_child
        slot_parent = self.scene().nodes[id_target].slot_parent

        connection = ConnectionItem(
            slot_child.center(), slot_parent.center(),
            slot_child, slot_parent
        )

        connection.parentNode = slot_child.parentItem()
        connection.childNode = slot_parent.parentItem()

        slot_child.connect(slot_parent, connection)
        slot_parent.connect(slot_child, connection)

        connection.updatePath()

        self.scene().addItem(connection)

        return connection
