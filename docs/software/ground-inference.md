# Ground-side inference

## Objective

Build an observability loop before building an autonomy loop.

```mermaid
flowchart LR
  CAM[Aircraft camera] --> STREAM[H.264 preview]
  FC[Flight controller] --> TEL[MAVLink telemetry]
  STREAM --> LAPTOP[Laptop capture process]
  TEL --> LAPTOP
  LAPTOP --> DET[Detector]
  DET --> VIEW[Live overlay]
  DET --> LOG[Detection log + snapshots]
  LOG --> REVIEW[Post-flight evaluation]
```

## Minimum viable toolchain

Use the repo-managed `uv` setup path. Ground inference starts after the SITL and bench interfaces are understood, but before onboard compute is required.

```bash
./setup.py --workstream sim
```

The `sim` workstream already installs the MAVLink client tools used for telemetry association. When the first real vision CLI lands, add a dedicated `vision` or `ground` dependency group to `pyproject.toml` instead of installing ad hoc packages with `pip`. Expected first dependencies are OpenCV, NumPy, ONNX Runtime, pandas or Polars, and the selected detector wrapper.

### Responsibilities by process

| Process | Responsibility | Must never do |
|---|---|---|
| `capture` | Receive stream, timestamp frames, reconnect on failure | Block flight telemetry loop |
| `telemetry` | Subscribe to MAVLink, cache latest valid state | Invent state if messages are stale |
| `detector` | Produce label/confidence/bounding box | Send direct servo/throttle commands |
| `validator` | Apply debounce, confidence, freshness and test-mode policy | Treat one frame as a mission command |
| `logger` | Write event, frame reference, state and config | Drop errors silently |
| `viewer` | Present human-readable overlay | Become the only safety interface |

## Start task: orange marker detection

Follow the learning path order:

1. Use a recorded or synthetic video clip before flying.
2. Make a high-contrast, known-size orange ground marker.
3. Record video during manual or waypoint flights over a safe field only after the relevant flight gates pass.
4. Run detector offline on the original recording.
5. Compare false positives, missed detections and confidence distribution.
6. Move to live laptop inference at low resolution.
7. Log only; do not request aircraft behavior.

## Event validation example

```python
from dataclasses import dataclass
from time import monotonic

@dataclass
class Detection:
    label: str
    confidence: float
    frame_time: float

class EventValidator:
    def __init__(self, threshold: float = 0.85, required_hits: int = 3):
        self.threshold = threshold
        self.required_hits = required_hits
        self.hits = 0

    def accept(self, det: Detection, telemetry_age_s: float) -> bool:
        if telemetry_age_s > 0.5 or det.confidence < self.threshold:
            self.hits = 0
            return False
        self.hits += 1
        return self.hits >= self.required_hits
```

This code demonstrates **logging qualification**, not flight control.

## Evaluation metrics

| Metric | Why it matters |
|---|---|
| Precision / false-alert rate | Operator trust and unnecessary mission interruptions |
| Recall | How often useful targets are missed |
| End-to-end latency | Whether frames correspond to current aircraft state |
| Telemetry age | Whether position/attitude association is meaningful |
| Frame-drop/reconnect rate | Video-link reliability |
| Per-flight reproducibility | Whether a result can be debugged later |
