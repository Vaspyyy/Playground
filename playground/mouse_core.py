"""Bounded, time-based Mouse Magic simulation, independent of GTK and KWin."""
from collections import deque
import math
import random

DEFAULTS = dict(enabled=False, ribbon=True, dust=True, ripples=True, field=True,
                idle=True, fullscreen=True, motion=45, density=45, brightness=75,
                reaction='swirl')
PRESETS = {
    'Fairy garden': dict(ribbon=False, dust=True, ripples=True, field=True, motion=30, density=45, reaction='attract'),
    'Comet': dict(ribbon=True, dust=True, ripples=True, field=False, motion=70, density=35, reaction='scatter'),
    'Quiet orbit': dict(ribbon=False, dust=False, ripples=True, field=True, motion=18, density=20, reaction='swirl'),
    'Everything': dict(ribbon=True, dust=True, ripples=True, field=True, motion=85, density=85, reaction='swirl'),
}


def normalize(raw):
    result = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return result
    for key, value in DEFAULTS.items():
        candidate = raw.get(key)
        if type(value) is bool and type(candidate) is bool:
            result[key] = candidate
        elif type(value) is int and type(candidate) in (int, float) and math.isfinite(candidate):
            result[key] = max(0, min(100, candidate))
    if raw.get('reaction') in ('swirl', 'scatter', 'attract'):
        result['reaction'] = raw['reaction']
    return result


class World:
    def __init__(self, seed=1):
        self.rng = random.Random(seed)
        self.trail = deque(maxlen=100)
        self.dust = deque(maxlen=350)
        self.ripples = deque(maxlen=32)
        self.field = []
        self.cursor = None
        self.last_move = 0
        self.bounds = []

    def reset(self, bounds=None):
        self.trail.clear()
        self.dust.clear()
        self.ripples.clear()
        self.field.clear()
        self.cursor = None
        if bounds is not None:
            self.bounds = list(bounds)

    def pointer(self, x, y, pressed, now, settings):
        previous = self.cursor
        self.cursor = (x, y)
        moved = previous is None or math.hypot(x-previous[0], y-previous[1]) > .4
        if moved:
            self.last_move = now
            # Teleporting between distant outputs must not draw a line across the desktop.
            if previous and math.hypot(x-previous[0], y-previous[1]) > 500:
                self.trail.clear()
            self.trail.append((x, y, now))
            if settings['dust']:
                for _ in range(1+int(settings['density']/25)):
                    angle = self.rng.random()*math.tau
                    speed = 15+self.rng.random()*(25+settings['motion'])
                    self.dust.append([x, y, math.cos(angle)*speed, math.sin(angle)*speed,
                                      now, self.rng.random()])
        if pressed and settings['ripples']:
            self.ripples.append((x, y, now))

    def step(self, now, dt, settings):
        dt = max(0, min(dt, .05))
        lifetime = .3+settings['motion']/120
        while self.trail and now-self.trail[0][2] > lifetime:
            self.trail.popleft()
        while self.dust and now-self.dust[0][4] > 1.2:
            self.dust.popleft()
        while self.ripples and now-self.ripples[0][2] > .9:
            self.ripples.popleft()
        for p in self.dust:
            p[0] += p[2]*dt
            p[1] += p[3]*dt
            p[3] += 12*dt
        count = (12+int(settings['density']*1.1))*len(self.bounds) if settings['field'] else 0
        self.field = self.field[:count]
        while len(self.field) < count:
            index = len(self.field)%len(self.bounds)
            x, y, w, h = self.bounds[index]
            self.field.append([x+self.rng.random()*w, y+self.rng.random()*h, 0., 0., self.rng.random(), index])
        if not self.cursor:
            return
        cx, cy = self.cursor
        force = .25+settings['motion']/60
        for p in self.field:
            dx, dy = p[0]-cx, p[1]-cy
            distance = max(8, math.hypot(dx, dy))
            ax, ay = math.sin(now+p[4]*20)*5, math.cos(now*.7+p[4]*20)*5
            if distance < 200:
                strength = (1-distance/200)*330*force
                ux, uy = dx/distance, dy/distance
                if settings['reaction'] == 'scatter':
                    ax += ux*strength; ay += uy*strength
                elif settings['reaction'] == 'attract':
                    ax -= ux*strength; ay -= uy*strength
                else:
                    radial = (60-distance)/100
                    ax += (-uy+ux*radial)*strength
                    ay += (ux+uy*radial)*strength
            damping = math.exp(-2.5*dt)
            p[2] = (p[2]+ax*dt)*damping
            p[3] = (p[3]+ay*dt)*damping
            p[0] += p[2]*dt; p[1] += p[3]*dt
            x, y, w, h = self.bounds[p[5]]
            p[0] = x+(p[0]-x)%max(1,w)
            p[1] = y+(p[1]-y)%max(1,h)

    def draw(self, cr, now, settings, palette):
        from render import color, dot
        alpha = settings['brightness']/100
        motion = settings['motion']/100
        if settings['field']:
            for x,y,vx,vy,hue,index in self.field:
                dot(cr,x,y,4+motion*3,color(palette,hue+now*.025),alpha*.55)
        if settings['ribbon'] and len(self.trail)>1:
            points = list(self.trail)
            lifetime = .3+settings['motion']/120
            for i in range(1,len(points)):
                x,y,born = points[i]
                fade = max(0,1-(now-born)/lifetime)
                rgb = color(palette,i/len(points)*.7+now*.15)
                for spread, opacity in ((3,.07),(1.7,.2),(1,.8)):
                    cr.set_source_rgba(*rgb,alpha*fade*opacity)
                    cr.set_line_width((2+motion*9)*fade*spread)
                    cr.set_line_cap(1)
                    cr.move_to(*points[i-1][:2]);cr.line_to(x,y);cr.stroke()
        if settings['dust']:
            for x,y,vx,vy,born,hue in self.dust:
                fade = max(0,1-(now-born)/1.2)
                dot(cr,x,y,(3+motion*5)*fade,color(palette,hue+now*.08),alpha*fade)
        if settings['ripples']:
            for x,y,born in self.ripples:
                age = (now-born)/.9
                radius = 5+(45+motion*80)*(1-(1-age)**2)
                for width, opacity in ((10,.06),(5,.16),(1.8,.8)):
                    cr.set_source_rgba(*color(palette,born*.17),alpha*(1-age)**2*opacity)
                    cr.set_line_width(width)
                    cr.arc(x,y,radius,0,math.tau);cr.stroke()
        if settings['idle'] and self.cursor:
            x,y = self.cursor
            idle = min(1,max(0,now-self.last_move-.15)*2)
            dot(cr,x,y,13+motion*10,color(palette,now*.1),alpha*(.15+.2*idle))
            for i in range(7):
                angle = i*math.tau/7+now*(.5+motion)
                radius = 10+(4+8*motion)*math.sin(now*.8+i)
                dot(cr,x+math.cos(angle)*radius,y+math.sin(angle)*radius,3.5,
                    color(palette,i/7+now*.08),alpha*idle*.7)
