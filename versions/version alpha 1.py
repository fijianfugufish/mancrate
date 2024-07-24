from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
#from ursina.shaders import lit_with_shadows_shader
from perlin_noise import PerlinNoise
from random import randint,randrange
from numpy import floor
from math import dist
import time

app = Ursina()

#lights = []
placedBlocks = []

window.color = color.rgb32(0,0,0)
#scene.fog_density = 0.05
#scene.fog_color = color.rgb(0,255,0,)

#Dl = DirectionalLight()
#Dl.disable()

sky = Sky()

#Entity.default_shader = lit_with_shadows_shader

prevTime = time.time()

#COLOURS
oak = color.rgb32(216,181,137)

#TEXTURES
grassTexture = load_texture('grass.png')
chickenTexture = load_texture('chicken.png')
wireframeTexture = load_texture('wireframe.png')
woodPlanksTexture = load_texture('woodPlanks.png')

#MODELS
grassModel = load_model('grass.obj')
chickenModel = load_model('chicken.fbx')

def nMap(n,min1,max1,min2,max2):
    return ((n-min1)/(max1-min1))*(max2-min2)+min2

bte = Entity(model='cube',unlit=True,texture=wireframeTexture,scale=1.0001)
canPlace = False

def buildTool():
    global canPlace,shells,placedBlocks
    try:
        canPlace = bte.visible = True
        e = mouse.hovered_entity
        bte.position = e.position - round(camera.forward,0)
        canPlace = True
        for i in shells + placedBlocks:
            if i.position == bte.position:
                canPlace = False
        if dist(e.position - round(camera.forward,0),player.position) > 6:
            canPlace = bte.visible = False
    except:
        canPlace = bte.visible = False

def build():
    global canPlace
    if not canPlace: return
    e = duplicate(bte)
    e.collider = 'cube'
    e.texture = woodPlanksTexture
    e.color = oak
    e.scale = 1
    placedBlocks.append(e)

def input(key):
    if key == 'escape':
        quit()
    elif key == 'left mouse up':
        build()
    elif key == 'right mouse up':
        e = mouse.hovered_entity
        if e and e.visible:
            placedBlocks.remove(e)
            destroy(e)

bobethy = Entity(model=chickenModel,texture=chickenTexture,double_sided=True,scale=0.05,y=0.876)

noise = PerlinNoise(octaves=2,seed=randint(1,1000000000))
amp = 50
freq = 80
terrain = Entity(model=None,collider=None)
terrainW = 40
subW = int(terrainW)
subsets = []
subCubes = []
sci = 0
currentSubset = 0

for i in range(subW):
    block = Entity(model='cube')
    subCubes.append(block)

for i in range((terrainW*terrainW)//subW):
    block = Entity(model='cube')
    block.parent = terrain
    subsets.append(block)

def generateSubset():
    global sci,currentSubset,amp,freq,terrainw
    if currentSubset >= len(subsets):
        finishTerrain()
        return
    for i in range(subW):
        x = subCubes[i].x = floor((i + sci)/terrainW)-terrainW/2
        z = subCubes[i].z = floor((i + sci)%terrainW)-terrainW/2
        y = subCubes[i].y = floor((noise([x/freq,z/freq]))*amp)
        subCubes[i].parent = subsets[currentSubset]

        y += randrange(-4,4)
        
        r = 0
        g = 0
        b = 0
        if z > terrainW*0.5:
            g = b = 0
            r = nMap(y,0,amp,110,255)
        else:
            g = nMap(y,0,amp*0.5,130,255)
        subCubes[i].color = color.rgb32(r,g,b)
        subCubes[i].visible = False

    subsets[currentSubset].combine(auto_destroy=False)
    #subsets[currentSubset].texture = grassTexture
    sci += subW
    currentSubset += 1

terrainFinished = False
def finishTerrain():
    global terrainFinished,amp
    if terrainFinished == True: return
    terrain.combine()
    terrainFinished = True
    player.land()
    terrain.texture = grassTexture
    terrain.unlit = False

shells = []
shellW = 6
for i in range(shellW*shellW):
    shell = Entity(model='cube',collider='box')
    shell.visible = False
    shells.append(shell)

def generateShell():
    global amp,freq,shellW
    for i in range(len(shells)):
        x = shells[i].x = floor((i/shellW) + player.x - 0.5 * shellW)
        z = shells[i].z = floor((i%shellW) + player.z - 0.5 * shellW)
        shells[i].y = floor((noise([x/freq,z/freq]))*amp)

def update():
    global prevZ,prevX,prevTime,amp,blocks
    if abs(player.z - prevZ) > 1 or abs(player.x - prevX) > 1:
        generateShell()

    if time.time() - prevTime > 0.001:
        generateSubset()
        prevTime = time.time()

    if player.y < -amp*2+1:
        player.y = amp*2
        player.land()

    buildTool()

    bobethy.look_at(player,'forward')
    bobethy.rotation_z = bobethy.rotation_x = 0

    #playerLight.position = player.position
    #playerLight.y += 10

player = FirstPersonController()
player.mouse_sensitivity = Vec2(100,100)
player.cursor.visible = False
player.x = player.z = 5
player.y = 12
prevZ = player.z
prevX = player.x
#playerLight = SpotLight(shadows=True)
#lights.append(playerLight)

generateShell()

app.run()
