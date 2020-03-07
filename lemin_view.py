import sys
from dataclasses import dataclass
from PySide2.QtWidgets import QApplication, QOpenGLWidget, QVBoxLayout, QLabel
from PySide2.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QTransform
from PySide2.QtCore import QRect, QRectF, Qt, QPoint, QPointF


@dataclass
class Camera:
    viewport: QOpenGLWidget
    pos: QPointF
    zoom: float

    def fit_solution_in_view(self, solution):
        if not solution.rect:
            return

        solution_rect = QRect(QPoint(solution.rect.left, solution.rect.top),
                              QPoint(solution.rect.right, solution.rect.bottom))

        viewport_rect = self.viewport.rect()

        # compute zoom level
        if solution_rect.width() > solution_rect.height():
            zoom = viewport_rect.width() / solution_rect.width() if viewport_rect.width() else 1
        else:
            zoom = viewport_rect.height() / solution_rect.height() if viewport_rect.height() else 1

        self.zoom = 0.80 * zoom if zoom else 1
        self.zoom = clamp(self.zoom, 0.1, 55)  # limit zoom level

        # center view on rect center
        self.pos = -QPointF(solution_rect.center())


def clamp(v, smallest, largest):
    "limit value on both sides"
    return max(smallest, min(v, largest))


class View(QOpenGLWidget):  # inherit from QOpenGLWidget to enable opengl backend for QPainter
    room_size = 28
    ant_size = 16

    def __init__(self, map, solution, parent=None):
        super().__init__(parent)
        self.setWindowTitle("lemin42 visual")

        self.camera = Camera(self, QPointF(0, 0), 1)
        self.mouse_last_pos = QPoint(0, 0)
        self.map = map
        self.solution = solution
        self.steps = 0

        self.create_pens()
        self.create_link_layer()

        self.anim_control = AnimationControl(solution)

        self.create_ui()

        self.camera.fit_solution_in_view(solution)

        # start redraw timer
        self.startTimer(1000 / 60)  # 60 fps

    def create_link_layer(self):
        """
            optimization: store all links in QPainterPath object
            to draw it in one call
        """
        self.link_layer = link_layer = QPainterPath()

        for link in self.map.links:
            from_ = link.from_.coords
            to_ = link.to_.coords

            link_layer.moveTo(from_.x, from_.y)
            link_layer.lineTo(to_.x, to_.y)

    def create_pens(self):
        pen = QPen(QColor("#3C4042"), 3)
        pen.setCosmetic(True)  # makes pen size zoom independent
        self.link_pen = pen

        pen = QPen(QColor("#606368"), self.room_size)
        pen.setCosmetic(True)  # makes pen size zoom independent
        self.room_pen = pen

        pen = QPen(QColor("#FF0266"), self.ant_size)
        pen.setCosmetic(True)  # makes pen size zoom independent
        self.ant_pen = pen

    def create_ui(self):
        align = Qt.AlignTop | Qt.AlignLeft

        layout = QVBoxLayout()
        self.setLayout(layout)

        # add error label if any errors from parsing
        if self.map.error or self.solution.error:
            error_lbl = QLabel(self.map.error or self.solution.error)
            error_lbl.setObjectName("error")
            layout.addWidget(error_lbl, 0, align)

        self.setStyleSheet("QLabel#error {color: #e91e63; font: 20px;}")

    def timerEvent(self, ev):
        self.update()  # schedule widget repaint
        self.anim_control.update()  # update ant animation

    def paintEvent(self, paintEvent):
        painter = QPainter(self)

        # clear background
        painter.setBackground(QColor("#202124"))
        painter.eraseRect(self.rect())

        self.apply_camera(painter)

        self.draw_links(painter)

        self.draw_rooms(painter)

        self.draw_ants(painter)

        # draw solution rect
        # solution_rect = QRect(QPoint(self.solution.rect.left, self.solution.rect.top),
        #                       QPoint(self.solution.rect.right, self.solution.rect.bottom))

        # pen = QPen(QColor("#777742"), 2)
        # pen.setCosmetic(True)  # makes pen size zoom independent
        # painter.setPen(pen)
        # painter.setBrush(Qt.NoBrush)
        # painter.drawRect(solution_rect)

    def mousePressEvent(self, ev):
        left_button_pressed = bool(ev.buttons() & Qt.LeftButton)

        if left_button_pressed:
            self.mouse_last_pos = ev.pos()

    def mouseMoveEvent(self, ev):  # mouse move only triggered when a mouse button pressed
        dmouse = ev.pos() - self.mouse_last_pos
        self.camera.pos += self.zoom_reverse(QPointF(dmouse))
        self.mouse_last_pos = ev.pos()

    def wheelEvent(self, ev):  # mouse wheel
        if ev.delta() < 0:
            self.camera.zoom /= 1.2
        else:
            self.camera.zoom *= 1.2

        # limit camera zoom level
        self.camera.zoom = clamp(self.camera.zoom, 0.1, 55)

    def apply_camera(self, painter):
        view_center = self.rect().center()
        transform = QTransform()
        transform.translate(view_center.x(), view_center.y())
        transform.scale(self.camera.zoom, self.camera.zoom)
        transform.translate(self.camera.pos.x(), self.camera.pos.y())
        painter.setTransform(transform)

    def zoom_reverse(self, x):
        return x/self.camera.zoom

    def draw_links(self, painter):
        painter.setPen(self.link_pen)
        painter.drawPath(self.link_layer)

    def draw_rooms(self, painter):
        painter.setPen(self.room_pen)
        for room in self.map.rooms.values():
            painter.drawPoint(room.coords.x, room.coords.y)

    def draw_ants(self, painter):
        if self.solution.error:
            return

        painter.setPen(self.ant_pen)
        for ant in self.solution.ants.values():
            painter.drawPoint(ant.x, ant.y)


def init_and_run(map, solution):
    # Create the Qt Application
    app = QApplication()
    # Create and show the form
    view = View(map, solution)
    view.resize(800, 600)
    view.show()
    # Run the main Qt loop
    sys.exit(app.exec_())


class AnimationControl:
    def __init__(self, solution):
        self.solution = solution
        self.time = 0
        self.freeze_time = 0

    def update(self):
        if self.solution.error:
            return

        if self.freeze_time == 0:
            self.time += 1
        else:
            self.freeze_time -= 1
            return

        step = self.time / 100
        self.solution.set_step(step)

        if self.time % 100 == 0:
            self.freeze_time = 20

        if step > self.solution.number_of_steps:
            self.time = 0
