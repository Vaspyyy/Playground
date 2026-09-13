"""Cairo rainbow glow. The central region remains completely transparent."""
import colorsys
import math
import random
try:
    import cairo
except ImportError:
    import cairocffi as cairo


def draw_glow(cr, width, height, spread, phase, opacity, palette='rainbow'):
    if opacity <= 0 or width <= 0 or height <= 0:
        return
    spread = min(spread, width / 2, height / 2)
    perimeter = 2 * (width + height)
    # Clockwise edge coordinates, with local y pointing toward the centre.
    sides = [(0, 0, 0, width, 0),
             (width, 0, 1, height, width),
             (width, height, 2, width, width + height),
             (0, height, 3, height, 2 * width + height)]
    for x, y, rotation, length, offset in sides:
        cr.save()
        cr.translate(x, y)
        cr.rotate(rotation * 3.141592653589793 / 2)
        # Partition corners diagonally so adjacent glows never double in brightness.
        cr.move_to(0, 0)
        cr.line_to(length, 0)
        cr.line_to(length - spread, spread)
        cr.line_to(spread, spread)
        cr.close_path()
        cr.clip()
        rainbow = cairo.LinearGradient(0, 0, length, 0)
        for i in range(49):
            t = i / 48
            hue = ((offset + t * length) / perimeter - phase) % 1
            r, g, b = color(palette, hue)
            rainbow.add_color_stop_rgb(t, r, g, b)
        fade = cairo.LinearGradient(0, 0, 0, spread)
        for position, alpha in [(0, 1), (0.05, .94), (.18, .60), (.40, .24), (.7, .055), (1, 0)]:
            fade.add_color_stop_rgba(position, 1, 1, 1, alpha * opacity)
        cr.set_source(rainbow)
        cr.mask(fade)
        cr.restore()


PALETTE_COLORS = {
    'aurora': ['36ffbb', '31cfec', '8071ff', 'd961f3'],
    'fire': ['ff371c', 'ff8a17', 'ffe269', 'ff5228'],
    'ice': ['528eff', '85eaff', 'efffff', '53c4f7'],
    'candy': ['ff62ca', 'bc7fff', '7dd9ff', 'ffd1ed'],
    'sunset': ['ffb15a', 'ff6488', 'b363e6', '6144ba'],
}


def color(palette, position):
    if palette not in PALETTE_COLORS:
        return colorsys.hsv_to_rgb(position % 1, .90, 1)
    stops = PALETTE_COLORS[palette]
    position = (position % 1) * len(stops)
    i, fraction = int(position), position % 1
    a, b = stops[i], stops[(i + 1) % len(stops)]
    return tuple((int(a[j:j+2], 16) * (1-fraction) + int(b[j:j+2], 16) * fraction) / 255
                 for j in (0, 2, 4))


def perimeter_point(t, width, height, inset=0):
    # Each edge gets one quarter of the timeline, regardless of aspect ratio.
    # This synchronizes corner crossings on differently shaped monitors.
    w, h = max(1, width - 2*inset), max(1, height - 2*inset)
    q = (t % 1) * 4
    if q < 1:
        return inset + q*w, inset
    if q < 2:
        return width-inset, inset + (q-1)*h
    if q < 3:
        return width-inset-(q-2)*w, height-inset
    return inset, height-inset-(q-3)*h


def dot(cr, x, y, radius, rgb, alpha):
    if alpha <= 0 or radius <= 0:
        return
    gradient = cairo.RadialGradient(x, y, 0, x, y, radius)
    gradient.add_color_stop_rgba(0, *rgb, alpha)
    gradient.add_color_stop_rgba(.22, *rgb, alpha*.85)
    gradient.add_color_stop_rgba(.52, *rgb, alpha*.28)
    gradient.add_color_stop_rgba(1, *rgb, 0)
    cr.set_source(gradient)
    cr.rectangle(x-radius, y-radius, radius*2, radius*2)
    cr.fill()


def draw_effect(cr, width, height, settings, effect, elapsed, opacity=1, seed=0):
    if opacity <= 0:
        return
    spread = min(settings['width'], min(width, height)/4)
    strength = opacity * settings['brightness']/100
    chaos = settings['chaos']/100
    phase = elapsed * settings['speed']
    palette = settings['palette']
    if effect == 'classic':
        draw_glow(cr, width, height, spread, phase, strength, palette)
        return
    draw_glow(cr, width, height, spread*.65, phase, strength*.12, palette)
    cr.save()
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    if effect == 'comets':
        count = 2 + int(chaos*5)
        tail_length = .045 + chaos*.11
        for comet in range(count):
            head = phase + comet/count
            for j in range(44):
                fraction = j/43
                pos = head - tail_length*(1-fraction)
                x, y = perimeter_point(pos, width, height, 3+spread*.10)
                dot(cr, x, y, spread*(.18+.30*fraction),
                    color(palette, pos), strength*fraction*fraction*.55)
            x, y = perimeter_point(head, width, height, 3+spread*.10)
            dot(cr, x, y, spread*.25, (1, 1, 1), strength)
    elif effect == 'sparks':
        rng = random.Random(seed)
        count = 60 + int(chaos*160)
        for i in range(count):
            origin, offset, drift, size = [rng.random() for _ in range(4)]
            age = (elapsed*(.6+settings['speed']*2) + offset) % 1
            travel = spread*(.35+chaos*2.6)*age
            travel = min(travel, min(width, height)*.30)
            pos = origin + (drift-.5)*age*.045*(1+chaos)
            x, y = perimeter_point(pos, width, height, 2+travel)
            alpha = math.sin(math.pi*age)**1.2 * strength
            radius = (2+size*4)*(1+chaos)
            rgb = color(palette, origin-phase*.3)
            dot(cr, x, y, radius*2.3, rgb, alpha*.65)
            cr.set_source_rgba(*rgb, alpha)
            cr.arc(x, y, max(.6, radius*.24), 0, math.tau)
            cr.fill()
    elif effect == 'waves':
        for ribbon in range(2+int(chaos*2)):
            for edge in range(4):
                points = []
                for j in range(49):
                    t = (edge + j/48)/4
                    oscillation = .5+.5*math.sin(t*math.tau*(4+int(chaos*5))-phase*math.tau*2+ribbon*1.8)
                    inset = 3 + spread*(.1 + oscillation*(.25+chaos*.85)+ribbon*.12)
                    points.append(perimeter_point(t, width, height, inset))
                # One connected path per edge prevents bright dots at segment joins.
                for line_width, alpha in [(spread*.36, .06), (spread*.15, .18), (2+chaos*2, .8)]:
                    gradient = cairo.LinearGradient(*points[0], *points[-1])
                    for j in range(17):
                        rgb = color(palette, (edge+j/16)/4-phase+ribbon*.12)
                        gradient.add_color_stop_rgba(j/16, *rgb, strength*alpha)
                    cr.set_source(gradient)
                    cr.set_line_width(line_width)
                    cr.move_to(*points[0])
                    for point in points[1:]:
                        cr.line_to(*point)
                    cr.stroke()
    cr.restore()
