"""Minimal PySide6 Surface gesture and keyboard application.

Run from the repository root with ``python -m Surface.app``.
"""

from __future__ import annotations

import sys
from typing import Any

from PySide6.QtCore import QEvent, QPointF, Qt, Signal, QObject
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QSizePolicy,
    QWidget,
)

from .input_model import GestureInput, GesturePoint, LatchedKeyboard
from .transport import FeatureTelemetry, MaxTransport


class UiSignals(QObject):
    """Deliver receive-thread callbacks safely to the Qt UI thread."""

    ready = Signal(bool)
    features = Signal(object)


class GestureCanvas(QWidget):
    """Touch/mouse drawing area; emits normalized points without CGL math."""

    def __init__(self, transport: MaxTransport) -> None:
        super().__init__()
        self.transport = transport
        self.gesture = GestureInput(self._point_received)
        self.trace: list[QPointF] = []
        self.last_xy: GesturePoint | None = None
        self.max_status = "Waiting for Max heartbeat"
        self.gesture_status = "Gesture idle"
        self.telemetry = "No feature telemetry"
        self._pointer: object | None = None
        self._mouse_active = False
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.setMouseTracking(True)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _point_received(self, point: GesturePoint) -> None:
        self.last_xy = point
        self.trace.append(QPointF(point.x * self.width(), point.y * self.height()))
        self.transport.send_gesture(point, self.width(), self.height())
        self.update()

    def _begin(self, pointer: object, pos: QPointF) -> bool:
        if not self.gesture.begin(pointer, pos.x(), pos.y(), self.width(), self.height()):
            return False
        self.gesture_status = "Gesture active"
        self._pointer = pointer
        self.trace.clear()
        # begin() emits before trace.clear(); restore its first sample.
        if self.last_xy is not None:
            self.trace.append(QPointF(self.last_xy.x * self.width(), self.last_xy.y * self.height()))
        self.update()
        return True

    def _move(self, pointer: object, pos: QPointF) -> bool:
        return self.gesture.move(pointer, pos.x(), pos.y(), self.width(), self.height())

    def _end(self, pointer: object, final_pos: QPointF | None = None) -> bool:
        if final_pos is not None:
            self._move(pointer, final_pos)
        if not self.gesture.end(pointer):
            return False
        self.gesture_status = "Gesture idle"
        self.transport.end_gesture()
        self._pointer = None
        self.update()
        return True

    def event(self, event: QEvent) -> bool:
        etype = event.type()
        if etype in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd, QEvent.Type.TouchCancel):
            points = event.points() if hasattr(event, "points") else event.touchPoints()
            if etype == QEvent.Type.TouchCancel:
                if self._pointer is not None:
                    self._end(self._pointer)
                return True
            for point in points:
                pid = ("touch", point.id())
                state = point.state()
                if state == Qt.TouchPointState.Pressed:
                    self._begin(pid, point.position())
                elif state == Qt.TouchPointState.Moved:
                    self._move(pid, point.position())
                elif state == Qt.TouchPointState.Released:
                    self._end(pid, point.position())
            return True
        if etype == QEvent.Type.TabletPress:
            return self._begin("pen", event.position()) or True
        if etype == QEvent.Type.TabletMove:
            if self.gesture.active:
                self._move("pen", event.position())
            return True
        if etype == QEvent.Type.TabletRelease:
            self._end("pen", event.position())
            return True
        return super().event(event)

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_active = self._begin("mouse", event.position())
            event.accept()

    def mouseMoveEvent(self, event: Any) -> None:
        if self._mouse_active and event.buttons() & Qt.MouseButton.LeftButton:
            self._move("mouse", event.position())
            event.accept()

    def mouseReleaseEvent(self, event: Any) -> None:
        if self._mouse_active and event.button() == Qt.MouseButton.LeftButton:
            self._end("mouse", event.position())
            self._mouse_active = False
            event.accept()

    def set_ready(self, ready: bool) -> None:
        if ready:
            self.max_status = "Max ready"
        else:
            self.max_status = "No Max heartbeat — drawing local; Max input paused"
        self.update()

    def set_features(self, telemetry: FeatureTelemetry) -> None:
        group = telemetry.active_group
        if group is None:
            self.telemetry = "No active feature group"
        else:
            low = ", ".join(f"{v:.3g}" for v in group.low)
            high = ", ".join(f"{v:.3g}" for v in group.high)
            self.telemetry = (
                f"Wr {group.wr:.4g}   E {group.energy:.3g}   W0 {group.w0:.4g}   "
                f"Asum {group.asum:.3g}   Abal {group.abal:.3g}   Phi {group.phi:.3g}\n"
                f"Low [{low}]\nHigh [{high}]"
            )
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#171b20"))
        painter.setPen(QPen(QColor("#49545f"), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        if len(self.trace) >= 2:
            path = QPainterPath(self.trace[0])
            for point in self.trace[1:]:
                path.lineTo(point)
            painter.setPen(QPen(QColor("#54d6c8"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)
        if self.trace:
            painter.setPen(QPen(QColor("#f0c674"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPoint(self.trace[-1])

        overlay = self.rect().adjusted(14, 14, -14, -14)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 165))
        painter.drawRoundedRect(overlay.left(), overlay.top(), overlay.width(), 92, 8, 8)
        painter.setPen(QColor("#edf2f7"))
        painter.drawText(overlay.adjusted(12, 8, -12, -8), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         f"{self.max_status}   |   {self.gesture_status}\n{self._xy_text()}\n{self.telemetry}")

    def _xy_text(self) -> str:
        if self.last_xy is None:
            return "XY  —"
        return f"XY  x {self.last_xy.x:.4f}   y {self.last_xy.y:.4f}"


class RotatedKeyboard(QWidget):
    """One octave drawn upright with its front edge against screen-left."""

    _WHITE_PITCHES = (0, 2, 4, 5, 7, 9, 11)
    _BLACK_AFTER = (1, 3, 6, 8, 10)
    _NAMES = ("C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B")

    def __init__(self, keyboard: LatchedKeyboard) -> None:
        super().__init__()
        self.keyboard = keyboard
        self.setFixedWidth(128)
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

    def _hit_pitch(self, pos: QPointF) -> int | None:
        w, h = self.width(), self.height()
        row_h = h / 7
        # Front is screen-left; raised/sharp keys sit at the back (screen-right).
        if pos.x() > w * 0.62:
            for after in self._BLACK_AFTER:
                row = sum(1 for white in self._WHITE_PITCHES if white < after) - 1
                y0 = row * row_h + row_h * 0.62
                y1 = (row + 1) * row_h + row_h * 0.38
                if y0 <= pos.y() < y1:
                    return 60 + after
        row = max(0, min(6, int(pos.y() / row_h)))
        return 60 + self._WHITE_PITCHES[row]

    def _press(self, pos: QPointF) -> None:
        pitch = self._hit_pitch(pos)
        if pitch is not None:
            self.keyboard.press(pitch)
            self.update()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press(event.position())
            event.accept()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.TouchBegin:
            points = event.points() if hasattr(event, "points") else event.touchPoints()
            if points:
                self._press(points[0].position())
            return True
        return super().event(event)

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#111418"))
        row_h = self.height() / 7
        white_index = 0
        for pitch_class in self._WHITE_PITCHES:
            rect = self.rect().adjusted(1, int(white_index * row_h) + 1, -1, -int((6 - white_index) * row_h) - 1)
            selected = self.keyboard.active_pitch == 60 + pitch_class
            painter.setBrush(QColor("#68d5c5") if selected else QColor("#f3f3ee"))
            painter.setPen(QPen(QColor("#59616a"), 1))
            painter.drawRect(rect)
            painter.setPen(QColor("#22272c"))
            painter.drawText(rect.adjusted(8, 0, -4, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             self._NAMES[pitch_class])
            white_index += 1
        for pitch_class in self._BLACK_AFTER:
            row = sum(1 for white in self._WHITE_PITCHES if white < pitch_class) - 1
            y0 = int((row + 0.62) * row_h)
            y1 = int((row + 1.38) * row_h)
            rect = self.rect().adjusted(int(self.width() * 0.62), y0, -1, -(self.height() - y1))
            selected = self.keyboard.active_pitch == 60 + pitch_class
            painter.setBrush(QColor("#397e78") if selected else QColor("#252b32"))
            painter.setPen(QPen(QColor("#0a0c0e"), 1))
            painter.drawRoundedRect(rect, 3, 3)


class SurfaceWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Circle Surface")
        self.signals = UiSignals()
        # Keep outgoing input gated until the Surface Max host is heartbeating.
        self.transport = MaxTransport(
            on_ready=self.signals.ready.emit,
            on_features=self.signals.features.emit,
        )
        self.transport.start()
        self.signals.ready.connect(self._on_ready)
        self.signals.features.connect(self._on_features)
        self._last_ready = False
        self.keyboard_model = LatchedKeyboard(self.transport.send_note)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.keyboard = RotatedKeyboard(self.keyboard_model)
        self.canvas = GestureCanvas(self.transport)
        layout.addWidget(self.keyboard)
        layout.addWidget(self.canvas, 1)
        self.setCentralWidget(root)
        self.setMinimumSize(900, 600)

    def _on_ready(self, ready: bool) -> None:
        self.canvas.set_ready(ready)
        if self._last_ready and not ready and self.keyboard_model.active_pitch is not None:
            self.keyboard_model.stop()
            self.keyboard.update()
        self._last_ready = ready

    def _on_features(self, telemetry: FeatureTelemetry) -> None:
        self.canvas.set_features(telemetry)

    def closeEvent(self, event: Any) -> None:
        self.keyboard_model.stop()
        self.transport.close()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Circle Surface")
    window = SurfaceWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
