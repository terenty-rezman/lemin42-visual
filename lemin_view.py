import sys

from dataclasses import dataclass
import math

from PySide2.QtWidgets import QApplication, QOpenGLWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide2.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QTransform, QStaticText
from PySide2.QtCore import QObject, QRect, QRectF, Qt, QPoint, QPointF, Slot, Signal

from lemin_animation_control import SimulationState, AnimationControl


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
        self.create_solution_paths()

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

        # exclude solution links as they are going to be painted separatelly
        all_links = set(self.map.links)
        solution_links = set()

        for ant in self.solution.ants.values():
            for link in ant.path.links:
                solution_links.add(link)

        # set difference
        none_solution_links = all_links - solution_links

        self.link_layer = link_layer = QPainterPath()

        for link in none_solution_links:
            from_ = link.from_.coords
            to_ = link.to_.coords

            link_layer.moveTo(from_.x, from_.y)
            link_layer.lineTo(to_.x, to_.y)

    def create_solution_paths(self):
        self.solution_paths = []

        # use set to avoid path duplication for ants that come the same path
        unique_paths = set()

        for ant in self.solution.ants.values():
            path = ant.path
            if path not in unique_paths:
                unique_paths.add(path)

        for path in unique_paths:
            qpath = QPainterPath()
            for link in path.links:
                from_ = link.from_.coords
                to_ = link.to_.coords

                qpath.moveTo(from_.x, from_.y)
                qpath.lineTo(to_.x, to_.y)

            self.solution_paths.append(qpath)

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

        pen = QPen(QColor("#AAAAAA"), 1)
        pen.setCosmetic(True)  # makes pen size zoom independent
        self.text_pen = pen

    def create_ui(self):
        alignTop = Qt.AlignTop | Qt.AlignLeft
        alignBottom = Qt.AlignBottom | Qt.AlignLeft

        layout = QVBoxLayout()
        self.setLayout(layout)

        # add error label if any errors from parsing
        if self.map.error or self.solution.error:
            error_lbl = QLabel(self.map.error or self.solution.error)
            error_lbl.setObjectName("error")
            layout.addWidget(error_lbl, 0, alignTop)

        self.setStyleSheet("""
            QLabel {color: #eeeeee; font: 20px;}
            QLabel#error {color: #e91e63; font: 18px;}
            QLabel#second {color: #aaaaaa; font: 15px;}
            """)

        state_label = QLabel("playing")
        layout.addWidget(state_label, 0, alignTop)

        def on_state_changed(value):
            mapping = {
                SimulationState.playing: 'playing',
                SimulationState.paused: '<font color=\"#e91e63\">paused</font>'
            }

            state_label.setText(mapping[value])

        self.anim_control.stateChanged.connect(on_state_changed)

        step_label = QLabel("")
        layout.addWidget(step_label, 0, alignTop)

        def on_step_changed(value):
            step_label.setText(
                f'step <font color=\"#e91e63\">{value}</font> / {self.solution.number_of_steps - 1}')

        self.anim_control.stepChanged.connect(on_step_changed)
        on_step_changed(0)

        descr_label = QLabel("""
            <font color=\"#e91e63\">Space</font> to play / pause <br>
            <font color=\"#e91e63\">D</font> next step <br>
            <font color=\"#e91e63\">A</font> previous step
            """)
        descr_label.setObjectName('second')
        layout.addWidget(descr_label, 1, alignBottom)

    def timerEvent(self, ev):
        self.update()  # schedule widget repaint
        self.anim_control.update()  # update ant animation

    def paintEvent(self, paintEvent):
        painter = QPainter(self)

        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)

        # clear background
        painter.setBackground(QColor("#202124"))
        painter.eraseRect(self.rect())

        self.apply_camera(painter)

        self.draw_links(painter)

        self.draw_solution_paths(painter)

        self.draw_rooms(painter)

        self.draw_ants(painter)

        # reset transform
        painter.resetMatrix()

        self.draw_room_names(painter)

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

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Space:
            self.anim_control.play_or_pause()
        elif ev.key() == Qt.Key_D:
            self.anim_control.rewind_forward()
        elif ev.key() == Qt.Key_A:
            self.anim_control.rewind_backward()

    def apply_camera(self, painter):
        mvp = self.mvp()
        painter.setTransform(mvp)

    def mvp(self):
        view_center = self.rect().center()
        mvp = QTransform()
        mvp.translate(view_center.x(), view_center.y())
        mvp.scale(self.camera.zoom, self.camera.zoom)
        mvp.translate(self.camera.pos.x(), self.camera.pos.y())
        return mvp

    def zoom_reverse(self, x):
        return x/self.camera.zoom

    def draw_links(self, painter):
        painter.setPen(self.link_pen)
        painter.drawPath(self.link_layer)

    def draw_solution_paths(self, painter):
        pen = QPen(QColor("#880E4F"), 2)
        pen.setCosmetic(True)  # makes pen size zoom independent
        painter.setPen(pen)
        for path in self.solution_paths:
            painter.drawPath(path)

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

    def draw_room_names(self, painter):
        # manually transform text position to draw text unaffected by zoom
        painter.setPen(self.text_pen)
        mvp = self.mvp()
        rect = QRectF(-100, self.room_size /
                      2, 200, self.room_size)

        for room in self.solution.all_rooms:
            screen_c = mvp.map(QPointF(room.coords.x, room.coords.y))
            painter.drawText(rect.translated(screen_c),
                             Qt.AlignCenter, room.name)


def init_and_run(map, solution):
    # Create the Qt Application
    app = QApplication()
    # Create and show the form
    view = View(map, solution)
    view.resize(800, 600)
    view.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
