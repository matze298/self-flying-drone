# Configuration chooser

Start with the desired *end state*, then select the smallest architecture that reaches it without forcing a rebuild.

```mermaid
flowchart TD
  A{Need onboard inference<br/>in the first six months?}
  A -- No --> B[Ground-first build<br/>laptop inference + video link]
  A -- Yes --> C{Need more than basic<br/>marker / object detection?}
  C -- No --> D[Jetson Orin Nano 8 GB<br/>or Raspberry Pi 5 + accelerator]
  C -- Yes --> E[Jetson Orin NX 16 GB<br/>on production carrier]
  B --> F{Will payload likely exceed<br/>camera + radio + battery?}
  D --> F
  E --> G[Choose 1.8–2.0 m cargo pusher]
  F -- No --> H[Choose 1.4–1.6 m pusher]
  F -- Yes --> G
```

## Choose a build profile

| Profile | Best for | Initial inference | Upgrade headroom | Avoid if |
|---|---|---|---|---|
| **Ground-first** | Learning flight, collecting data, laptop-powered development | Laptop | High—add compute later | You need no-dependency detection in the air immediately |
| **Reference build** **(recommended)** | Avoiding a second purchase cycle while keeping complexity manageable | Laptop, then Orin Nano | Very high | You need a sub-250 g aircraft |
| **Compute-forward** | Multiple cameras, tracking, mapping experiments | Jetson Orin NX | Maximum | You have not yet validated your power, cooling, and field workflow |

## The recommended long-life baseline

<div class="hero-grid" markdown>
<div class="hero-card" markdown>
### Airframe
1.6–2.0 m pusher, fixed wing, accessible fuselage bay, removable wing, space around center of gravity, repairable EPO or composite structure.
</div>
<div class="hero-card" markdown>
### Flight core
H7-class ArduPilot flight controller, GNSS with compass, airspeed sensor provision, high-quality power/current module, RC receiver, buzzer.
</div>
<div class="hero-card" markdown>
### Compute path
Laptop-first vision; reserve a protected mount, fused power branch, UART/USB route, camera harness, and ventilation for an Orin-class companion.
</div>
</div>

!!! tip "A sophisticated aircraft need not run sophisticated software on day one"
    Buy the airframe, power system, flight controller and interface capacity for the later system. Keep the early software behavior deliberately simple.
