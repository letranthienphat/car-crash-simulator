import streamlit as st
import numpy as np
import time
import math
import random
from PIL import Image

st.set_page_config(layout="wide")

# ===== SETTINGS =====
W, H = 512, 512
TILE = 32
MAP_W, MAP_H = 64, 64

# ===== CITY MAP =====
# 0 grass, 1 road, 2 building types
map_data = np.zeros((MAP_H, MAP_W), dtype=int)

# road grid
for y in range(MAP_H):
    for x in range(MAP_W):
        if x % 8 == 0 or y % 8 == 0:
            map_data[y, x] = 1
        elif random.random() < 0.25:
            map_data[y, x] = random.choice([2,3,4])  # 3 types buildings

# ===== PLAYER =====
player = {"x": MAP_W*TILE//2, "y": MAP_H*TILE//2, "vx":0, "vy":0, "a":0}

# ===== AI CARS =====
ai = []
for i in range(15):
    ai.append({"x":random.randint(0,MAP_W*TILE),
               "y":random.randint(0,MAP_H*TILE),
               "vx":0,"vy":0})

# ===== PARTICLES =====
particles = []

def spawn_particles(x,y):
    for _ in range(40):
        particles.append({
            "x":x,"y":y,
            "vx":random.uniform(-3,3),
            "vy":random.uniform(-3,3),
            "life":60
        })

# ===== COLLISION =====
def solid(x,y):
    tx=int(x//TILE)
    ty=int(y//TILE)
    if tx<0 or ty<0 or tx>=MAP_W or ty>=MAP_H:
        return True
    return map_data[ty,tx]>=2

# ===== DRAW FRAME =====
def draw():
    img = np.zeros((H,W,3),dtype=np.uint8)

    camx = int(player["x"]-W//2)
    camy = int(player["y"]-H//2)

    # draw map
    for y in range(MAP_H):
        for x in range(MAP_W):
            sx = x*TILE-camx
            sy = y*TILE-camy
            if sx<-TILE or sy<-TILE or sx>W or sy>H:
                continue

            if map_data[y,x]==0: col=(0,100,0)
            elif map_data[y,x]==1: col=(70,70,70)
            elif map_data[y,x]==2: col=(0,0,200)
            elif map_data[y,x]==3: col=(120,0,180)
            elif map_data[y,x]==4: col=(0,150,150)

            img[sy:sy+TILE, sx:sx+TILE] = col

    # player car
    px=int(player["x"]-camx)
    py=int(player["y"]-camy)
    img[py-4:py+4, px-8:px+8]=(255,255,0)

    # AI cars
    for c in ai:
        ax=int(c["x"]-camx)
        ay=int(c["y"]-camy)
        img[ay-3:ay+3, ax-6:ax+6]=(255,0,0)

    # particles
    for p in particles:
        px=int(p["x"]-camx)
        py=int(p["y"]-camy)
        if 0<=px<W and 0<=py<H:
            img[py:py+2, px:px+2]=(255,255,255)

    return img

# ===== STREAMLIT CONTROLS =====
st.title("PIXEL CITY CAR ENGINE - STREAMLIT")

col1, col2 = st.columns([1,1])
with col1:
    up = st.button("↑ GAS")
    down = st.button("↓ BRAKE")
with col2:
    left = st.button("← LEFT")
    right = st.button("→ RIGHT")

# ===== GAME LOOP =====
frame = st.empty()

for _ in range(2000):
    # controls
    if up:
        player["vx"] += math.cos(player["a"])*0.5
        player["vy"] += math.sin(player["a"])*0.5
    if down:
        player["vx"] -= math.cos(player["a"])*0.2
        player["vy"] -= math.sin(player["a"])*0.2
    if left: player["a"] -= 0.1
    if right: player["a"] += 0.1

    player["vx"]*=0.95
    player["vy"]*=0.95

    nx = player["x"]+player["vx"]
    ny = player["y"]+player["vy"]

    if solid(nx, player["y"]):
        spawn_particles(player["x"],player["y"])
        player["vx"]*=-0.5
    else:
        player["x"]=nx

    if solid(player["x"], ny):
        spawn_particles(player["x"],player["y"])
        player["vy"]*=-0.5
    else:
        player["y"]=ny

    # AI logic
    for c in ai:
        dx=player["x"]-c["x"]
        dy=player["y"]-c["y"]
        d=math.hypot(dx,dy)+1

        if d<300:
            c["vx"]+=dx/d*0.1
            c["vy"]+=dy/d*0.1
        else:
            c["vx"]+=random.uniform(-0.02,0.02)
            c["vy"]+=random.uniform(-0.02,0.02)

        c["vx"]*=0.95
        c["vy"]*=0.95

        nx=c["x"]+c["vx"]
        ny=c["y"]+c["vy"]

        if not solid(nx,c["y"]): c["x"]=nx
        if not solid(c["x"],ny): c["y"]=ny

        # crash
        if math.hypot(player["x"]-c["x"], player["y"]-c["y"])<20:
            spawn_particles((player["x"]+c["x"])/2,(player["y"]+c["y"])/2)
            player["vx"]*=-0.5
            player["vy"]*=-0.5

    # particles update
    for p in particles[:]:
        p["x"]+=p["vx"]
        p["y"]+=p["vy"]
        p["vx"]*=0.95
        p["vy"]*=0.95
        p["life"]-=1
        if p["life"]<=0:
            particles.remove(p)

    img = draw()
    frame.image(Image.fromarray(img), use_column_width=True)

    time.sleep(0.03)
