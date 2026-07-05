# Safety, legal, and ethics

!!! warning "This is not legal advice"
    Drone rules depend on operating location, aircraft mass/class, site, airspace, radio configuration and operation type. Confirm the current national requirements before every project phase.

## EU/Germany framing

For EASA Open-category operations, VLOS requirements apply, and the remote pilot needs a way to intervene. EASA distinguishes **automatic** operations—predefined routes with a pilot able to intervene—from **autonomous** operation, where the pilot cannot intervene; the latter is not allowed in the Open category. See official sources in [References](../appendix/references.md).

For a German operation, use the Luftfahrt-Bundesamt’s current information for pilot competency and operator obligations. Requirements for privately built aircraft can depend on the operational category and weight.

## Operational ethics

- Test only in a suitable, permitted area with an established recovery plan.
- Avoid collecting identifiable imagery of people and private property.
- Do not use models to track people, vehicles on public roads, or wildlife as a hobby experiment.
- Keep a flight log, risk note and configuration version for every autonomous test.
- Stop tests when the environment changes: spectators, wind, poor GNSS, low light, low battery, or uncertain link quality.

## Mandatory project constraints

```text
Human pilot can intervene at all times.
Vehicle remains within the limits of the operating category and site permission.
Vision loss, video loss, companion crash and model error do not remove basic flight safety.
No unreviewed code update is flown.
Every flight has a defined abort / RTL / landing plan.
```
