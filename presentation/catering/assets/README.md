# Kitchen assets

The kitchen backgrounds and the earlier chef reference were generated with
OpenAI's image-generation tool on 17 October 2026. They are illustrations;
none is a screenshot of a real kitchen or an optimization result.

| Asset | Use |
|---|---|
| `kitchen-empty-v3.png` | Runtime background, 1536 × 1024, rendered at 384 × 256 |
| `kitchen-pixel-v2.png` | Earlier background retained as the source for the empty-room edit |
| `chef-pixel-v1.png` | Transparent 1254 × 1254 reference; not used at runtime |

`chef-sprites.js` draws the runtime cooks as native 16 × 24 animation frames.
`kitchen-props.js` draws ingredients, pots, flames, cleaning and packed food
from the checked replay state. Worker routes illustrate the schedule; walking
time is not an optimized or measured constraint.

The empty-room edit removed baked-in food and flames so idle equipment does
not appear active. Earlier generation prompts and editing notes are retained
in this file's Git history at commit `3aff00bd`.

Fonts and the Axion mark have separate notices in
[the branding directory](../../assets/branding/README.md).
