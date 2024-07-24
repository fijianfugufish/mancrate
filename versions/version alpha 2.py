from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
#from safe_combine import safe_combine
#from ursina.shaders import lit_with_shadows_shader
from perlin_noise import PerlinNoise
from random import randint,randrange
from numpy import floor,sin,cos,radians
from math import dist
import time

app = Ursina()

deltaTime = globalClock.getDt()

#lights = []
placedBlocks = []

window.color = color.rgb32(0,0,0)
scene.fog_density = 0.05
scene.fog_color = color.rgb(0,0,0)

#Dl = DirectionalLight()
#Dl.disable()

sky = Sky()

#Entity.default_shader = lit_with_shadows_shader

prevTime = time.time()

#COLOURS
oak = color.rgb32(216,181,137)
darkOak = color.rgb32(85,52,43)
dirt = color.rgb32(205,170,125)
stone = color.rgb32(136,140,141)
endStone = color.rgb32(255,255,191)

#TEXTURES
bedrockTexture = 'bedrock.png'
grassTexture = 'grass.png'
wireframeTexture = 'wireframe.png'
woodPlanksTexture = 'woodPlanks.png'
cobbleTexture = 'cobble.png'
endStoneTexture = 'endStone.png'
stoneTexture = 'stone.png'

grassMTexture = 'grassM.png'
chickenTexture = 'chickenM.png'

#MODELS
grassModel = 'grassModel.obj'
chickenModel = 'chickenModel.fbx'

def nMap(n,min1,max1,min2,max2):
    return ((n-min1)/(max1-min1))*(max2-min2)+min2

bte = Entity(model='cube',unlit=True,texture=wireframeTexture,scale=1.0001)
class BTYPE:
    BED = Entity(model='cube',texture=bedrockTexture)
    OAKP = Entity(model='cube',texture=woodPlanksTexture,color=oak)
    DOAKP = Entity(model='cube',texture=woodPlanksTexture,color=darkOak)
    BIRP = Entity(model='cube',texture=woodPlanksTexture,color=endStone)
    GRASS = Entity(model=grassModel,texture=grassMTexture)
    COB = Entity(model='cube',texture=cobbleTexture)
    STONE = Entity(model='cube',texture=stoneTexture)
    END = Entity(model='cube',texture=endStoneTexture,color=endStone)
blockType = BTYPE.BED
buildMode = False

canPlace = False

def buildTool():
    global canPlace,shells,placedBlocks,buildMode,player
    try:
        assert buildMode
        canPlace = bte.visible = True
        e = mouse.hovered_entity
        bte.position = e.position - round(camera.forward,0)
        canPlace = True
        if bte.world_y >= 100:
            canPlace = False
        if dist(e.position - round(camera.forward,0),player.position) > 6:
            canPlace = bte.visible = False
    except:
        if buildMode and player.air_time == 0:
            bte.position = round(player.position + camera.forward,0)
        else: canPlace = bte.visible = False

def build():
    global canPlace,blockType
    if not canPlace or not buildMode: return
    e = duplicate(blockType)
    e.position = bte.position
    e.collider = 'cube'
    placedBlocks.append(e)

def input(key):
    global blockType,buildMode
    if key == 'escape':
        quit()
    if key == 'left mouse up':
        build()
    if key == 'right mouse up':
        e = mouse.hovered_entity
        if e and e.visible and e.texture != bedrockTexture and buildMode:
            placedBlocks.remove(e)
            destroy(e)
    if key == '1': blockType = BTYPE.OAKP
    if key == '2': blockType = BTYPE.DOAKP
    if key == '3': blockType = BTYPE.BIRP
    if key == '4': blockType = BTYPE.GRASS
    if key == '5': blockType = BTYPE.COB
    if key == '6': blockType = BTYPE.STONE
    if key == '7': blockType = BTYPE.END

    if key == 'f': buildMode = not buildMode

    if key == 'g': generateTerrain()

bobethy = Entity(model=chickenModel,texture=chickenTexture,double_sided=True,scale=0.05,y=0.876)

noise = PerlinNoise(octaves=1,seed=randint(1,100000))

megasets = []
subsets = []
subCubes = []

