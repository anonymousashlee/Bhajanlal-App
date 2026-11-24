import re
from collections import OrderedDict

RAW = """1. 3D Vector & Quaternion Math: Calculate smooth rotations, offsets, and look-at targets without gimbal lock.
2. Spring-Arm & Boom Systems: Push the camera forward automatically so walls and buildings never block the player.
3. Damping & Interpolation (Lerp/Slerp): Smooth out sudden jumps when characters turn or accelerate.
4. Field of View (FOV) Scaling: Widen the FOV dynamically at high driving speeds to create a sense of velocity.
5. Camera Collision & Sphere Casting: Detect tight alleys, ceilings, and corners cleanly.
6. Look-Ahead & Lead Offset: Shift the camera ahead of the car or runner so players see incoming turns.
7. Target Lock-On & Soft-Lock: Frame enemies smoothly during gunfights without disorienting the player.
8. Over-the-Shoulder Aiming: Transition cleanly from wide exploration framing to tight combat aiming.
9. Multi-Mode Camera Blending: Blend effortlessly between on-foot, car, motorcycle, boat, and helicopter cameras.
10. Input & Deadzone Tuning: Make mouse and analog stick camera rotation feel responsive and natural.
11. Speed-Based Distance Pullback: Pull the camera back as vehicles hit top speed.
12. Drift & Turn Banking: Tilt and swing the camera slightly during sharp turns and handbrake drifts.
13. Airborne & Stunt Jump Framing: Track cars smoothly through mid-air ramps and landings.
14. Reverse & Rear-View Switching: Snap to rear-facing angles instantly during police chases.
15. Cinematic Hood & Bumper Cams: Tune close-up driving perspectives without clipping through vehicle meshes.
16. Aircraft & Helicopter Orbiting: Handle 360-degree pitch and roll without flipping or disorienting the player.
17. Boat & Water Bobbing Compensation: Filter out rapid wave jitter so ocean driving stays readable.
18. Impact & Crash Camera Recoil: Jolt the camera proportionally when colliding with traffic or walls.
19. Weapon Recoil & Kickback: Add subtle camera pitch and shake per shot fired.
20. Sniper & Scope Zooming: Adjust sensitivity, FOV, and depth of field when using scoped weapons.
21. Rule of Thirds & Composition: Place characters, vehicles, and landmarks for strong visual balance.
22. Shot Size & Focal Length Selection: Choose wide, medium, and close-up lenses to match story tension.
23. Camera Cuts & Continuity (180-Degree Rule): Keep spatial geography clear during dialogue and action cuts.
24. Spline & Dolly Track Animation: Move cameras along smooth curves for mission intros and city flyovers.
25. Handheld & Perlin Noise Shake: Add subtle organic motion so cutscenes feel alive rather than robotic.
26. Slow-Motion & Bullet-Time Cameras: Sync time dilation with dramatic camera orbits during stunts or takedowns.
27. Focus Pulling (Depth of Field): Shift sharpness from foreground speakers to background threats.
28. Framing & Sightline Guidance: Point the camera subtly toward mission objectives or incoming enemies.
29. Camera Occlusion Fading: Fade out foreground trees, fences, or pedestrians that block the view.
30. Aspect Ratio & Letterboxing: Transition into cinematic widescreen bars during story scenes.
31. Cinemachine / Sequencer Mastery: Build modular virtual cameras and cutscene timelines in Unity or Unreal.
32. Camera State Machines: Prioritize and blend dozens of active camera states without conflicts.
33. Frustum Culling Awareness: Understand what the camera sees to optimize rendering performance.
34. Near & Far Clipping Plane Tuning: Prevent close geometry clipping and distant z-fighting.
35. Motion Sickness Prevention: Avoid unnatural roll, erratic zoom, and frame-rate-dependent camera jitter.
36. Multi-Monitor & Ultrawide Support: Keep horizontal and vertical FOV consistent across screen ratios.
37. Photo Mode & Free-Cam Tools: Build debug and player cameras with pause, roll, and filter controls.
38. Audio Listener Placement: Balance camera vs. character audio positioning for realistic 3D sound.
39. Split-Screen & Picture-in-Picture: Render secondary camera feeds for scopes, mirrors, or co-op views.
40. Camera Debugging Gizmos: Visualize camera rails, collision spheres, and look targets in-editor.
41. Procedural Screen Shake Systems: Build trauma-based shake that decays smoothly after explosions.
42. Hit-Stop & Micro-Freeze Sync: Pair brief impact pauses with tight camera punches.
43. Idle & Breathing Motion: Add gentle camera sway when standing still.
44. Slope & Stair Smoothing: Prevent vertical camera jitter when running up stairs or curbs.
45. Interior-to-Exterior Transitions: Adjust camera distance and FOV cleanly when entering tight buildings.
46. Auto-Centering & Assist Logic: Gently recenter the camera behind vehicles while respecting manual input.
47. Target Framing Constraints: Keep both the player and tall helicopters or buildings inside the frame.
48. Timeline Event Triggering: Fire sound, VFX, and dialogue cues directly from camera animation tracks.
49. Playtesting Camera Readability: Spot blind spots during fast chases and chaotic shootouts.
50. Reference Study (Film & Games): Analyze 1980s crime cinema and open-world action games for shot ideas.
51. Particle System Architecture (Niagara / VFX Graph): Build GPU-accelerated emitters for high particle counts.
52. Emitter Timing & Burst Control: Layer core flash, secondary sparks, and lingering smoke cleanly.
53. Velocity, Drag & Gravity Curves: Make debris, sparks, and water droplets arc realistically.
54. Flipbook & Sprite Sheet Animation: Animate fire, explosions, and smoke using multi-frame textures.
55. Sub-UV Blending & Motion Vectors: Smooth low-frame-rate smoke animations without visible popping.
56. Color-over-Life & Alpha Curves: Transition fire from bright white-yellow to orange, red, and dark smoke.
57. Size-over-Life & Stretch Alignment: Stretch sparks and rain streaks along their movement direction.
58. Particle Collisions & Bouncing: Make shell casings, glass shards, and sparks bounce off streets.
59. Soft Particles & Depth Fade: Eliminate harsh clipping lines where smoke meets walls or floors.
60. GPU Instancing & Mesh Particles: Spawn 3D debris chunks, shells, and shattered parts efficiently.
61. Muzzle Flashes & Smoke Puffs: Create distinct silhouettes for pistols, shotguns, SMGs, and rifles.
62. Bullet Tracers & Air Trails: Give gunfire clear visual readability across city streets.
63. Surface-Specific Bullet Impacts: Differentiate concrete dust, metal sparks, wood splinters, and water splashes.
64. Multi-Stage Explosion Design: Combine shockwaves, fireballs, shrapnel, scorch decals, and rising smoke plumes.
65. Vehicle Fire & Engine Damage: Escalate radiator steam into dark smoke and open hood flames.
66. Glass Shattering & Debris: Spawn falling glass shards and window frame effects on impact.
67. Melee & Impact Sparks/Dust: Add punchy visual feedback to close-quarters combat.
68. Flame & Molotov Spreading: Simulate burning puddles, heat distortion, and rising embers.
69. Blood & Hit Feedback Effects: Balance visceral combat feedback with target age-rating guidelines.
70. Decal Projection Systems: Leave tire marks, bullet holes, burn craters, and oil spills on surfaces.
71. Tire Smoke & Burnout Plumes: Spawn dense, lingering smoke during drifts and hard launches.
72. Skid Marks & Ribbon Trails: Generate continuous ground trails aligned to wheel contact points.
73. Exhaust Backfire & Nitro Flames: Trigger blue/orange exhaust pops during gear shifts and boosts.
74. Water Wakes, Boat Foam & Splashes: Simulate hull wakes, propeller foam, and coastal waves.
75. Dynamic Rain & Puddle Ripples: Layer falling rain streaks, splash rings, and wet street reflections.
76. Volumetric Fog & Light Shafts: Create hazy sunsets, streetlights, and club spotlights.
77. Neon Glow & Emissive Signage: Craft vibrant 1980s-style neon signs with subtle flicker and bloom.
78. Atmospheric Dust, Leaves & Trash: Add blowing palm leaves, street papers, and dust motes for life.
79. Helicopter Rotor Wash: Push ground dust, water spray, and foliage outward beneath low aircraft.
80. Fire Hydrant & Destructible Prop FX: Create gushing water jets and electrical transformer sparks.
81. Node-Based Shader Graphs: Build custom materials for water, glass, neon, and dissolve effects.
82. UV Panning & Texture Distortion: Animate flowing water, fire licking, and heat haze cheaply.
83. Fresnel & Rim Lighting Effects: Highlight vehicle curves, water edges, and forcefields.
84. Screen-Space Reflections & Wetness: Make asphalt glisten after tropical rainstorms.
85. Post-Processing Stacks: Tune bloom, color grading, vignette, and chromatic aberration.
86. Retro 1980s Color Grading & LUTs: Nail warm pastel sunsets and high-contrast neon nights.
87. Heat Haze & Shockwave Refraction: Bend background pixels behind jet exhausts and explosions.
88. Motion Blur & Speed Lines: Reinforce extreme driving velocity without smearing the HUD.
89. Outline & Interaction Highlights: Make pickups, weapons, and mission markers stand out cleanly.
90. Vertex Animation Shaders: Sway palm trees, flags, and ocean waves on the GPU.
91. Overdraw & Transparency Optimization: Prevent stacked smoke layers from tanking frame rates.
92. VFX LODs & Distance Culling: Simplify or disable distant particle effects across the city.
93. Object Pooling for Effects: Reuse explosion and bullet impact instances instead of spawning garbage.
94. Lighting Integration with VFX: Add brief dynamic point lights to muzzle flashes and explosions.
95. Texture Packing (RGBA Channels): Store masks, noise, and gradients in single textures to save memory.
96. Procedural Noise Generation: Create Perlin, Voronoi, and curl noise in Substance Designer or shaders.
97. Dissolve & Spawn Shaders: Smoothly fade out destroyed debris and wrecked vehicles.
98. VFX Timing & Anticipation: Give big explosions or hazards a split-second windup cue.
99. Readability vs. Visual Clutter: Keep intense gunfights and explosions exciting without blinding the player.
100. Audio-Visual Synchronization: Lock every spark, thunderclap, and explosion flash to its sound effect."""

