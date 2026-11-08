"""Small dependency-free OSC/TUIO transport for the Surface prototype."""

from __future__ import annotations

import math
import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Callable

from .input_model import GesturePoint


def _osc_string(value: str) -> bytes:
    encoded = value.encode("utf-8") + b"\0"
    return encoded + b"\0" * ((-len(encoded)) % 4)


def encode_osc(address: str, *arguments: int | float | str) -> bytes:
    """Encode the OSC scalar types used by the app/Max bridge."""
    tags = [","]
    payload = bytearray()
    for value in arguments:
        if isinstance(value, bool):
            raise TypeError("OSC booleans are not part of this bridge schema")
        if isinstance(value, int):
            tags.append("i")
            payload.extend(struct.pack(">i", value))
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("OSC float arguments must be finite")
            tags.append("f")
            payload.extend(struct.pack(">f", value))
        elif isinstance(value, str):
            tags.append("s")
            payload.extend(_osc_string(value))
        else:
            raise TypeError(f"Unsupported OSC argument: {type(value).__name__}")
    return _osc_string(address) + _osc_string("".join(tags)) + bytes(payload)


def encode_osc_bundle(*messages: bytes) -> bytes:
    """Encode an immediate OSC bundle, as used for a TUIO cursor frame."""
    bundle = bytearray(b"#bundle\0" + struct.pack(">Q", 1))
    for message in messages:
        bundle.extend(struct.pack(">i", len(message)))
        bundle.extend(message)
    return bytes(bundle)


def _read_osc_string(packet: bytes, offset: int) -> tuple[str, int]:
    end = packet.find(b"\0", offset)
    if end < 0:
        raise ValueError("unterminated OSC string")
    value = packet[offset:end].decode("utf-8")
    return value, (end + 4) & ~3


def decode_osc(packet: bytes) -> tuple[str, tuple[int | float | str, ...]]:
    """Decode a scalar OSC message (the bridge doesn't use OSC bundles)."""
    address, offset = _read_osc_string(packet, 0)
    tags, offset = _read_osc_string(packet, offset)
    if not tags.startswith(","):
        raise ValueError("invalid OSC type tag string")
    args: list[int | float | str] = []
    for tag in tags[1:]:
        if tag == "i":
            args.append(struct.unpack_from(">i", packet, offset)[0])
            offset += 4
        elif tag == "f":
            args.append(struct.unpack_from(">f", packet, offset)[0])
            offset += 4
        elif tag == "s":
            value, offset = _read_osc_string(packet, offset)
            args.append(value)
        else:
            raise ValueError(f"unsupported OSC type tag {tag!r}")
    return address, tuple(args)


@dataclass(frozen=True)
class FeatureGroup:
    wr: float
    energy: float
    w0: float
    asum: float
    abal: float
    phi: float
    low: tuple[float, ...]
    high: tuple[float, ...]


@dataclass(frozen=True)
class FeatureTelemetry:
    groups: tuple[FeatureGroup, ...]

    @property
    def active_group(self) -> FeatureGroup | None:
        return max(self.groups, key=lambda group: group.energy, default=None)


class FeatureAssembler:
    """Build five 18-value groups from channel-indexed Max snapshots.

    The index is 1-based and identifies a fixed feature channel, so arrival
    order is irrelevant. Repeated indices mark a new snapshot frame; this lets
    the assembler discard a partial frame if a UDP datagram was lost.
    """

    CHANNEL_COUNT = 90
    GROUP_WIDTH = 18

    def __init__(self) -> None:
        self._values = [0.0] * self.CHANNEL_COUNT
        self._seen: set[int] = set()

    def add(self, channel: int, value: int | float) -> FeatureTelemetry | None:
        if isinstance(channel, bool) or not isinstance(channel, int):
            raise ValueError("/circle/feature channel must be an integer")
        if not 1 <= channel <= self.CHANNEL_COUNT:
            raise ValueError("/circle/feature channel must be between 1 and 90")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("/circle/feature value must be numeric")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("/circle/feature value must be finite")

        index = channel - 1
        if index in self._seen:
            # The channel is being sampled again before this frame was whole.
            self._seen.clear()
        self._values[index] = value
        self._seen.add(index)

        if len(self._seen) < self.CHANNEL_COUNT:
            return None

        groups = []
        for start in range(0, self.CHANNEL_COUNT, self.GROUP_WIDTH):
            f = self._values[start : start + self.GROUP_WIDTH]
            groups.append(FeatureGroup(f[0], f[1], f[2], f[3], f[4], f[5], tuple(f[6:12]), tuple(f[12:18])))
        self._seen.clear()
        return FeatureTelemetry(tuple(groups))


