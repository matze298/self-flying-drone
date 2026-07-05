# Mechanical integration

Mechanical integration belongs to the hardware bench and manual-aircraft steps of the [Learning path](../start/learning-path.md). Do not use airframe work to skip the simulator, wiring, or safety-gate discipline.

## Fuselage layout

```mermaid
flowchart LR
  NOSE[Nose<br/>camera + lens hood] --> GNSS[High / forward<br/>GNSS antenna]
  GNSS --> CG[CG zone<br/>battery + companion tray]
  CG --> FC[Low-vibration bay<br/>flight controller]
  FC --> ESC[Rear bay<br/>ESC + motor wires]
```

This is a **layout pattern**, not a universal placement rule. It should be adapted after checking the airframe’s CG range, antenna separation and service access.

## Companion tray specification

| Requirement | Implementation |
|---|---|
| CG control | Tray located around the approved CG adjustment zone |
| Retention | Mechanical strap + secondary restraint; never adhesive only |
| Vibration | Light damping only; avoid a soft, oscillating platform |
| Cooling | Defined inlet/outlet path; fan if the heat budget requires it |
| Serviceability | One connector group and tray removal without cutting ties |
| Protection | Non-conductive standoffs; keep exposed PCB away from carbon or metal parts |

## Camera mount

1. Use a rigid nose/underside plate, not the flight-controller isolator.
2. Mark forward direction and record camera yaw/pitch relative to the airframe.
3. Use a field-of-view that sees enough ground at the intended altitude.
4. Protect the lens from grass and belly landings.
5. Re-run camera calibration if lens, mounting angle, resolution or crop changes.

## Mass-change process

Every hardware addition follows this loop:

```text
weigh module → mount near CG → verify CG → inspect control travel → bench test power → low-risk flight test → update BOM and photos
```

Do not make several structural, propulsion and software changes before the same flight. That makes outcomes impossible to interpret.
