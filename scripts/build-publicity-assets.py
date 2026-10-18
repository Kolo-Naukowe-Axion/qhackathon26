"""Build the post-hackathon thumbnail from existing project art and fonts.

Requires Pillow. Does not modify submitted media or experiment evidence.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / 'presentation/assets/branding'
image = Image.new('RGB', (1280, 720), '#142b22')
draw = ImageDraw.Draw(image)
cream, mint, gold = '#f5e2b8', '#bdd49a', '#deb568'
# Actual kitchen capture, cropped to equipment and crew rather than tiny UI text.
scene = Image.open(ROOT / 'docs/assets/axion-kitchen.jpg').convert('RGB')
scene = ImageOps.fit(scene.crop((440, 205, 1330, 1000)), (626, 608), method=Image.Resampling.NEAREST)
image.paste(scene, (600, 54))
draw.rectangle((595, 49, 1231, 667), outline=gold, width=5)
draw.rectangle((20, 20, 1260, 700), outline='#6a8050', width=2)
font = lambda size: ImageFont.truetype(str(BRAND / 'space-grotesk-bold.ttf'), size)
body = lambda size: ImageFont.truetype(str(BRAND / 'manrope-semibold.ttf'), size)
mark = Image.open(BRAND / 'axion-logo.png').convert('RGBA')
mark.thumbnail((40, 52))
# Recolor the alpha silhouette for a dark background.
mask = ImageOps.invert(mark.convert('L')) if mark.getextrema()[3] == (255, 255) else mark.getchannel('A')
image.paste(Image.new('RGB', mark.size, cream), (58, 62), mask)
draw.text((113, 75), 'TEAM AXION', font=body(22), fill=mint)
draw.text((54, 148), 'AXION', font=font(104), fill=cream)
draw.text((54, 248), 'KITCHEN', font=font(104), fill=mint)
draw.text((60, 384), 'Quantum optimization.', font=body(28), fill=cream)
draw.text((60, 426), 'Catering production.', font=body(27), fill=cream)
draw.rectangle((60, 505, 536, 606), fill=gold)
draw.text((82, 511), 'WINNER', font=font(49), fill='#243728')
draw.text((84, 568), 'QPOLAND 2026 · MAIN PRIZE', font=body(18), fill='#243728')
draw.text((60, 640), 'QAOA  /  VQE  /  VeloxQ', font=body(23), fill=mint)
image.save(BRAND / 'axion-kitchen-winner.jpg', quality=95, subsampling=0)
print(BRAND / 'axion-kitchen-winner.jpg')
