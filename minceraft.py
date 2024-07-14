from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
from random import randint
from numpy import floor

app = Ursina()

window.color = color.rgb32(0,0,0)
scene.fog_density = 0.1
scene.fog_color = color.rgb32(0,0,0)

def input(key):
    if key == 'escape':
        quit()

grassTexture = load_texture('grass.png')

terrain = Entity(model=None,collider=None,texture=grassTexture)
noise = PerlinNoise(octaves=2,seed=randint(1000,100000))
amp = 6
freq = 24

terrainW = 32
for i in range(terrainW*terrainW):
    cube = Entity(model='cube')
    cube.x = floor(i//terrainW)
    cube.z = floor(i%terrainW)
    cube.y = floor((noise([cube.x/freq,cube.z/freq]))*amp)
    cube.parent = terrain

terrain.combine()
terrain.collider = 'mesh'

def update():
    pass

player = FirstPersonController()
player.mouse_sensitivity = Vec2(100,100)
player.cursor.visible = False
player.x = player.z = 5
player.y = 12

app.run()
