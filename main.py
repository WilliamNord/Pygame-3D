import pygame
import sys
import math

pygame.init()
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode(size=(SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("3d")

clock = pygame.time.Clock()

def draw_point(x, y):
    s = 10
    pygame.draw.rect(
        surface=screen,
        color=(0,0,0),
        rect=(round(x - s / 2), round(y - s / 2), s, s)
    )

def draw_line(p1, p2):
    start_x, start_y = p1
    end_x, end_y = p2
    pygame.draw.line(surface=screen, color=(255,0,0), start_pos=(start_x, start_y), end_pos=(end_x, end_y), width=5)
    


def screen_coords(x, y) -> tuple[float, float]:
    screen_x = (x + 1) / 2 * SCREEN_WIDTH
    screen_y = (1 - y) / 2 * SCREEN_HEIGHT
    return screen_x, screen_y

def clear():
    screen.fill((255,255,255))
clear()

def project(x, y, z) -> tuple[float, float]:
    """_summary_

    Args:
        x (float): x-kooridnat
        y (float): y-kooridnat
        z (float): z-kooridnat
        
    Returns:
        tuple: returnerer x/z og y/z slik at en skjerm kan vise punktet og z betegner distanse
    """
    if z >= 0.01:
        z = z
    else:
        z = 0.01
    projected_x = x/z
    projected_y = y/z
        
    return projected_x, projected_y

#for å rotere rundt Y må vi endre X og Z
def rotate_XZ(x, y, z, vinkel) -> tuple[float, float, float]:
    c = math.cos(vinkel)
    s = math.sin(vinkel)
    rx = x*c + z*s
    ry = y
    rz = -x*s + z*c
    return rx, ry, rz + 2 #+2 bare så den roterer litt lenge unna skjermen

points = [
    [ 0.5,  0.5, 0.5],
    [-0.5,  0.5, 0.5],
    [-0.5, -0.5, 0.5],
    [ 0.5, -0.5, 0.5],
    
    [ 0.5,  0.5, -0.5],
    [-0.5,  0.5, -0.5],
    [-0.5, -0.5, -0.5],
    [ 0.5, -0.5, -0.5],
    
    [0, 0.5, 0], 
    [0, 1, 0]
]

#noen av linjene tegnes to ganger som 0 til 1, 0 til 3 osv.
faces = [
    [0, 1, 2, 3], # forside
    [4, 5, 6, 7], # bakside
    [0, 1, 5, 4], # topp
    [3, 2, 6, 7], # bunn
    [0, 3, 7, 4], # høyre side
    [1, 2, 6, 5], # venstre side    
    
]

delta_z = 0
vinkel = 0

running = True
while running == True:
    #ta vekk clear() for å tegne veigen av nodene 
    clear()
    delta_t = clock.tick(FPS) / 1000
    vinkel += 0.5*math.pi * delta_t
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
            
    
    for x, y, z in points:
        delta_z += 0.1 * delta_t
        
        # "*" pakker opp tulples slik at neste funksjon får riktige sett med argumenter
        draw_point(*screen_coords(*project(*rotate_XZ(x, y, z, vinkel))))
    
    for face in faces:
        for i in range(len(face)):
            a = points[face[i]]
            b = points[face[(i + 1) % len(face) ]]
            draw_line(
                p1 = (screen_coords(*project(*rotate_XZ(a[0], a[1], a[2], vinkel)))),
                p2 = (screen_coords(*project(*rotate_XZ(b[0], b[1], b[2], vinkel))))
            )
    draw_line(
        p1=screen_coords(*project(*rotate_XZ(points[-1][0], points[-1][1], points[-1][2], vinkel))),
        p2= screen_coords(*project(*rotate_XZ(points[-2][0], points[-2][1], points[-2][2], vinkel)))
        )
    # pygame.draw.line(surface=screen, color=(0,0,0), start_pos=(0,0), end_pos=(600,600))
    pygame.display.flip()
    
    