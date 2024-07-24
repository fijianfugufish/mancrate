from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
#from ursina.shaders import lit_with_shadows_shader
from perlin_noise import PerlinNoise
from random import randint,randrange
from numpy import floor,sin,cos,radians
from math import dist
from copy import deepcopy
import time

app = Ursina()

deltaTime = globalClock.getDt()  # pyright: ignore

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

inventoryTexture = 'inventoryI.png'
hotbarTexture = 'hotbarI.png'
invbgTexture = 'invbgI.png'

#MODELS
grassModel = 'grassModel.obj'
chickenModel = 'chickenModel.fbx'

class Block(Entity):
    def __init__(self,model='cube',texture='white_cube',color=color.white,blockName='[unnamed]'):
        super().__init__(
            model=model,
            texture=texture,
            color=color
            )
        self.blockName = blockName

class BTYPE:
    NONE = None
    BED = Block(model='cube',texture=bedrockTexture,blockName='Bedrock')
    OAKP = Block(model='cube',texture=woodPlanksTexture,color=oak,blockName='Oak Planks')
    DOAKP = Block(model='cube',texture=woodPlanksTexture,color=darkOak,blockName='Dark Oak Planks')
    BIRP = Block(model='cube',texture=woodPlanksTexture,color=endStone,blockName='Birch Planks')
    GRASS = Block(model=grassModel,texture=grassMTexture,blockName='Grass')
    COB = Block(model='cube',texture=cobbleTexture,blockName='Cobblestone')
    STONE = Block(model='cube',texture=stoneTexture,blockName='Stone')
    END = Block(model='cube',texture=endStoneTexture,color=endStone,blockName='End Stone')

empty = {
    'Amount': 0,
    'Block': BTYPE.NONE,
    }

itemsHeld = {}

class InvSlot(Draggable):
    def __init__(self,parent,model,origin,texture,color,z,position,btype):
        super().__init__(                                                         
            parent=parent,                             
            model=model,                                             
            origin=origin,                                          
            texture=texture,
            color=color,
            z=z,
            position=position
            )
        self.location = int(self.x+1 + self.y*-9)
        self.amount = 1
        self.btype = btype

    def updLoc(self):
        self.location = int(self.x+1 + self.y*-9)

    def getLoc(self,pos):
        return int(list(pos)[0]+1 + list(pos)[1]*-9)
    
class Inventory(Entity):
    def __init__(self):
        self.sizex = 9
        self.sizey = 4
        super().__init__(
            parent=camera.ui,
            model='quad',
            scale=(self.sizex/10,self.sizey/10),                                           
            origin=(-0.5,0.5),                                         
            position=(-0.45,0.2),
            texture=inventoryTexture,                                     
            texture_scale=(self.sizex,self.sizey),
            z=0
            )
        self.overlay = Entity(
            model='quad',
            parent=self,
            scale=(100,100),
            color=color.black,
            z=10,
            alpha=0.8,
            visible=False
            )
        self.bg = Entity(
            model='quad',
            parent=self,
            scale=(332/200,352/200),
            texture=invbgTexture,
            z=8,
            origin=(-0.5,0.5),
            position=(0,0.5),
            visible=False
            )
        self.hotbar = Entity(
            model='quad',
            parent=self,
            scale=(1,1/self.sizey),
            texture=hotbarTexture,
            position=(0,-1.5),
            origin=(-0.5,0.5)
            )
        self.itemParent = Entity(parent=self,scale=(1/self.sizex,1/self.sizey),visible=False)

    def flipVisibility(self):
        self.visible_self = not self.visible_self
        self.itemParent.visible = not self.itemParent.visible
        self.overlay.visible = not self.overlay.visible
        #self.bg.visible = not self.bg.visible
        self.hotbar.visible = not self.hotbar.visible

    def findFreeSpot(self):                                                      
        takenSpots = [(int(e.x),int(e.y)) for e in self.itemParent.children]    
        for y in range(self.sizey):                                                         
            for x in range(self.sizex):                                                     
                if not (x,-y) in takenSpots:                                      
                    return (x,-y)  

    def append(self,item: object) -> None:
        global itemsHeld
        icon = InvSlot(                                                         
            parent=inventory.itemParent,                             
            model='quad',                                             
            origin=(-0.5,0.5),                                          
            texture=item.texture,
            color=item.color,
            z=-1,
            position=self.findFreeSpot(),
            btype=item
            )
        print(icon.location)
        name = item.blockName.replace('_', ' ').title()                           
        icon.tooltip = Tooltip(name)                            
        icon.tooltip.background.color = color.hsv(0,0,0,.8)
        itemsHeld[icon.location]['Amount'] = icon.amount
        itemsHeld[icon.location]['Block'] = icon.btype      
        def drag():                                                     
            icon.orgPos = (icon.x,icon.y)
            icon.z = -2
        def drop():                                                         
            icon.x = round(icon.x,0)                                            
            icon.y = round(icon.y,0)
            icon.updLoc()
            icon.z = -1
            itemsHeld[icon.getLoc(icon.orgPos)]['Amount'] = 0
            itemsHeld[icon.getLoc(icon.orgPos)]['Block'] = BTYPE.NONE
            if icon.x < 0 or icon.x > self.sizex - 1 or icon.y > 0 or icon.y < self.sizey * -1 +1: 
                icon.position = (icon.orgPos)
                icon.updLoc()
                return
            for c in self.itemParent.children:                                     
                if c == icon:                                           
                    continue                                            
                if c.x == icon.x and c.y == icon.y:                     
                    c.position = icon.orgPos
                    c.updLoc()
                    itemsHeld[c.location]['Amount'] = c.amount
                    itemsHeld[c.location]['Block'] = c.btype
                    break
            icon.updLoc()
            itemsHeld[icon.location]['Amount'] = icon.amount
            itemsHeld[icon.location]['Block'] = icon.btype
        icon.drag = drag
        icon.drop = drop

