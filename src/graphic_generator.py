"""Local, model-free editorial graphic renderer with genuinely different compositions."""
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont
import math, re

STYLES = ["Editorial Magazine", "Photojournalism", "Breaking News", "Technology & Data", "Minimal Report", "Illustrated Feature"]

PALETTES = {
    "Editorial Magazine": ((246, 242, 232), (232, 224, 207), (27, 49, 54), (54, 125, 112), (205, 105, 82)),
    "Photojournalism": ((14, 30, 39), (21, 59, 68), (20, 44, 53), (71, 163, 148), (244, 190, 103)),
    "Breaking News": ((37, 20, 27), (92, 25, 39), (48, 20, 28), (205, 49, 60), (255, 205, 102)),
    "Technology & Data": ((10, 23, 40), (22, 43, 72), (13, 30, 53), (44, 135, 153), (109, 231, 224)),
    "Minimal Report": ((248, 248, 245), (231, 234, 231), (31, 38, 40), (85, 101, 99), (25, 125, 105)),
    "Illustrated Feature": ((19, 43, 49), (30, 83, 82), (20, 53, 58), (79, 171, 147), (238, 177, 111)),
}


def _font(size, bold=False):
    candidates = [
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    ]
    for path in candidates:
        try: return ImageFont.truetype(path, size)
        except OSError: pass
    return ImageFont.load_default()