genSpeed = 0
genAmount = 160

currentSubset = 0
currentCube = 0
numSubCubes = 160
numSubsets = 420
theta = 0
rad = 0
renderDist = 64
origin = Vec3(0,12,0)

subDic = dict()
caveDic = {'x9z9':'cave'}

for i in range(numSubCubes):
    block = Entity(model=grassModel)
    block.disable()
    subCubes.append(block)

for i in range(numSubsets):
    block = Entity(model=None)
    block.texture = grassMTexture
    block.disable()
    subsets.append(block)

def genPerlin(_x,_z):
    y = 0
    freq = 64
    amp = 42
    y += ((noise([_x/freq,_z/freq]))*amp)
    freq = 32
    amp = 21
    y += ((noise([_x/freq,_z/freq]))*amp)
    if caveDic.get('x'+str(int(_x))+'z'+str(int(_z))) == 'cave':
        y += 32
    return floor(y)

def generateTerrain():
    global currentCube,theta,rad,renderDist,origin,subDic,currentSubset
    if rad >= renderDist: return
    x = floor(origin.x + sin(radians(theta)) * rad)
    z = floor(origin.z + cos(radians(theta)) * rad)
    if subDic.get('x'+str(x)+'z'+str(z)) != 'i':
        subCubes[currentCube].enable()
        subCubes[currentCube].x = x
        subCubes[currentCube].z = z
        if x == z == 0:
            subCubes[currentCube].disable()
        subDic['x'+str(x)+'z'+str(z)] = 'i'
        subCubes[currentCube].parent = subsets[currentSubset]
        y = subCubes[currentCube].y = genPerlin(x,z)
        #subCubes[currentCube].disable()
        currentCube += 1
        if currentCube == numSubCubes:
            subsets[currentSubset].combine(auto_destroy=False)
            subsets[currentSubset].enable()
            currentSubset += 1
            currentCube = 0

            if currentSubset == numSubsets:
                megasets.append(Entity(texture=grassMTexture))
                for i in subsets:
                    i.parent = megasets[-1]
                megasets[-1].combine(auto_destroy=False)
                if len(megasets) > 1:
                    destroy(megasets[0])
                    megasets.remove(megasets[0])
                currentSubset = 0
    if rad != 0:
        theta += 45/rad
    else: rad += 0.5
    if theta >= 360:
        theta = 0
        rad += 0.5

shells = []
shellW = 6
for i in range(shellW*shellW):
    shell = Entity(model='cube',collider='box')
    shell.visible = False
    shells.append(shell)

def generateShell():
    # global player,deltaTime
    # targetY = genPerlin(player.x,player.z) + 0.35
    # player.y = lerp(player.y,targetY,9.807 * deltaTime)
    
    global shellW
    for i in range(len(shells)):
        x = shells[i].x = floor((i/shellW) + player.x - 0.5 * shellW)
        z = shells[i].z = floor((i%shellW) + player.z - 0.5 * shellW)
        shells[i].y = genPerlin(x,z)

def update():
    global prevZ,prevX,prevTime,blocks,genSpeed,genAmount,rad,origin,theta,deltaTime
    deltaTime = globalClock.getDt()
    if abs(player.z - prevZ) > 10 or abs(player.x - prevX) > 10:
        origin = player.position
        rad = 0
        theta = 0
        
        prevZ = player.z
        prevX = player.x
        
    generateShell()

    if time.time() - prevTime > genSpeed:
        for i in range(genAmount):
            generateTerrain()
        prevTime = time.time()

    if player.y < -125:
        player.y = 125

    buildTool()

    bobethy.look_at(player,'forward')
    bobethy.rotation_z = bobethy.rotation_x = 0

    #playerLight.position = player.position
    #playerLight.y += 10

player = FirstPersonController()
player.mouse_sensitivity = Vec2(100,100)
player.cursor.visible = False
#player.gravity = 0
player.x = player.z = 1
player.y = 12
prevZ = player.z
prevX = player.x
origin = player.position
#playerLight = SpotLight(shadows=True)
#lights.append(playerLight)

generateShell()

blockType = BTYPE.OAKP

app.run()