currentSlot = 1

inventory = Inventory()
inventory.visible_self = False

for i in range(36):
    itemsHeld[i+1] = deepcopy(empty)
print(itemsHeld)

for i in range(10):
    inventory.append(BTYPE.COB)
    inventory.append(BTYPE.OAKP)
    
print(itemsHeld[31]['Block'])

def nMap(n,min1,max1,min2,max2):
    return ((n-min1)/(max1-min1))*(max2-min2)+min2

bte = Entity(model='cube',unlit=True,texture=wireframeTexture,scale=1.0001)
blockType = BTYPE.BED
buildMode = False

canPlace = False

def buildTool():
    global canPlace,shells,placedBlocks,buildMode,player,blockType
    try:
        assert buildMode
        canPlace = bte.visible = True
        e = mouse.hovered_entity
        bte.position = round(e.position - camera.forward,0)
        canPlace = True
        for i in shells + placedBlocks:
            if i.position == bte.position:
                canPlace = False
        if bte.world_y >= 100:
            canPlace = False
        print(blockType)
        if dist(e.position - camera.forward,player.position) > 4 or blockType == None or not player.enabled:
            canPlace = bte.visible = False
    except:
        if buildMode and player.air_time == 0 and blockType != None and player.enabled:
            bte.position = round(player.position + camera.forward,0)
        else: canPlace = bte.visible = False

def build():
    global canPlace,blockType,currentSlot
    print(blockType)
    if not canPlace or not buildMode or blockType == None or not player.enabled: return
    e = duplicate(blockType)
    e.position = bte.position
    e.collider = 'cube'
    placedBlocks.append(e)

def input(key):
    global blockType,buildMode,currentSlot
    if key == 'escape':
        quit()
    if key == 'left mouse up':
        build()
    if key == 'right mouse up':
        e = mouse.hovered_entity
        if e and e.visible and e.texture != bedrockTexture and buildMode:
            placedBlocks.remove(e)
            destroy(e)
    
    if key == '1': currentSlot = 1
    if key == '2': currentSlot = 2
    if key == '3': currentSlot = 3
    if key == '4': currentSlot = 4
    if key == '5': currentSlot = 5
    if key == '6': currentSlot = 6
    if key == '7': currentSlot = 7
    if key == '8': currentSlot = 8
    if key == '9': currentSlot = 9

    if key == 'f': buildMode = not buildMode

    if key == 'e':
        player.enabled = not player.enabled
        inventory.flipVisibility()

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
caveDic = {}#'x9z9':'cave'}

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
shellW = 5
for i in range(shellW*shellW):
    shell = Entity(model='cube',collider='box',scale=1.0001)
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
    global prevZ,prevX,prevTime,blocks,genSpeed,genAmount,rad,origin,theta,deltaTime,currentSlot,blockType
    if abs(player.z - prevZ) > 10 or abs(player.x - prevX) > 10:
        origin = player.position
        rad = 0
        theta = 0
        
        prevZ = player.z
        prevX = player.x

    if currentSlot == 1: blockType = itemsHeld[28]['Block']
    if currentSlot == 2: blockType = itemsHeld[29]['Block']
    if currentSlot == 3: blockType = itemsHeld[30]['Block']
    if currentSlot == 4: blockType = itemsHeld[31]['Block']
    if currentSlot == 5: blockType = itemsHeld[32]['Block']
    if currentSlot == 7: blockType = itemsHeld[34]['Block']
    if currentSlot == 8: blockType = itemsHeld[35]['Block']
    if currentSlot == 9: blockType = itemsHeld[36]['Block']
    
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

blockType = itemsHeld[28]['Block']

app.run()
