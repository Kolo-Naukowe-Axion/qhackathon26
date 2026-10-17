# Pixel kitchen art

Created with the built-in image generation tool, 17 October 2026. The retained
assets are `kitchen-empty-v3.png` (1536 × 1024 runtime environment),
`kitchen-pixel-v2.png` (earlier 1536 × 1024 source) and `chef-pixel-v1.png`
(1254 × 1254 transparent reference, no longer used at runtime). The game renders
the room at **384 × 256**. Animated cooks are now native **16 × 24** frames drawn
by `chef-sprites.js`, with four directions, separate limb poses and task-specific
work frames. No paid CLI/API
workflow was used. Original transparency is preserved in the earlier character
source file.

## Earlier background prompt

The input was the earlier, more detailed generated kitchen. It was simplified
using this exact edit prompt:

> Use case: style-transfer. Simplify this game environment dramatically into an authentic LOW RESOLUTION cozy 16-bit game screen. Keep the same overall kitchen layout and the same four workstations in the same locations: two cookers at upper left-center and upper right-center, chopping counter middle left, packing counter middle right, clear center aisle, bottom center doorway. But redraw the whole image as if its true native game resolution were ONLY 384 by 256 pixels, then enlarged 4x with nearest-neighbor. Every visible pixel should be a chunky 4x4 square in the output, NO tiny detailed pixel noise. Limited palette around 24 warm colors, simple large color clusters, flat readable objects, basic 1 or 2 pixel shading, dark brown pixel outlines. A cozy indie kitchen game blending Stardew Valley and Overcooked, with small 16x24-pixel scale props. Much less environmental detail: remove the distant village and windmill, use a simple grass backdrop with a few trees and flowers; remove most wall trinkets and most plants. Simple cream and terracotta floor tiles, timber walls, sage tiles, plain cooker counters with single big pots, one chopping board with a few green vegetables, one packing bench with a few square trays. Keep the room large and open with clear flat floor areas for moving game characters. No characters, no baked smoke, no baked flames, no text, no labels, no UI. NOT high-resolution digital painting, NOT antialiased, not polished miniature dollhouse. The desired effect is a simple low-res game asset with big readable pixels and restrained detail.

The earlier output included decorative hearth flames despite the prompt. It is
retained as source art only. The runtime uses the empty environment below.

## Empty environment edit

The built-in image generation tool edited `kitchen-pixel-v2.png` into
`kitchen-empty-v3.png` on 17 October 2026. Prompt specification:

> Use case: precise-object-edit. Preserve this exact 1536 × 1024 kitchen, camera, native 384 × 256 pixel scale, furniture geometry, positions, palette and scenery. Remove both pots and their contents. Make the stove tops and hearths unlit, with no baked fire or glow. Remove the chopping board, knife and on-top vegetables from the left island. Remove all on-top food, trays and boxes from the right island. Remove the boxes from the cart. Preserve furniture, under-bench stock, plants and pantry scenery. No new props, characters, text or UI. Keep native low-resolution pixels and the exact layout.

`kitchen-props.js` now draws the stateful layer at 384 × 256: prep ingredients,
waiting bowls, cooking pots, flames and steam, packing trays, dirty pots/soap,
and packed crates awaiting departure. It restores the empty background before
each replay frame. Pots and flames cannot persist into idle station state.

## Chef prompt

> Use case: stylized-concept. Asset type: transparent animated-game character base sprite. Create ONE original adorable pixel-art chef for a cozy catering kitchen game blending Stardew Valley's detailed 16-bit pixel art and Overcooked's big-headed expressive cooks. Full-body character facing camera, slightly top-down three-quarter game camera, feet visible, oversized tall white chef hat, friendly focused face, white double-breasted chef jacket, deep forest-green apron, dark brown trousers, little dark boots. Warm caramel skin, brown hair. Subtle asymmetric ready-to-work stance with arms slightly apart, hands empty. Sharp deliberate square pixels with dark pixel outlines and rich tiny shading clusters, no antialiasing or blur, NOT vector, NOT low-poly, not a glossy 3D render. The sprite should be entirely isolated on TRUE transparent background, centered with little padding, roughly square image containing one tall character. No floor, NO shadow, no background, no kitchen, NO text or lettering, no props, no UI, no multiple characters, no sprite sheet. It will be placed as a moving game character over a separately made warm pixel-art kitchen.

The generated standing sprite above was replaced after movement feedback.
The game assigns worker identity with apron colors and name badges. Native
walking frames alternate feet and arms; work frames face the countertop and use
a knife, tray, spoon or cloth. Routes follow the centre aisle; travel is still an
illustration, not measured travel time. The four recorded plan references and
their objective values are retained.
