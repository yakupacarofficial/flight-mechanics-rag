# Flight Performance and Operating Envelopes

## Wing Loading and Stall Speed

Flight performance is fundamentally tied to the physical dimensions and weight of the aircraft. One of the most critical design parameters is **Wing Loading**, which dictates operational speeds and handling.

*   **Wing Loading (W/S):** The ratio of the aircraft's total weight to its total wing area. A high wing loading means the wing must produce a lot of lift per square unit, requiring higher airspeeds to stay aloft. This is common in fast, heavily loaded platforms. Low wing loading allows for slower flight and tighter turns, typical of gliders and long-endurance UAVs.
*   **Stall Speed ($V_{stall}$):** The minimum steady flight speed at which the aircraft can generate enough lift to support its weight. It is directly proportional to the square root of wing loading and inversely proportional to maximum lift coefficient ($C_{Lmax}$) and air density.
    *   Formula: $V_{stall} = \sqrt{rac{2W}{
ho S C_{Lmax}}}$
    *   In mission planning, calculating the correct stall speed is vital when configuring automated landing sequences or accounting for sudden weight changes (such as executing an autonomous payload drop).

## The Lift-to-Drag Ratio (L/D)

The **Lift-to-Drag Ratio (L/D)** is the ultimate measure of an aircraft's aerodynamic efficiency. 

*   It represents how much lift is generated for every unit of drag penalized. 
*   **L/D Max:** The specific angle of attack and corresponding airspeed where the total drag is at its absolute minimum. Flying at $L/D_{max}$ ensures the aircraft is operating at its peak aerodynamic efficiency, which is crucial for maximizing range in propeller-driven aircraft and maximizing glide distance.

## Gliding Flight

In unpowered flight (gliding), the aircraft's thrust is zero, and its weight provides the forward propulsive component as it descends along a glide path.

*   **Glide Angle:** The angle between the horizontal plane and the actual flight path. The minimum glide angle (shallowest descent) is achieved exactly when flying at $L/D_{max}$.
*   **Glide Ratio:** The ratio of horizontal distance traveled to vertical distance lost. Mathematically, the glide ratio is identical to the L/D ratio. An aircraft with an L/D of 15:1 will travel 15 units forward for every 1 unit of altitude lost.

## Climbing Flight

Climbing performance is dictated by the excess thrust or excess power available beyond what is required to maintain level flight.

*   **Angle of Climb (AoC):** Focuses on gaining the maximum altitude over the shortest horizontal distance. It is determined by **Excess Thrust**. This is the critical metric for clearing obstacles immediately after takeoff.
*   **Rate of Climb (RoC):** Focuses on gaining the maximum altitude in the shortest amount of time. It is determined by **Excess Power**. The maximum RoC defines how quickly an aircraft can reach its cruise altitude or operational ceiling.

## Range and Endurance (Breguet Equations)

For autonomous mapping or surveillance missions, accurately predicting how long or how far the platform can fly is paramount.

*   **Endurance:** The maximum amount of time an aircraft can remain airborne on a given amount of fuel or battery capacity. For propeller-driven platforms, maximum endurance requires flying at the airspeed that minimizes power required (which is lower than $V_{md}$).
*   **Range:** The maximum total distance an aircraft can travel. For propeller-driven platforms, maximum range occurs at the $L/D_{max}$ airspeed.
*   **Breguet Range Equation:** A classical analytical formula used to estimate range and endurance. It incorporates aerodynamic efficiency (L/D), propulsive efficiency, specific fuel consumption, and the weight fraction (ratio of initial weight to final empty weight). 

## The V-n Diagram (Maneuver Envelope)

The **V-n Diagram** (Velocity vs. Load Factor) defines the structural and aerodynamic operational limits of an airframe. It establishes the safe flight envelope that flight controllers must respect.

*   **Load Factor (n):** The ratio of the aerodynamic forces acting on the aircraft to its gross weight, often expressed in "G's". In straight and level flight, $n=1$. In a 60-degree banked turn, $n=2$.
*   **Aerodynamic Limit (Stall Region):** The curved left boundary of the diagram. At lower speeds, attempting to pull high G-forces will result in an accelerated stall before structural damage occurs.
*   **Structural Limit ($n_{max}$):** The horizontal top and bottom boundaries. Exceeding these load factors will cause permanent structural deformation or catastrophic failure.
*   **Maneuvering Speed ($V_A$ or Corner Speed):** The intersection of the maximum lift capability curve and the structural limit line. This is the optimal speed for executing maximum-performance maneuvers; full control deflection will stall the aircraft just before exceeding structural G-limits.