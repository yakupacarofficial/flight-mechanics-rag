# Finite Wing Aerodynamics and 3D Flow

## Wing Geometry and Macroscopic Parameters

While airfoils describe a 2D cross-section, practical flight involves a finite 3D wing. The macroscopic geometry of the wing dictates the overall aerodynamic efficiency and handling qualities.

*   **Aspect Ratio (AR):** The ratio of the wing's span to its mean chord, calculated as $AR = b^2 / S$ (where $b$ is wingspan and $S$ is wing area). High aspect ratio wings (often seen on long-endurance fixed-wing UAVs) are highly efficient and produce less induced drag. Low aspect ratio wings offer better maneuverability and structural strength.
*   **Taper Ratio (λ):** The ratio of the tip chord to the root chord. A tapered wing reduces weight at the extremities and improves the spanwise lift distribution, approximating the ideal elliptical lift distribution.
*   **Mean Aerodynamic Chord (MAC):** The chord of an equivalent rectangular wing that produces the same aerodynamic forces and moments as the actual wing. Accurately mapping the MAC is essential for defining the Center of Gravity (CG) limits and precisely configuring aerodynamic coefficients in simulation environments like Gazebo or X-Plane.
*   **Sweep Angle:** The angle between the wing's lateral axis and a line drawn along the 25% chord line. While primarily used for delaying drag divergence in transonic flight, slight sweep can also enhance lateral stability.
*   **Wing Twist (Washout):** A structural design where the geometric angle of attack at the wingtip is lower than at the root. This ensures that the wing root stalls before the tip, maintaining aileron effectiveness and preventing uncommanded roll during a stall.

## 3D Flow and Wingtip Vortices

A finite wing operates differently than an infinite 2D airfoil due to the physical boundaries at the wingtips, which introduce complex 3D flow phenomena.

*   **Spanwise Flow:** The high-pressure air under the wing naturally seeks the low-pressure area above it. At the wingtips, this air spills upward and inward over the edge, creating a spanwise flow rather than a purely chordwise flow.
*   **Wingtip Vortices:** The convergence of the spanwise flows from the upper and lower surfaces at the trailing edge creates powerful, spiraling masses of air known as wingtip vortices. 
*   **Downwash and Induced Drag:** These vortices alter the local relative wind over the wing, deflecting it downward (downwash). This alters the effective angle of attack and tilts the total lift vector backward. The rearward component of this tilted lift vector is a drag penalty known as **Induced Drag**. Induced drag is most severe at high angles of attack and low airspeeds.

## Aerodynamic Devices: Winglets and Vortex Generators

Engineers employ specific aerodynamic modifications to control boundary layer behavior and mitigate the negative effects of 3D flow.

*   **Winglets:** Vertical or angled extensions placed at the wingtips designed to restrict the immediate mixing of high and low-pressure air. By diffusing the strength of wingtip vortices, winglets effectively reduce induced drag and increase the effective aspect ratio of the wing without physically extending the wingspan.
*   **Vortex Generators (VGs):** Small, fin-like structures placed along the upper surface of the wing, typically near the leading edge. They intentionally create miniature, controlled vortices that draw high-energy freestream air down into the slow-moving boundary layer. This re-energized boundary layer strongly resists flow separation, increasing the critical angle of attack and delaying stall conditions.

## Ground Effect

When an aircraft operates within a distance from the ground roughly equal to its wingspan, its aerodynamic characteristics shift dramatically due to a phenomenon called **Ground Effect**.

*   **Vortex Interruption:** The proximity to the solid ground surface physically restricts the downward expansion and formation of wingtip vortices. 
*   **Aerodynamic Consequences:** Because the vortices are suppressed, the downwash angle is significantly reduced, leading to a sharp decrease in induced drag and a corresponding increase in effective lift. An aircraft entering ground effect during a landing flare will often experience a "floating" tendency, requiring precise energy management to touch down properly.