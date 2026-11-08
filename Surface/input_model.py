"""Device-independent gesture and one-octave keyboard state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable


@dataclass(frozen=True)
class GesturePoint:
    """A normalized gesture sample, before Max-specific aspect mapping."""

    x: float
    y: float


class GestureInput:
    """Own one pointer at a time and emit normalized samples in event order."""

    def __init__(self, on_point: Callable[[GesturePoint], None]) -> None:
        self._on_point = on_point
        self._active_pointer: Hashable | None = None

    @property
    def active(self) -> bool:
        return self._active_pointer is not None

    def begin(self, pointer: Hashable, x: float, y: float, width: float, height: float) -> bool:
        if self.active or width <= 0 or height <= 0:
            return False
        self._active_pointer = pointer
        self._emit(x, y, width, height)
        return True

    def move(self, pointer: Hashable, x: float, y: float, width: float, height: float) -> bool:
        if pointer != self._active_pointer or width <= 0 or height <= 0:
            return False
        self._emit(x, y, width, height)
        return True

    def end(self, pointer: Hashable) -> bool:
        if pointer != self._active_pointer:
            return False
        self._active_pointer = None
        return True

    def cancel(self) -> None:
        self._active_pointer = None

    def _emit(self, x: float, y: float, width: float, height: float) -> None:
        px = min(1.0, max(0.0, x / width))
        py = min(1.0, max(0.0, y / height))
        self._on_point(GesturePoint(px, py))


class LatchedKeyboard:
    """Model monophonic latch/replace behavior for MIDI pitches C4–B4."""

    FIRST_PITCH = 60
    LAST_PITCH = 71
    VELOCITY = 100

    def __init__(self, send_note: Callable[[int, int], None]) -> None:
        self._send_note = send_note
        self.active_pitch: int | None = None

    def press(self, pitch: int) -> bool:
        if not self.FIRST_PITCH <= pitch <= self.LAST_PITCH:
            return False
        if pitch == self.active_pitch:
            self.stop()
        else:
            if self.active_pitch is not None:
                self._send_note(self.active_pitch, 0)
            self.active_pitch = pitch
            self._send_note(pitch, self.VELOCITY)
        return True

    def stop(self) -> None:
        if self.active_pitch is not None:
            pitch = self.active_pitch
            self.active_pitch = None
            self._send_note(pitch, 0)

