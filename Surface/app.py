"""Minimal PySide6 Surface gesture and keyboard application.

Run from the repository root with ``python -m Surface.app``.
"""

from __future__ import annotations

import sys
import time
from typing import Any

from PySide6.QtCore import QEvent, QPointF, Qt, Signal, QObject, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .input_model import GestureInput, GesturePoint, LatchedKeyboard
from .cgs_plot import curve_points
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
        self._trace_image = QImage(1, 1, QImage.Format.Format_ARGB32_Premultiplied)
        self._trace_image.fill(Qt.GlobalColor.transparent)
        self._last_trace_pixel: QPointF | None = None
        self.show_raw_curve = True
        self.show_cgs_curve = False
        self._cgs_curve_path = QPainterPath()
        self._cgs_curve_points: tuple[tuple[float, float], ...] = ()
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
        width, height = self.width(), self.height()
        # Preserve every input sample on the Max path before doing UI work.
        self.transport.send_gesture(point, width, height)
        self.last_xy = point
        self._ensure_trace_size(width, height)
        pixel = QPointF(point.x * width, point.y * height)
        painter = QPainter(self._trace_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#54d6c8"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self._last_trace_pixel is not None:
            painter.drawLine(self._last_trace_pixel, pixel)
        painter.end()
        self._last_trace_pixel = pixel
        self.update()

    def _begin(self, pointer: object, pos: QPointF) -> bool:
        if self.gesture.active or self.width() <= 0 or self.height() <= 0:
            return False
        self._clear_trace()
        if not self.gesture.begin(pointer, pos.x(), pos.y(), self.width(), self.height()):
            return False
        self.gesture_status = "Gesture active"
        self._pointer = pointer
        self.update()
        return True

    def _clear_trace(self) -> None:
        self._trace_image.fill(Qt.GlobalColor.transparent)
        self._last_trace_pixel = None

    def _ensure_trace_size(self, width: int, height: int) -> None:
        width, height = max(1, width), max(1, height)
        if self._trace_image.width() == width and self._trace_image.height() == height:
            return
        old_width, old_height = self._trace_image.width(), self._trace_image.height()
        self._trace_image = self._trace_image.scaled(
            width,
            height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        if self._last_trace_pixel is not None:
            self._last_trace_pixel = QPointF(
                self._last_trace_pixel.x() * width / old_width,
                self._last_trace_pixel.y() * height / old_height,
            )

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._ensure_trace_size(self.width(), self.height())
        self._rebuild_cgs_path()

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
            self.set_cgs_curve(())
        else:
            low = ", ".join(f"{v:.3g}" for v in group.low)
            high = ", ".join(f"{v:.3g}" for v in group.high)
            self.telemetry = (
                f"Wr {group.wr:.4g}   E {group.energy:.3g}   W0 {group.w0:.4g}   "
                f"Asum {group.asum:.3g}   Abal {group.abal:.3g}   Phi {group.phi:.3g}\n"
                f"Low [{low}]\nHigh [{high}]"
            )
            self.set_cgs_curve(curve_points(group))
        self.update()

    def set_show_raw_curve(self, visible: bool) -> None:
        self.show_raw_curve = visible
        self.update()

    def set_show_cgs_curve(self, visible: bool) -> None:
        self.show_cgs_curve = visible
        self.update()

    def set_cgs_curve(self, points: Any) -> None:
        """Set world-coordinate points for the display-only CGS curve."""
        self._cgs_curve_points = tuple((float(x), float(y)) for x, y in points)
        self._rebuild_cgs_path()
        self.update()

    def _rebuild_cgs_path(self) -> None:
        """Fit the current world-coordinate curve with equal pixel scale."""
        path = QPainterPath()
        points = self._cgs_curve_points
        if len(points) < 2 or self.width() <= 0 or self.height() <= 0:
            self._cgs_curve_path = path
            return

        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        span_x, span_y = x_max - x_min, y_max - y_min
        if span_x < 1e-12 and span_y < 1e-12:
            self._cgs_curve_path = path
            return
        span_x = max(span_x, 1e-12)
        span_y = max(span_y, 1e-12)
        margin = 0.10
        pixels_per_unit = min(
            self.width() * (1.0 - 2.0 * margin) / span_x,
            self.height() * (1.0 - 2.0 * margin) / span_y,
        )
        center_x = (x_min + x_max) / 2.0
        center_y = (y_min + y_max) / 2.0
        for index, (x, y) in enumerate(points):
            nx = 0.5 + (x - center_x) * pixels_per_unit / self.width()
            ny = 0.5 - (y - center_y) * pixels_per_unit / self.height()
            if index == 0:
                path.moveTo(nx, ny)
            else:
                path.lineTo(nx, ny)
        self._cgs_curve_path = path

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#171b20"))
        painter.setPen(QPen(QColor("#49545f"), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        if self.show_raw_curve and not self._trace_image.isNull():
            painter.drawImage(self.rect(), self._trace_image)
        if self.show_raw_curve and self._last_trace_pixel is not None:
            painter.setPen(QPen(QColor("#f0c674"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawPoint(self._last_trace_pixel)
        if self.show_cgs_curve and self._cgs_curve_path.elementCount() > 1:
            cgs_pen = QPen(QColor("#f0c674"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(cgs_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self._cgs_curve_path)

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
        self.signals.ready.connect(self._on_ready)
        self.signals.features.connect(self._on_features)
        self._last_ready = False
        self.keyboard_model = LatchedKeyboard(self.transport.send_note)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        status_bar = QWidget()
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 4, 10, 4)
        status_layout.setSpacing(12)
        self.raw_toggle = QCheckBox("Raw")
        self.raw_toggle.setChecked(True)
        self.cgs_toggle = QCheckBox("CGS")
        self.max_status_label = QLabel("Waiting for Max heartbeat")
        self.position_rate_label = QLabel("Position packets: 0/s")
        status_layout.addWidget(self.raw_toggle)
        status_layout.addWidget(self.cgs_toggle)
        status_layout.addStretch(1)
        status_layout.addWidget(self.max_status_label)
        status_layout.addWidget(self.position_rate_label)
        layout.addWidget(status_bar)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.keyboard = RotatedKeyboard(self.keyboard_model)
        self.canvas = GestureCanvas(self.transport)
        self.raw_toggle.toggled.connect(self.canvas.set_show_raw_curve)
        self.cgs_toggle.toggled.connect(self.canvas.set_show_cgs_curve)
        content_layout.addWidget(self.keyboard)
        content_layout.addWidget(self.canvas, 1)
        layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setMinimumSize(900, 600)

        self._rate_count = self.transport.position_packets_sent
        self._rate_time = time.monotonic()
        self._rate_timer = QTimer(self)
        self._rate_timer.setInterval(500)
        self._rate_timer.timeout.connect(self._update_position_rate)
        self._rate_timer.start()
        self.transport.start()

    def _update_position_rate(self) -> None:
        now = time.monotonic()
        count = self.transport.position_packets_sent
        elapsed = max(now - self._rate_time, 1e-6)
        rate = (count - self._rate_count) / elapsed
        self._rate_count = count
        self._rate_time = now
        self.position_rate_label.setText(f"Position packets: {rate:.0f}/s")

    def _on_ready(self, ready: bool) -> None:
        self.canvas.set_ready(ready)
        self.max_status_label.setText("Max ready" if ready else "Max unavailable")
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