def _wrap(draw, text, font, width):
    words = str(text or '').split()
    lines, line = [], ''
    for word in words:
        candidate = f'{line} {word}'.strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            line = candidate
        else:
            if line: lines.append(line)
            # Break an individual long token instead of overflowing the canvas.
            line = word
            while draw.textbbox((0, 0), line, font=font)[2] > width and len(line) > 1:
                cut = max(1, len(line) // 2)
                while cut > 1 and draw.textbbox((0, 0), line[:cut] + '-', font=font)[2] > width: cut -= 1
                lines.append(line[:cut] + '-')
                line = line[cut:]
    if line: lines.append(line)
    return lines or ['']


def _gradient(size, top, bottom):
    w, h = size
    im = Image.new('RGB', size)
    draw = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(round(top[i] * (1-t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, w, y), fill=c)
    return im


def _motif(draw, style, w, h, margin, accent, secondary):
    # Original locally drawn editorial motifs; no model or external image is used.
    if style == 'Technology & Data':
        step = max(28, w // 24)
        for x in range(0, w, step): draw.line((x, 0, x, h), fill='#1d3851', width=1)
        for y in range(0, h, step): draw.line((0, y, w, y), fill='#1d3851', width=1)
        cx, cy = int(w*.79), int(h*.22)
        for r in (int(w*.06), int(w*.10), int(w*.14)):
            draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=accent, width=max(2, w//540))
        for i in range(5):
            x1 = int(w*.66) + i*int(w*.035)
            draw.line((x1, int(h*.36), x1, int(h*.36)-int(h*(.05 + (i%3)*.035))), fill=secondary, width=max(3,w//300))
    elif style == 'Breaking News':
        draw.polygon([(int(w*.62),0),(w,0),(w,int(h*.28))], fill=secondary)
        draw.rectangle((0,int(h*.74),w,int(h*.755)), fill=accent)
        for i in range(5):
            x = int(w*.70)+i*int(w*.06)
            draw.line((x,int(h*.06),x+int(w*.09),int(h*.15)),fill=accent,width=max(2,w//500))
    elif style == 'Minimal Report':
        draw.rectangle((0,0,max(8,w//45),h), fill=accent)
        draw.ellipse((int(w*.83),int(h*.06),int(w*.93),int(h*.16)), outline=secondary, width=max(2,w//400))
    elif style == 'Illustrated Feature':
        # layered landscape/orbit shapes that give this style a distinct illustrated identity
        draw.ellipse((int(w*.68),-int(h*.08),int(w*1.05),int(h*.25)), fill=secondary)
        draw.ellipse((int(w*.74),int(h*.03),int(w*.99),int(h*.22)), fill=accent)
        draw.polygon([(int(w*.55),int(h*.43)),(int(w*.76),int(h*.23)),(int(w*.98),int(h*.43))], fill='#386d68')
        draw.polygon([(int(w*.53),int(h*.48)),(int(w*.78),int(h*.31)),(w,int(h*.48))], fill='#244d54')
        for i in range(7):
            x=int(w*.65)+i*int(w*.035); y=int(h*.53)+(i%2)*int(h*.025)
            draw.ellipse((x,y,x+max(4,w//180),y+max(4,w//180)),fill=secondary)
    elif style == 'Photojournalism':
        # Graphic editorial framing, rather than pretending to have a photograph.
        draw.rectangle((int(w*.65),0,w,int(h*.38)), fill=secondary)
        draw.polygon([(int(w*.63),int(h*.38)),(int(w*.83),int(h*.15)),(w,int(h*.38))], fill='#39766f')
        draw.ellipse((int(w*.79),int(h*.05),int(w*.92),int(h*.18)), fill=accent)
    else:  # Editorial Magazine
        draw.ellipse((int(w*.72),-int(h*.13),int(w*1.08),int(h*.22)), fill=secondary)
        draw.ellipse((int(w*.82),-int(h*.07),int(w*1.02),int(h*.13)), fill=accent)


def make_graphic(headline, summary, publisher='News source', published_date='', source_url='', status='INSUFFICIENT_EVIDENCE', output_path='output/newspilot.png', size=(1080,1350), style='Editorial Magazine'):
    """Render a high-resolution PNG. Supported styles and canvas dimensions are model-free."""
    if style not in PALETTES: style = 'Editorial Magazine'
    w, h = int(size[0]), int(size[1])
    if w < 320 or h < 320 or w > 4000 or h > 4000: raise ValueError('Canvas dimensions must be between 320 and 4000 pixels.')
    top, bottom, dark, secondary, accent = PALETTES[style]
    im = _gradient((w,h), top, bottom)
    d = ImageDraw.Draw(im)
    margin = int(min(w,h)*.075)
    _motif(d, style, w, h, margin, '#' + '%02x%02x%02x' % accent, '#' + '%02x%02x%02x' % secondary)
    light = style in ('Editorial Magazine','Minimal Report')
    ink = '#1f3034' if light else '#f5f7f4'
    muted = '#52676a' if light else '#c1d5d8'
    accent_hex = '#%02x%02x%02x' % accent
    panel = '#fffaf0' if style == 'Editorial Magazine' else ('#f5f6f2' if style == 'Minimal Report' else '#172f3a')
    # Content panel is offset/size-aware and uses a different layout per style.
    top_y = int(h*.12) if style != 'Breaking News' else int(h*.10)
    panel_y = int(h*.17)
    panel_bottom = int(h*.83)
    if style == 'Photojournalism':
        # Image-led feeling created from original geometric illustration; clearly local artwork.
        hero_box = (margin, int(h*.10), w-margin, int(h*.42))
        d.rounded_rectangle(hero_box, radius=int(min(w,h)*.025), fill='#244b55', outline='#477d7c', width=max(2,w//500))
        # Fill the hero panel with a deliberate, locally rendered editorial illustration.
        # This avoids an empty image placeholder when no licensed/source image is available.
        hx0, hy0, hx1, hy1 = hero_box
        hero_w, hero_h = hx1-hx0, hy1-hy0
        # Soft grid and circuit traces add depth without pretending to be a real photograph.
        grid = '#315d65'
        for gx in range(hx0 + int(hero_w*.06), hx1, max(24, int(w*.045))):
            d.line((gx, hy0+int(hero_h*.10), gx, hy1-int(hero_h*.10)), fill=grid, width=max(1,w//1200))
        for gy in range(hy0 + int(hero_h*.18), hy1, max(24, int(h*.045))):
            d.line((hx0+int(hero_w*.04), gy, hx1-int(hero_w*.04), gy), fill=grid, width=max(1,w//1200))
        # Network nodes and connecting paths on the left give the illustration a focal point.
        nodes = [(.13,.34),(.25,.22),(.30,.57),(.43,.34),(.48,.70),(.18,.72),(.56,.52)]
        links = [(0,1),(0,2),(1,3),(2,3),(2,5),(3,4),(3,6),(4,6),(5,4)]
        pts = [(hx0+int(hero_w*x), hy0+int(hero_h*y)) for x,y in nodes]
        for a,b in links:
            d.line((*pts[a], *pts[b]), fill='#4aa99b', width=max(2,w//420))
        for i,(nx,ny) in enumerate(pts):
            r = max(5, int(w*(.009 if i in (1,3,6) else .006)))
            d.ellipse((nx-r,ny-r,nx+r,ny+r), fill=accent_hex if i in (1,3) else '#65bdb0', outline='#d8f0e8', width=max(1,w//900))
        # A simple shield outline communicates security/verification; it is original vector art.
        sx, sy = hx0+int(hero_w*.30), hy0+int(hero_h*.25)
        sw, sh = int(hero_w*.18), int(hero_h*.47)
        shield = [(sx,sy),(sx+sw//2,sy-int(sh*.10)),(sx+sw,sy),(sx+int(sw*.92),sy+int(sh*.52)),(sx+sw//2,sy+sh),(sx+int(sw*.08),sy+int(sh*.52))]
        d.line(shield+[shield[0]], fill='#f5f7f4', width=max(2,w//380), joint='curve')
        d.line((sx+int(sw*.28),sy+int(sh*.43),sx+int(sw*.44),sy+int(sh*.59),sx+int(sw*.73),sy+int(sh*.30)), fill=accent_hex, width=max(3,w//300), joint='curve')
        # Keep the existing sun/landscape accent on the right side.
        d.ellipse((int(w*.68),int(h*.13),int(w*.84),int(h*.32)), fill=accent_hex)
        d.polygon([(int(w*.47),int(h*.42)),(int(w*.69),int(h*.22)),(int(w*.87),int(h*.42))],fill='#39766f')
        panel_y = int(h*.47)
    elif style == 'Breaking News':
        d.rounded_rectangle((margin, panel_y, w-margin, panel_bottom), radius=int(min(w,h)*.02), fill=panel, outline=accent_hex, width=max(2,w//500))
    elif style == 'Technology & Data':
        d.rounded_rectangle((margin, panel_y, w-margin, panel_bottom), radius=int(min(w,h)*.02), fill=panel, outline='#2d627b', width=max(2,w//500))
    elif style == 'Minimal Report':
        d.rectangle((margin, panel_y, w-margin, panel_bottom), fill=panel)
    else:
        d.rounded_rectangle((margin, panel_y, w-margin, panel_bottom), radius=int(min(w,h)*.02), fill=panel, outline='#526b70' if not light else '#d6d0c3', width=max(1,w//900))
    pad = int(min(w,h)*.055)
    content_x = margin + pad
    content_w = w - 2*(margin+pad)
    label_font = _font(max(13,int(w*.018)), True)
    meta_font = _font(max(12,int(w*.014)))
    d.text((margin, int(h*.045)), 'NEWSPILOT   /   NEWS INTELLIGENCE', font=label_font, fill=ink)
    d.line((margin,int(h*.085),w-margin,int(h*.085)), fill=accent_hex, width=max(2,w//500))
    tag_y = panel_y + pad
    d.rounded_rectangle((content_x,tag_y,content_x+int(content_w*.40),tag_y+int(h*.035)),radius=int(min(w,h)*.012),fill=secondary)
    d.text((content_x+int(w*.012),tag_y+int(h*.007)), 'LATEST COVERAGE', font=meta_font, fill='#ffffff' if not light else '#ffffff')
    title_y = tag_y + int(h*.065)
    # Adapt font size to available height and width.
    title_size = int(min(w*.052, h*.075))
    max_title_height = int(h*(.24 if style == 'Photojournalism' else .29))
    while title_size > 18:
        title_font = _font(title_size, True)
        title_lines = _wrap(d, headline, title_font, content_w)
        line_height = int(title_size*1.18)
        if len(title_lines)*line_height <= max_title_height: break
        title_size -= max(1, int(w/600))
    for line in title_lines:
        if title_y + line_height > panel_bottom - int(h*.12): break
        d.text((content_x,title_y),line,font=title_font,fill=ink)
        title_y += line_height
    title_y += int(h*.018)
    d.rounded_rectangle((content_x,title_y,content_x+int(w*.11),title_y+max(3,int(w*.005)),),radius=2,fill=accent_hex)
    body_y = title_y + int(h*.04)
    body_font_size = max(15,int(min(w*.023,h*.026)))
    body_font = _font(body_font_size)
    body_lines = _wrap(d, summary or 'Additional article detail was not available in the collected source metadata.', body_font, content_w)
    max_body_lines = max(2, int(h*.14 / max(1, body_font_size*1.4)))
    for line in body_lines[:max_body_lines]:
        if body_y + body_font_size*1.4 > panel_bottom - int(h*.07): break
        d.text((content_x,body_y),line,font=body_font,fill=muted)
        body_y += int(body_font_size*1.4)
    # Source coverage is explicitly not a truth verdict.
    status_y = max(body_y+int(h*.025), int(h*.68))
    status_y = min(status_y, panel_bottom-int(h*.105))
    d.text((content_x,status_y),'SOURCE COVERAGE',font=meta_font,fill=muted)
    d.text((content_x,status_y+int(h*.027)),str(status).replace('_',' ').title(),font=_font(max(15,int(w*.022)),True),fill=accent_hex)
    footer_y = int(h*.88)
    d.line((margin,footer_y-int(h*.018),w-margin,footer_y-int(h*.018)),fill=secondary,width=max(1,w//700))
    footer = f'{publisher or "News source"}  •  {published_date or "Date unavailable"}'
    d.text((margin,footer_y),footer[:120],font=meta_font,fill=ink)
    domain = urlparse(source_url).hostname or ''
    domain = domain.removeprefix('www.')
    d.text((margin,footer_y+int(h*.028)),domain[:100] or 'Review the original report for details',font=meta_font,fill=accent_hex)
    out = Path(output_path); out.parent.mkdir(parents=True,exist_ok=True)
    im.save(out,'PNG',optimize=True)
    return out
