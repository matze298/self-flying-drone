# Open-source licenses

Licenses can influence how code may be redistributed. Confirm the exact version/repository license before commercial distribution; this table is an engineering reminder, not legal advice.

| Component | Typical use | License posture to verify |
|---|---|---|
| ArduPilot | Flight-control firmware | GPLv3 |
| OpenHD | Open digital video project | GPLv3 |
| MAVSDK | High-level MAVLink client API | BSD-3-Clause |
| OpenCV 4.5+ | Image/video processing | Apache-2.0 |
| ONNX Runtime | Cross-platform inference | MIT |
| Ultralytics YOLO | Training/inference convenience layer | AGPL-3.0 or commercial license |
| GStreamer | Media pipeline | LGPL/GPL components vary |
| FFmpeg | Media tools | LGPL/GPL configuration dependent |
| CVAT / Label Studio | Annotation | Check deployment and version license |

## Policy for this project

- Maintain a `THIRD_PARTY_NOTICES.md` file in the code repository.
- Pin dependencies and retain their license metadata in release artifacts.
- Do not assume “open source” means unrestricted proprietary redistribution.
- Prefer permissively licensed runtimes (OpenCV, ONNX Runtime, MAVSDK) for the custom glue code; review model and training framework terms independently.