def parse_telemetry(address: str, args: tuple[int | float | str, ...]) -> bool | FeatureTelemetry:
    """Parse the proposed /circle/ready and /circle/features messages."""
    if address == "/circle/ready":
        if len(args) != 1 or not isinstance(args[0], (int, float)):
            raise ValueError("/circle/ready expects one numeric argument")
        return bool(args[0])
    if address != "/circle/features":
        raise ValueError(f"unknown telemetry address: {address}")
    if not args or not isinstance(args[0], int):
        raise ValueError("/circle/features must begin with an integer group count")
    count = args[0]
    group_width = 18
    if count < 0 or len(args) != 1 + count * group_width:
        raise ValueError("/circle/features argument count does not match group count")
    groups = []
    for i in range(count):
        values = args[1 + i * group_width:1 + (i + 1) * group_width]
        if any(not isinstance(value, (int, float)) for value in values):
            raise ValueError("feature group values must be numeric")
        f = tuple(float(value) for value in values)
        groups.append(FeatureGroup(f[0], f[1], f[2], f[3], f[4], f[5], f[6:12], f[12:18]))
    return FeatureTelemetry(tuple(groups))


class MaxTransport:
    """UDP bridge to the existing Max TUIO input and additive note port."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        tuio_port: int = 3333,
        note_port: int = 3334,
        telemetry_port: int = 3335,
        on_ready: Callable[[bool], None] | None = None,
        on_features: Callable[[FeatureTelemetry], None] | None = None,
        ready_timeout: float = 2.5,
        require_ready: bool = True,
    ) -> None:
        self._destination = (host, tuio_port)
        self._note_destination = (host, note_port)
        self._ready_timeout = ready_timeout
        self._require_ready = require_ready
        self._on_ready = on_ready
        self._on_features = on_features
        self._feature_assembler = FeatureAssembler()
        self._tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._rx.bind(("0.0.0.0", telemetry_port))
        self._rx.settimeout(0.25)
        self._running = False
        self._thread: threading.Thread | None = None
        self._ready = False
        self._last_heartbeat = 0.0
        self._sequence = 0

    @property
    def ready(self) -> bool:
        return self._ready and time.monotonic() - self._last_heartbeat <= self._ready_timeout

    def send_gesture(self, point: GesturePoint, width: float, height: float) -> None:
        """Send TUIO set coordinates compensated for Max's fixed Y scaling."""
        if not self._can_send() or width <= 0 or height <= 0:
            return
        y_tuio = 1.0 - (1.0 - point.y) * (height / width) / 1.42
        self._sequence += 1
        # Existing Max receiver routes /tuio/2Dcur -> set -> unpack; remaining
        # values are zero velocity/acceleration fields and ignored by this patch.
        session = 1
        packet = encode_osc_bundle(
            encode_osc("/tuio/2Dcur", "set", session, point.x, y_tuio, 0.0, 0.0, 0.0, 0.0),
            encode_osc("/tuio/2Dcur", "alive", session),
            encode_osc("/tuio/2Dcur", "fseq", self._sequence),
        )
        self._tx.sendto(packet, self._destination)

    def end_gesture(self) -> None:
        """Send a TUIO cursor frame that releases the app's active session."""
        if not self._can_send():
            return
        self._sequence += 1
        packet = encode_osc_bundle(
            encode_osc("/tuio/2Dcur", "alive"),
            encode_osc("/tuio/2Dcur", "fseq", self._sequence),
        )
        self._tx.sendto(packet, self._destination)

    def send_note(self, pitch: int, velocity: int) -> None:
        if self._can_send() and 60 <= pitch <= 71 and velocity in (0, 100):
            self._tx.sendto(encode_osc("/circle/note", pitch, velocity), self._note_destination)

    def _can_send(self) -> bool:
        return not self._require_ready or self.ready

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, name="max-telemetry", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._running = False
        self._rx.close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _receive_loop(self) -> None:
        # Callbacks run on this worker thread; a Qt UI should relay them through
        # signals before touching widgets.
        while self._running:
            try:
                packet, _ = self._rx.recvfrom(8192)
            except socket.timeout:
                self._update_ready()
                continue
            except OSError:
                break
            try:
                address, args = decode_osc(packet)
                if address == "/circle/feature":
                    if len(args) != 2:
                        raise ValueError("/circle/feature expects channel and value")
                    result = self._feature_assembler.add(args[0], args[1])
                else:
                    result = parse_telemetry(address, args)
            except (ValueError, UnicodeError, struct.error):
                continue
            if isinstance(result, bool):
                self._last_heartbeat = time.monotonic()
                self._ready = result
                self._update_ready()
            elif isinstance(result, FeatureTelemetry) and self._on_features is not None:
                self._on_features(result)

    def _update_ready(self) -> None:
        ready = self.ready
        if getattr(self, "_reported_ready", None) != ready:
            self._reported_ready = ready
            if self._on_ready is not None:
                self._on_ready(ready)

