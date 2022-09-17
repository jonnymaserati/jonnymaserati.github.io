---
layout: post
title:  "A Case for Automated Well Trajectory Planning (AWTP)"
author: Jonny Corcutt
tags: python well drilling modified machine learning automation engineering visualization
use_math: false
---
![image](/assets/images/2022-09-04-simulated-automated-well-trajectory-planning.png)
Automated well trajectory planning proof of concept for simulated in-fill drilling of an unconventional shale development, with shallow hazard, well-bore instability (inclination constraints), anti-collision (offset wells), lease lines, fracture zone avoidance, dogleg severity and target inclination and azimuth rules and constraints.

## What is AWTP?
Automated well Trajectory Planning (AWTP) is the process of generating well trajectory profiles for a given scenario, while honoring a set of rules and/or constraints. As there are an infinite number of solutions for connecting two points in three dimensional space, post processing of the results is necessary to quickly filter down a set of *best* trajectories.

Note that the definition of *best* is a subjective one, which highlights a major benefit (and perhaps unexpected) benefit - AWTP necessitates communication between project stakeholders in order to discuss and agree on what drives value for their project (what is *best*?), or at least to see the impact that the well trajectory has on the project's value drivers. Typical discussions include DRILLEX versus production - should the well be as cheap as possible (maximize drill-ability) or should more money be spent to optimize production?

AWTP is built upon the [welleng] open-source Python library for constructing well trajectories using minimum curvature methods and applying [ISCWSA] position error models and clearance calculation methods. On top of these, it applies a range of algorithms and machine learning to efficiently and without bias, navigate three-dimensional space and probe for pathways between source and target locations.

### Rules and Constraints
Typically, rules used during the construction phase of the trajectories are used to constrain the results to *viable* solutions, i.e. well trajectories that can feasibly be drilled. Examples of such rules and constraints are:
  - **Dog Leg Severity (DLS) Limits:** for a given hole size or formation, experience may dictate a maximum design DLS. For example, an Electric Submersible Pump is often run at a specific True Vertical Depth (TVD) in an interval with minimal tortuosity, which yields a material benefit on the longevity of the pump. Also, to minimize the sliding intervals when drilling with a bent sub and motor, build and turn sections are often designed with a minimum DLS to encourage fewer and longer hold sections to improve average rates of penetration.
  - **Anti-Collision:** typically, we do not want to collide with existing wells when drilling, so it is advantageous to ensure that the generated wells minimize the risk of collision (by ensuring that the appropriate well uncertainty ellipses do not touch).
  - **Inclination and Azimuth:** for example a maximum inclination through specific mapped formations, like the 25 degrees maximum inclination typically assigned to trajectories drilled through the North Sea Group of formations in the Dutch sector of the North Sea.
  - **Subsurface Hazards:** spatial volumes can be defined and assigned rules/constraints such as avoidance domains (anti-targets) like shallow hazards.

## What is AWTP used for?
  - **Trajectory planning in highly congested environments:** AWTP has been utilized on the Norwegian Continental shelf<sup>[1]</sup>, where manually planning trajectories that avoid collision is increasingly difficult and inefficient using traditional methods.
  - **Slot to target optimization:** AWTP has been utilized in the Middle East for determining the *best* surface locations for given subsurface targets and for optimizing the location of surface facilities.
  - **Subsurface target selection:** AWTP has been utilized in South East Asia for testing combinations of subsurface targets to optimize well placement for wells with multi-zone objectives, often resulting in combinations of targets that had not been considered by the subsurface team.
  - **Trajectory drilling optimization:** AWTP has been used in the Middle East for optimizing complex three-dimensional extended reach trajectories, with post-processing and filtering based upon metrics such as [Modified Tortuosity Index](https://jonnymaserati.github.io/2022/06/19/modified-tortuosity-index-survey-frequency.html).
  - **Feasibility and scoping of wells:** AWTP allows non-wells/drilling (e.g. subsurface) disciplines to scope wells for project feasibility (having worked collaboratively to determine an appropriate set of rules/constraints for the given environment).


## What could AWTP be used for?
  - **Trajectory production optimization:** AWTP can generate a range of viable reservoir section trajectories that can be post-processed in subsurface models to optimize the likely productivity of well - AI methods have been tested for this purpose, but often the trajectories generated are sub-optimal for drilling.
  - **Automated Relief Well Trajectory Planning:** AWTP can be utilized to determine relief well trajectories that offer the highest probability of intersecting the target wellbore at the desired depth and parameters, while avoiding subsurface hazards.
  - **Position uncertainty optimization:** AWTP can be utilized for determining trajectories with the highest likelihood of being landed at the desired subsurface target, taking account of both the well trajectory and subsurface location uncertainties.
  - **Automated Well Design workflows:** AWTP can be used to initiate full-stack automated Well Design work-flows, porting viable trajectories to Well Design software like [Oliasoft] via their Application Programming Interfaces (API) for optimizing e.g. casing seat locations taking account of kick tolerances or more advanced trajectory optimization using torque and drag and hydraulics modules.

## References
[1] [Jon Gustav Vabø; Evan Thomas Delaney; Tom Savel; Norbert Dolle, "Novel Application of Artificial Intelligence with Potential to Transform Well Planning Workflows on the Norwegian Continental Shelf." Paper presented at the SPE Annual Technical Conference and Exhibition, Dubai, UAE, September 2021. https://doi.org/10.2118/206339-MS](https://doi.org/10.2118/206339-MS)

[welleng]: https://github.com/jonnymaserati/welleng
[ISCWSA]: https://www.iscwsa.net/
[Oliasoft]: https://oliasoft.com