def slug(title):
    t = title.split(":")[0].strip().lower()
    t = re.sub(r"[^a-z0-9]+","-",t).strip("-")
    return t

def pillar_for(n):
    if n <= 10: return "Camera: Core Mechanics"
    if n <= 20: return "Camera: Vehicle & Action"
    if n <= 30: return "Camera: Cinematic Framing"
    if n <= 40: return "Camera: Technical & Engine"
    if n <= 50: return "Camera: Polish & Game Feel"
    if n <= 60: return "VFX: Core Particle Systems"
    if n <= 70: return "VFX: Combat, Weapon & Destruction"
    if n <= 80: return "VFX: Vehicle & City Environment"
    if n <= 90: return "VFX: Shaders, Post-Processing & Optimization"
    return "VFX: Technical Art & Polish"

entries = []
seen_ids = set()
for line in RAW.strip().splitlines():
    m = re.match(r"(\d+)\.\s*(.+)", line.strip())
    if not m: continue
    n = int(m.group(1))
    title = m.group(2).strip()
    if ":" in title:
        name_part, desc_part = title.split(":",1)
        name = name_part.strip()
        desc = desc_part.strip()
    else:
        name = title; desc = title
    sid = slug(name)
    if sid in seen_ids:
        sid = f"{sid}-{n}"
    seen_ids.add(sid)
    steps = [
        f"Define the goal and constraints for {name.lower()} in an open-world camera/VFX context.",
        f"Implement the core math/system for {name.lower()} with frame-rate-independent updates.",
        f"Tune parameters and validate against 1980s crime-cinema / open-world action-game references.",
        f"Profile performance and add LOD/culling so the effect stays within frame budget.",
        f"Wire into the camera/VFX pipeline and playtest for readability.",
    ]
    out = f"A production-ready {name.lower()} implementation with tuned params and perf budget."
    desc_final = desc if desc.lower().startswith("use when") else f"Use when {desc.lower()}."
    entries.append((sid, name, desc_final, steps, out, []))

# group by pillar
groups = OrderedDict()
for i,e in enumerate(entries, start=1):
    p = pillar_for(i)
    groups.setdefault(p, []).append(e)

lines = ["# Bhajanlal skill library - List 10: Game Camera Systems & Real-Time VFX (items 1-100)",
         "# Auto-generated from the 100-skill camera/VFX prompt.",
         "# tuple: (id, name, description, steps, output, covers)",
         "",
         "PILLARS = ["]
for p, es in groups.items():
    lines.append(f'    ("{p}", [')
    for (sid,name,desc,steps,out,covers) in es:
        lines.append(f'        ("{sid}",')
        lines.append(f'         {repr(name)},')
        lines.append(f'         {repr(desc)},')
        lines.append("         [")
        for st in steps:
            lines.append(f'            {repr(st)},')
        lines.append("         ],")
        lines.append(f'         {repr(out)},')
        lines.append("         []),")
    lines.append("    ]),")
lines.append("]")

open("/Users/ashleesharma/.config/opencode/skill_build/p15.py","w").write("\n".join(lines)+"\n")
print("wrote p15.py with", len(entries), "skills")
