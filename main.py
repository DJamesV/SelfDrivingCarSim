import pygame
import random
import math

#key signals
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,

)

### Setting up vars
#color codes
W = (255,255,255) #white
R = (255,0,0) #red
G = (0,255,0) #green
B = (0,0,255) #blue
Y = (255,255,0) #yellow
BL = (0,0,0) #black - note B for blue (as in rgb) and BL for BLack
screenLightness = 75 #how dark a gray the backgrond is
screenColor = (screenLightness,screenLightness,screenLightness) #the color of the screen as a tuple (r,g,b)

##screen vars
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
fRate = 30 #frameRate
clock=pygame.time.Clock()

#car vars
carWidth = 50
carHeight = carWidth*(7/3) #would recommend keeping this ratio - approximately the ratio with actual cars
maxSpeed = 150/fRate #this is set relative to frame rate so that the speed stays consant even if the frame rate changes

#sensor vars
sensorWidth = 1
lineNumber = 1
lineLength = [200]
def lineCenterCalc(carRect, iVal):
    lineCenters = [(carRect.centerx, (carRect.top-lineLength[iVal]))]
    return lineCenters[iVal]
def linePointsCalc(carRect, iVal):
    linePoints = [((carRect.centerx, carRect.top), (carRect.centerx, (carRect.top)))]
arcNumber = 6
arcDistanceMin = 20
arcDistanceMax = 180
arcIncrement = (arcDistanceMax-arcDistanceMin)/(arcNumber-1)
#to add another sensor you'd adjust arcCenterCalc and arcAngles
#use Pi for ease of change at least while still editing
arcAngles = [[math.pi*(1/8), math.pi*(3/8)], [math.pi*(5/8), math.pi*(7/8)], [math.pi*(7/8), math.pi*(9/8)], [math.pi*(15/8), math.pi*(17/8)]] #arcAngles in radians I want sensors to detect
def arcCenterCalc(carRect, iVal):
    arcCenters = [((carRect.right), (carRect.top)),
                   ((carRect.left), (carRect.top)), 
                  ((carRect.left), (carRect.bottom)),
                    ((carRect.right), (carRect.bottom))]
    return arcCenters[iVal]

#shared vars
totalSpeed = 0

# Initialize pygame
pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

class Car(pygame.sprite.Sprite):
    def __init__(self, width, height, speed):
        super(Car, self).__init__()
        self.width = width
        self.height = height
        self.speed = speed
        self.surf = pygame.Surface((width, height))
        self.surf.fill(W)
        self.rect = self.surf.get_rect()
        #moving rect to center of screen
        self.rect.center = ((SCREEN_WIDTH)/2, (SCREEN_HEIGHT)/2)
    def update(self, kPressed, tSpeed):
        ### To Do Next: ADJUST THIS AND ADD IN OTHER CARS - everything should be in relation to total speed
        #moving things
        if kPressed[K_UP] and (self.rect.top-self.speed)>0:
            self.rect.move_ip(0, -self.speed)
        if kPressed[K_DOWN] and (self.rect.bottom+self.speed)<SCREEN_HEIGHT:
            self.rect.move_ip(0,self.speed)
        if kPressed[K_LEFT] and (self.rect.left-self.speed)>0:
            self.rect.move_ip(-self.speed,0)
        if kPressed[K_RIGHT] and (self.rect.right+self.speed)<SCREEN_WIDTH:
            self.rect.move_ip(self.speed,0)

        ###technically redundant but why not
        #checking for out of bounds to left
        if self.rect.left < 0:
            self.rect.left = 0
        #checking for out of bounds to right
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        #checking for out of bounds above
        if self.rect.top < 0:
            self.rect.top = 0
        #checking for out of bound below
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        return tSpeed
    
class LineSensor(pygame.sprite.Sprite):
    def __init__(self, startPoint, endPoint, lWidth):
        super(LineSensor, self).__init__()
        self.width = lWidth
        self.height = abs(startPoint[1] - endPoint[1])
        self.surf = pygame.Surface((self.width, self.height))
        self.surf.fill(BL)
        self.surf.set_colorkey(BL)
        self.rect = self.surf.get_rect()
        self.line = pygame.draw.line(self.surf, G, startPoint, endPoint)
    def update(self, cRect):
        self.rect.center = lineCenterCalc(cRect, self.iValue)

class ArcSensor(pygame.sprite.Sprite):
    def __init__(self, width, height, startAngle, stopAngle, aWidth):
        super(ArcSensor, self).__init__()
        self.width = width
        self.height = height
        self.surf = pygame.Surface((width, height))
        self.surf.fill(BL)
        self.surf.set_colorkey(BL)
        self.rect = self.surf.get_rect()
        self.arc = pygame.draw.arc(self.surf, G, self.rect, startAngle, stopAngle, aWidth)
        self.mask = pygame.mask.from_surface(self.surf)
    def update(self, cRect):
        self.rect.center = arcCenterCalc(cRect, self.iValue)
        
allSprites = pygame.sprite.Group()
sensors = pygame.sprite.Group()

car = Car(carWidth, carHeight, maxSpeed)
allSprites.add(car)

for i in lineNumber:
    thisLineCenter = lineCenterCalc(car.rect, i)
    lineFront = LineSensor((car.rect.centerx, car.rect.top), (car.rect.centerx, (car.rect.top-lineLength[i])), sensorWidth)

##creating every sensor arc in one for loop, as well as defining their places relative to the car
arcs = list()#this list will hold every arc sprite
for i in range(len(arcAngles)):
    arcs.append([])
    for j in range(arcNumber):
        arcs[i].append(0)
#this for loop goes through each sensor position, one top right, one top left, one back right, one back left
for i in range(len(arcAngles)):
    #arcs is a list of list, so I'm defining each index of arc as an empty list
    #arcs.append([])
    #this for loop creates every individual arc within a sensor
    for j in range(arcNumber):
        thisArcSize = arcDistanceMin+arcIncrement*j
        arcs[i][j] = (ArcSensor(thisArcSize, thisArcSize, arcAngles[i][0], arcAngles[i][1], sensorWidth))
        #figuring out where I need to move the arcs to relative to the car
        thisArcCenter = arcCenterCalc(car.rect, i)
        #moving arc to position just found
        arcs[i][j].rect.center = thisArcCenter
        arcs[i][j].iValue = i
        sensors.add(arcs[i][j])


for sprite in sensors:
    allSprites.add(sprite)
        
running = True

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running=False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running=False


    screen.fill(screenColor)
    
    keyPressed = pygame.key.get_pressed() #figuring out what key was pressed
    car.update(keyPressed, totalSpeed) #using the pressed key to update the cars position (and, accordingly, the total speed variable)
    sensors.update(car.rect) #adjusting the sensors so that they stay with the car

    for sprite in allSprites:
        screen.blit(sprite.surf, sprite)

    pygame.display.flip()

    clock.tick(30)

pygame.quit()