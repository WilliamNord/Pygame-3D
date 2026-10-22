"""
Bad Apple!! tegnet med wireframe-epler.

Du trenger:
    pip install pygame opencv-python numpy

Legg videofilen ved siden av dette skriptet og kall den bad_apple.mp4
(eller endre VIDEO under). For lyd, hent ut lydsporet med:
    ffmpeg -i bad_apple.mp4 -vn bad_apple.ogg
"""
import math
import os
import sys
import time

import cv2
import numpy as np
import pygame

# ---------- Innstillinger ----------
VIDEO = "bad_apple.mp4"
LYD = "bad_apple.ogg"        # valgfri, spilles bare hvis filen finnes
GRID_W = 32                  # antall epler bortover (4:3 som videoen)
GRID_H = 24                  # antall epler nedover
INVERT = False               # True = epler der videoen er hvit i stedet for svart
TERSKEL = 128                # lysstyrke (0-255) som skiller svart fra hvit
Z = 3.0                      # avstand til eplene
BG = (255, 255, 255)
LINJE_FARGE = (200, 0, 0)
STILK_FARGE = (90, 55, 15)

pygame.init()
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bad Apple")
clock = pygame.time.Clock()

if not os.path.exists(VIDEO):
    print(f"Fant ikke {VIDEO}. Legg videofilen i samme mappe som skriptet.")
    sys.exit(1)

cap = cv2.VideoCapture(VIDEO)
video_fps = cap.get(cv2.CAP_PROP_FPS) or 30


# ---------- Eple-modell (lav oppløsning så det går fort) ----------
N_BREDDE = 6
N_LENGDE = 8


def radius(t):
    return math.sin(t) * (0.55 + 0.08 * math.cos(t))


def hoyde(t):
    h = 0.5 * math.cos(t)
    h -= 0.30 * math.exp(-(t / 0.45) ** 2)
    h += 0.10 * math.exp(-((math.pi - t) / 0.45) ** 2)
    return h


modell = []
for i in range(N_BREDDE + 1):
    t = math.pi * i / N_BREDDE
    for j in range(N_LENGDE):
        v = 2 * math.pi * j / N_LENGDE
        modell.append([radius(t) * math.cos(v), hoyde(t), radius(t) * math.sin(v)])
# to ekstra punkt på slutten = stilken
modell.append([0.0, hoyde(0), 0.0])
modell.append([0.08, 0.50, 0.0])
modell = np.array(modell)

# tipp eplet litt (rotasjon rundt X) slik at vi ser ned i fordypningen
tilt = -0.45
ct, st = math.cos(tilt), math.sin(tilt)
modell = np.stack([
    modell[:, 0],
    modell[:, 1] * ct - modell[:, 2] * st,
    modell[:, 1] * st + modell[:, 2] * ct,
], axis=1)

N_GRID_PUNKT = (N_BREDDE + 1) * N_LENGDE

# ---------- Geometri for rutenettet ----------
CELLE = 2 / GRID_H                   # cellestørrelse i skjermkoordinater
SKALA_EPLE = CELLE * Z / 1.15        # så eplet fyller cellen
PIKSLER_PER_ENHET = SCREEN_HEIGHT / 2


def tegn_epler(mask, t):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return

    # midtpunkt for hvert eple i verdenen
    cx = (xs + 0.5 - GRID_W / 2) * CELLE * Z
    cy = (GRID_H / 2 - (ys + 0.5)) * CELLE * Z

    # hvert eple roterer litt forskjøvet, så det blir en bølge over bildet
    vinkel = t * 2.0 + (xs + ys) * 0.35
    c = np.cos(vinkel)[:, None]
    s = np.sin(vinkel)[:, None]

    px = modell[:, 0][None, :] * SKALA_EPLE
    py = modell[:, 1][None, :] * SKALA_EPLE
    pz = modell[:, 2][None, :] * SKALA_EPLE

    # rotasjon rundt Y for alle epler på en gang
    rx = px * c + pz * s + cx[:, None]
    ry = py + cy[:, None]
    rz = -px * s + pz * c + Z

    rz = np.maximum(rz, 0.01)
    sx = SCREEN_WIDTH / 2 + rx / rz * PIKSLER_PER_ENHET
    sy = SCREEN_HEIGHT / 2 - ry / rz * PIKSLER_PER_ENHET
    pts = np.stack([sx, sy], axis=2)   # (antall epler, punkter, 2)

    for p in pts:
        g = p[:N_GRID_PUNKT].reshape(N_BREDDE + 1, N_LENGDE, 2)
        for i in range(1, N_BREDDE):                    # ringer rundt eplet
            pygame.draw.lines(screen, LINJE_FARGE, True, g[i], 1)
        for j in range(N_LENGDE):                       # topp til bunn
            pygame.draw.lines(screen, LINJE_FARGE, False, g[:, j], 1)
        pygame.draw.line(screen, STILK_FARGE, p[N_GRID_PUNKT], p[N_GRID_PUNKT + 1], 2)


def start_lyd():
    if os.path.exists(LYD):
        pygame.mixer.music.load(LYD)
        pygame.mixer.music.play()


start_lyd()
start = time.time()
frame_nr = -1
mask = np.zeros((GRID_H, GRID_W), dtype=bool)

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

    nå = time.time() - start

    # les frem til riktig videoframe (hopper over frames hvis vi henger etter)
    ny_frame = None
    mål = int(nå * video_fps)
    while frame_nr < mål:
        ok, frame = cap.read()
        if not ok:
            # videoen er ferdig: start på nytt
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            start_lyd()
            start = time.time()
            frame_nr = -1
            ny_frame = None
            break
        frame_nr += 1
        ny_frame = frame

    if ny_frame is not None:
        grå = cv2.cvtColor(ny_frame, cv2.COLOR_BGR2GRAY)
        liten = cv2.resize(grå, (GRID_W, GRID_H), interpolation=cv2.INTER_AREA)
        mask = (liten > TERSKEL) if INVERT else (liten < TERSKEL)

    screen.fill(BG)
    tegn_epler(mask, nå)
    pygame.display.flip()