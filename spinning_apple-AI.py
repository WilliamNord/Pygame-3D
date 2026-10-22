import pygame
import sys
import math
import random

pygame.init()
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("3d epler")

clock = pygame.time.Clock()

ANTALL_EPLER = 10
random.seed()  # bruk random.seed(1) hvis du vil ha samme plassering hver gang


def draw_point(x, y, s=3, color=(0, 0, 0)):
    pygame.draw.rect(
        surface=screen,
        color=color,
        rect=(round(x - s / 2), round(y - s / 2), s, s)
    )


def draw_line(p1, p2, color=(255, 0, 0), width=2):
    pygame.draw.line(surface=screen, color=color, start_pos=p1, end_pos=p2, width=width)


def screen_coords(x, y) -> tuple[float, float]:
    screen_x = (x + 1) / 2 * SCREEN_WIDTH
    screen_y = (1 - y) / 2 * SCREEN_HEIGHT
    return screen_x, screen_y


def clear():
    screen.fill((255, 255, 255))


def project(x, y, z) -> tuple[float, float]:
    if z < 0.01:
        z = 0.01
    return x / z, y / z


def rotate_X(x, y, z, vinkel) -> tuple[float, float, float]:
    c = math.cos(vinkel)
    s = math.sin(vinkel)
    return x, y * c - z * s, y * s + z * c


def rotate_Y(x, y, z, vinkel) -> tuple[float, float, float]:
    c = math.cos(vinkel)
    s = math.sin(vinkel)
    return x * c + z * s, y, -x * s + z * c


# ---------- Eple-modellen (lages bare én gang og deles av alle epler) ----------
N_BREDDE = 12
N_LENGDE = 14


def radius(t):
    return math.sin(t) * (0.55 + 0.08 * math.cos(t))


def hoyde(t):
    h = 0.5 * math.cos(t)
    h -= 0.30 * math.exp(-(t / 0.45) ** 2)
    h += 0.10 * math.exp(-((math.pi - t) / 0.45) ** 2)
    return h


points = []
for i in range(N_BREDDE + 1):
    t = math.pi * i / N_BREDDE
    r = radius(t)
    y = hoyde(t)
    for j in range(N_LENGDE):
        v = 2 * math.pi * j / N_LENGDE
        points.append([r * math.cos(v), y, r * math.sin(v)])


def idx(i, j):
    return i * N_LENGDE + (j % N_LENGDE)


lines = []
for i in range(N_BREDDE + 1):
    for j in range(N_LENGDE):
        lines.append((idx(i, j), idx(i, j + 1)))
        if i < N_BREDDE:
            lines.append((idx(i, j), idx(i + 1, j)))

stem = [
    [0.00, hoyde(0), 0.0],
    [0.01, 0.28, 0.0],
    [0.04, 0.42, 0.0],
    [0.09, 0.52, 0.0],
]


# ---------- Mange epler ----------
class Eple:
    def __init__(self, sx, sy, z):
        # sx, sy er posisjon på skjermen (-1 til 1), z er dybde
        self.x = sx * z   # ganger z så eplet havner på riktig sted etter projeksjon
        self.y = sy * z
        self.z = z
        self.skala = random.uniform(0.8, 1.2)
        self.vinkel = random.uniform(0, 2 * math.pi)
        self.fart = random.uniform(0.3, 1.2) * random.choice([-1, 1])
        self.tilt = random.uniform(-0.8, -0.2)

    def oppdater(self, delta_t):
        self.vinkel += self.fart * delta_t

    def transform(self, p):
        x, y, z = p[0] * self.skala, p[1] * self.skala, p[2] * self.skala
        x, y, z = rotate_X(x, y, z, self.tilt)
        x, y, z = rotate_Y(x, y, z, self.vinkel)
        # flytt eplet til sin plass i verdenen
        x, y, z = x + self.x, y + self.y, z + self.z
        return screen_coords(*project(x, y, z))

    def tegn(self):
        # lenger unna = lysere farge
        dybde = (self.z - 2.5) / 2.5          # 0 (nær) til 1 (langt unna)
        dybde = max(0, min(1, dybde))
        linje_farge = (255, round(190 * dybde), round(190 * dybde))
        punkt_farge = (round(120 * dybde),) * 3

        sp = [self.transform(p) for p in points]
        for a, b in lines:
            draw_line(sp[a], sp[b], color=linje_farge)
        for p in sp:
            draw_point(*p, color=punkt_farge)

        st = [self.transform(p) for p in stem]
        stilk_farge = (110 + round(100 * dybde), 70 + round(110 * dybde), 20 + round(120 * dybde))
        for k in range(len(st) - 1):
            draw_line(st[k], st[k + 1], color=stilk_farge, width=4)


def lag_epler(antall):
    epler = []
    forsok = 0
    while len(epler) < antall and forsok < 1000:
        forsok += 1
        sx = random.uniform(-0.8, 0.8)
        sy = random.uniform(-0.8, 0.8)
        z = random.uniform(2.5, 5.0)
        # ikke la eplene havne oppå hverandre på skjermen
        for e in epler:
            if math.hypot(sx - e.x / e.z, sy - e.y / e.z) < 0.4:
                break
        else:
            epler.append(Eple(sx, sy, z))
    # tegn de lengst unna først
    epler.sort(key=lambda e: -e.z)
    return epler


epler = lag_epler(ANTALL_EPLER)

running = True
while running:
    clear()
    delta_t = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            epler = lag_epler(ANTALL_EPLER)  # mellomrom = nye epler

    for eple in epler:
        eple.oppdater(delta_t)
        eple.tegn()

    pygame.display.flip()