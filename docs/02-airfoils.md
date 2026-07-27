# Airfoil Terminology and Aerodynamic Characteristics

## Airfoil Geometry and Terminology

An airfoil is the cross-sectional shape of a wing, blade, or sail designed to generate lift. Understanding its basic geometry is essential for analyzing flight mechanics.

*   **Leading Edge (LE) and Trailing Edge (TE):** The forward-most point of the airfoil is the leading edge, while the sharp, rearmost point is the trailing edge.
*   **Chord Line (c):** A straight geometric line connecting the leading edge directly to the trailing edge. The chord length is the fundamental reference for aerodynamic measurements.
*   **Mean Camber Line:** A curve drawn halfway between the upper and lower surfaces of the airfoil. It defines the curvature of the wing.
*   **Maximum Thickness and Camber:** Thickness is the maximum distance between the upper and lower surfaces, while maximum camber is the maximum distance between the mean camber line and the chord line. These parameters significantly dictate the airfoil's lift and drag profile.

## Angle of Attack (AoA) and Pressure Distribution

*   **Angle of Attack (α):** The acute angle formed between the airfoil's chord line and the direction of the freestream relative wind. It is the primary pilot-controlled (or autopilot-controlled) variable determining lift generation.
*   **Pressure Distribution:** As the Angle of Attack changes, the pressure distribution around the airfoil shifts. At positive angles, a low-pressure region forms over the upper surface, creating an upward suction force. The peak of this low-pressure area moves forward toward the leading edge as the AoA increases, continuously altering the total lift vector.

## The Lift-Curve and Stall Phenomenon

The relationship between the Coefficient of Lift (CL) and the Angle of Attack (α) is one of the most critical concepts in aerodynamics, defining the operational limits of an aircraft.

*   **Linear Region:** For small angles of attack, the lift coefficient increases linearly with the angle of attack. The slope of this line is the lift-curve slope.
*   **Critical Angle of Attack and Maximum Lift (CL_max):** As AoA continues to increase, the adverse pressure gradient on the upper surface becomes stronger. The lift curve begins to flatten until it reaches its absolute peak, known as CL_max, which corresponds to the critical angle of attack.
*   **Stall:** Immediately after exceeding the critical angle of attack, the boundary layer lacks the kinetic energy to remain attached to the upper surface. The flow separates, causing a dramatic, sudden loss of lift and a sharp increase in drag. This is defined as an aerodynamic stall.

## Effects of Camber and Thickness

The physical shape of the airfoil directly dictates its aerodynamic performance across different flight regimes.

*   **Symmetrical vs. Cambered Airfoils:** Symmetrical airfoils have identical upper and lower surfaces (zero camber), meaning they generate zero lift at a zero degree Angle of Attack. Cambered airfoils are asymmetrical, generating positive lift even at a zero degree AoA, which is highly advantageous for increasing the payload capacity of fixed-wing configurations.
*   **Thickness Effects:** Thicker airfoils generally offer higher maximum lift coefficients and more gradual stall characteristics, making them predictable. Thinner airfoils produce less drag at high speeds but typically exhibit sharper, more abrupt stall behaviors.

## High-Lift Devices: Flaps and Slats

To safely operate at lower speeds without stalling, the airfoil's geometry is temporarily altered using high-lift devices.

*   **Trailing Edge Flaps:** Deployed downward from the trailing edge, flaps effectively increase both the camber and the chord line of the airfoil. This significantly increases the maximum lift coefficient, albeit with a substantial drag penalty.
*   **Leading Edge Slats:** Deployed from the front of the wing, slats open a physical gap that channels high-energy air from the lower surface into the upper surface's boundary layer. This delays flow separation, allowing the airfoil to reach a much higher critical angle of attack before stalling.

## The Three Aerodynamic Centers

Understanding where aerodynamic forces act on an airfoil is crucial for structural design and longitudinal static stability, especially when defining the physical parameters of an aircraft in simulation environments.

*   **Center of Pressure (CP):** The specific point on the chord line where the total resultant aerodynamic force (lift and drag) acts. Crucially, the CP moves forward as the Angle of Attack increases and moves aft as it decreases, creating varying pitching moments.
*   **Aerodynamic Center (AC):** A fixed reference point (typically located at 25% of the chord length, or the quarter-chord point, for subsonic flight) where the aerodynamic pitching moment remains constant, regardless of changes in the Angle of Attack. Engineers use the AC as the primary invariant reference for stability calculations.
*   **Center of Gravity (CG):** While a property of the entire airframe rather than just the airfoil, the CG's position relative to the Aerodynamic Center dictates static stability. For a conventionally stable configuration, the aircraft's CG must be located forward of its overall Aerodynamic Center.