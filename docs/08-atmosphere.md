# The Standard Atmosphere and Airspeed Terminology

## The International Standard Atmosphere (ISA)

Aerodynamic performance varies drastically depending on the properties of the air mass an aircraft is flying through. To provide a common reference for aircraft design, performance testing, and calibration of flight instruments, engineers use the **International Standard Atmosphere (ISA)**.

*   **Purpose:** The ISA is a hypothetical, idealized model of the Earth's atmosphere. It assumes a linear temperature lapse rate and calculates corresponding changes in pressure and density with altitude.
*   **Sea-Level Standard Values:** In the ISA model, mean sea level (MSL) conditions are defined as:
    *   **Temperature:** 15.0 °C (288.15 K)
    *   **Pressure:** 101,325 Pa (29.92 inHg or 1013.25 mb)
    *   **Density:** 1.225 kg/m³
*   Simulation environments and aerodynamic calculators use the ISA as the default atmospheric baseline.

## Fundamental Air Properties

The physical properties of the air directly influence the generation of aerodynamic forces (lift and drag) and engine performance.

*   **Air Density ($
ho$):** The mass of air per unit volume. Density is the most critical atmospheric variable in aerodynamics. It decreases significantly as altitude increases or temperature increases. Lower density means less lift generated at a given speed, reduced engine power, and decreased propeller efficiency.
*   **Viscosity ($\mu$):** The internal friction of a fluid, or its resistance to gradual deformation by shear stress. In aerodynamics, air viscosity is responsible for the creation of the boundary layer and skin friction drag. Unlike liquids, the viscosity of a gas (like air) *increases* as its temperature increases.
*   **Compressibility:** At low speeds (below Mach 0.3), air behaves essentially like an incompressible fluid (density remains constant). At higher speeds, the air compresses as it strikes the aircraft, altering the flow physics and requiring complex corrections.

## Types of Airspeed

The speed of an aircraft can be measured and expressed in several different ways, each serving a distinct operational or navigational purpose.

*   **Indicated Airspeed (IAS):** The raw, uncorrected speed read directly from the aircraft's airspeed indicator, driven by the dynamic pressure from the pitot-static system. Flight manuals, stall speeds, and structural limit speeds are always referenced in IAS because it directly reflects the dynamic pressure acting on the airframe, regardless of altitude.
*   **Calibrated Airspeed (CAS):** Indicated airspeed corrected for instrument errors and position errors (inaccuracies caused by the physical placement of the static ports on the airframe).
*   **Equivalent Airspeed (EAS):** Calibrated airspeed corrected for the compressibility of air at high speeds. For most subsonic light aircraft and small UAVs, CAS and EAS are essentially identical.
*   **True Airspeed (TAS):** Equivalent airspeed corrected for non-standard air density (variations in altitude and temperature). TAS is the actual, physical speed of the aircraft moving through the surrounding air mass. It is the primary speed used for flight planning and navigation algorithms.
*   **Ground Speed (GS):** True airspeed corrected for the effect of wind. If a UAV has a TAS of 20 m/s and is flying directly into a 5 m/s headwind, its Ground Speed is 15 m/s.