import pygame
import random
import math

# key signals
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

## color codes
W = (255,255,255) #white
R = (255,0,0) #red
G = (0,255,0) #green
B = (0,0,255) #blue
Y = (255,255,0) #yellow
BL = (0,0,0) #black - note B for blue (as in rgb) and BL for BLack
screenLightness = 75 # how light a gray the backgrond is - higher means lighter lower means darker, range 0-255
screenColor = (screenLightness, screenLightness, screenLightness) # the color of the screen as a tuple (r,g,b)

##screen vars
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
fRate = 30 #frameRate
clock=pygame.time.Clock()

## Car vars
carWidth = 50
carHeight = carWidth*(7/3) #would recommend keeping this ratio - approximately the ratio with actual cars
maxSpeed = 200/fRate #this is set relative to frame rate so that the speed stays consant even if the frame rate changes
acceleration = 30/fRate #this is set  relative to frame rate so that it will stay the same as the frame rate changes
friction = 1/fRate #set relative to frame rate so it stays constant
carTurnSpeed = 1.5*(1/8)*math.pi/fRate
# Considering the rotate function just uses specifically things for Car, at this point it should be solely in the Car function, or have variables changed to be more universal,
# but I currently have it here for editing purposes, etc. Will probably edit it to be one or the other at some point
def rotate(object, turningRight: bool):
    minMax = [object.surfDims, object.surfDims, 0,0]
    minMaxChanged = [False, False, False, False]
    minMaxDefault = [0,0, object.surfDims,object.surfDims]
    newPoints = []
    for point in object.polyPoints:
        if point[0] != 0:
            theta = math.atan((point[1]/point[0]))
            if point[0] < 0:
                theta += math.pi
        elif point[1] > 0:
            theta = 0.5*math.pi
        else:
            theta = 1.5*math.pi
        length = (point[0]**2 + point[1]**2)**0.5
        if turningRight:
            px = length*math.cos(theta+object.turnSpeed)
            py = length*math.sin(theta+object.turnSpeed)
        else:
            px = length*math.cos(theta-object.turnSpeed)
            py = length*math.sin(theta-object.turnSpeed)
        newPoints.append((px,py))
        if px < minMax[0]:
            minMax[0] = px
            minMaxChanged[0] = True
        if px > minMax[2]:
            minMax[2] = px
            minMaxChanged[2] = True
        if py < minMax[1]:
            minMax[1] = py
            minMaxChanged[1] = True
        if py > minMax[3]:
            minMax[3] = py
            minMaxChanged[3] = True
    for i in range(len(minMax)):
        if minMaxChanged[i] == False:
            minMax[i] = minMaxDefault[i]
    xDiff = (((minMax[2]-minMax[0])/2)+minMax[0])-(object.surfDims/2)
    yDiff = (((minMax[3]-minMax[1])/2)+minMax[1])-(object.surfDims/2)
    for i in range(len(newPoints)):
        px, py = newPoints[i]
        px -= xDiff
        py -= yDiff
        newPoints[i] = px, py
    object.polyPoints = newPoints
    object.surf.fill(BL)
    object.polygon = pygame.draw.polygon(object.surf, W, object.polyPoints)

## Sensor vars
sensorWidth = 1 # width of arcs and lines used for sensors
# line vars
lineLengths = [200] # length of lines in list format - list not needed for code as currently written but here for flexibility. To add more line sensors, you'd adjust this, lineCenterCalc, and linePointsCalc
def lineCenterCalc(carRect, iVal: int): # this is a function instead of a list due to the presence of values like carRect.top
    lineCenters = [(carRect.centerx, (carRect.top-lineLengths[iVal]))]
    return lineCenters[iVal]
def linePointsCalc(carRect, iVal: int): # function instead of list due to presence of values like carRect
    linePoints = [((carRect.centerx, carRect.top), (carRect.centerx, (carRect.top)))]
    return linePoints[iVal]
# arc vars - note: sensor generally refers to each group of arcs, arc refers to an individual arc
arcNumber = 6 # number of seperate arcs per sensor, distributed over arcDistanceMin to arcDistanceMax
arcDistanceMin = 10*2 # due to pygame quirks, this is half the distance the first arc will be put at from the car (hence the *2)
arcDistanceMax = 90*2 # half the distance the last arc will be put at
arcIncrement = (arcDistanceMax-arcDistanceMin)/(arcNumber-1)
#to add another arc sensor you'd adjust arcCenterCalc and arcAngles
#use Pi for ease of change at least while still editing
arcAngles = [[math.pi*(1/8), math.pi*(3/8)], [math.pi*(5/8), math.pi*(7/8)], [math.pi*(7/8), math.pi*(9/8)], [math.pi*(15/8), math.pi*(17/8)]] # angles I want each individual sensor to detect from to (note: in radians)
def arcCenterCalc(polyPoints, cTop, cLeft, iVal): # function due to dependency on carRect
    arcCenters = [(polyPoints[1]),
                   (polyPoints[0]),
                  (polyPoints[3]),
                    (polyPoints[2])]
    thisx, thisy = arcCenters[iVal]
    thisx += cLeft
    thisy += cTop
    return thisx, thisy

## Lane vars
laneLineWidth = 10
laneLineHeight = 50
lanexPos = [200, 400]

## Shared vars
totalSpeed = 0 # note: this var is positive for forward motion and negative for backwards motion

# Initialize pygame
pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) #setting up screen


### Setting up classes

# this class is for the Car the AI (or user) will be driving
class Car(pygame.sprite.Sprite):
    def __init__(self, width, height, mSpeed, accel, turnSpeed, friction):
        super(Car, self).__init__() # initializing the super useful Sprite class
        self.width = width
        self.height = height
        self.surfDims = (width**2 + height**2)**0.5
        self.mSpeed = mSpeed
        self.accel = accel
        self.friction = friction
        self.surf = pygame.Surface((self.surfDims, self.surfDims))
        self.surf.set_colorkey(BL) # here so that when I rotate everything it makes the extra padding transparent
        self.surf.fill(BL)
        xDiff = width/2 - self.surfDims/2
        yDiff = height/2 - self.surfDims/2
        self.polyPoints = [(-xDiff, -yDiff), (width - xDiff, -yDiff), (width - xDiff, height - yDiff), (-xDiff, height - yDiff)]
        self.polygon = pygame.draw.polygon(self.surf, W, self.polyPoints)
        self.mask = pygame.mask.from_surface(self.surf)
        self.rect = self.surf.get_rect()
        self.rect.center = ((SCREEN_WIDTH)/2, (SCREEN_HEIGHT)/2)
        self.angle = 0 # setting current angle as 0 - in this case I've set 0 as pointing towards the top of the screen
        self.turnSpeed = turnSpeed
        self.totalSpeed = 0
        if self.polyPoints[0][0] != 0:
            self.theta0 = math.atan(((self.polyPoints[0][1] - self.surfDims/2)/(self.polyPoints[0][0]- self.surfDims/2)))
            if (self.polyPoints[0][0] - self.surfDims/2) < 0:
                self.theta0 += math.pi
        else:
            self.theta0 = 0.5*math.pi
            if (self.polyPoints[0][1] - self.surfDims/2) < 0:
                self.theta0 += math.pi
        self.tick = 0
        self.leftoverSideMovement = 0
        self.leftoverUpMovement = 0
    def update(self, kPressed, tSpeed):
        ### To Do Next: ADJUST THIS AND ADD IN OTHER CARS - everything should be in relation to total speed
        # cars y value won't change, but will move side to side and rotate
        # going 'faster' or 'slower' will change total speed (speed screen moves by), which will change perception of motion
        # moving things
        if kPressed[K_UP] and (self.totalSpeed + self.accel) <= self.mSpeed:
            self.totalSpeed += self.accel
        if kPressed[K_DOWN] and (self.totalSpeed - self.accel) >= -self.mSpeed:
            self.totalSpeed -= self.accel
        if kPressed[K_RIGHT]:
            rotate(self, True)
            self.angle += self.turnSpeed
        if kPressed[K_LEFT]:
            rotate(self, False)
            self.angle -= self.turnSpeed
        
        if self.totalSpeed > 0:
            if self.totalSpeed - self.friction >= 0:
                self.totalSpeed -= self.friction
            else:
                self.totalSpeed = 0
        elif self.totalSpeed < 0:
            if self.totalSpeed + self.friction <= 0:
                self.totalSpeed += self.friction
            else:
                self.totalSpeed = 0

        realUpMovement = self.totalSpeed * math.cos(self.angle) + self.leftoverUpMovement
        self.leftoverUpMovement = 0
        realSideMovement = self.totalSpeed * math.sin(self.angle) + self.leftoverSideMovement
        self.leftoverSideMovement = 0
        roundedUpMovement = realUpMovement.__floor__()
        self.leftoverUpMovement += realUpMovement - roundedUpMovement
        roundedSideMovement = realSideMovement.__floor__()
        self.leftoverSideMovement += realSideMovement - roundedSideMovement

        tSpeed = roundedUpMovement
        
        self.rect.move_ip(roundedSideMovement, 0)

        self.tick += 1
        if self.tick >= fRate: #currently gets called once every second
            self.checkAngle()
            self.tick = 0
        
        self.mask.clear()
        self.mask.draw(pygame.mask.from_surface(self.surf), (0, 0)) # you can test this by setting 'self.maskSurf = self.mask.to_surface(setcolor = (255,0, 0, 255))' then blitting car.maskSurf onto the screen

        return tSpeed
    def checkAngle(self):
        fx, fy = self.polyPoints[0]
        if (fx - self.surfDims/2) != 0:
            tempTheta = math.atan((fy-self.surfDims/2)/(fx-self.surfDims/2))
            if (fx - self.surfDims/2) < 0:
                tempTheta += math.pi
        elif (fy - self.surfDims) > 0:
            tempTheta = 0.5*math.pi
        else:
            tempTheta = 1.5*math.pi
        self.angle = tempTheta - self.theta0

# this class is for sensors in the form of lines as opposed to arcs
class LineSensor(pygame.sprite.Sprite):
    def __init__(self, startPoint, endPoint, lWidth):
        super(LineSensor, self).__init__()
        self.width = lWidth
        self.height = abs(startPoint[1] - endPoint[1])
        self.surf = pygame.Surface((self.width, self.height))
        self.surf.fill(BL)
        self.surf.set_colorkey(BL) # says I want everything colored black to actually be transparent
        self.rect = self.surf.get_rect()
        self.line = pygame.draw.line(self.surf, G, startPoint, endPoint, lWidth) # line and not rect is important because that means I can use the rect.clipline() function for collision detection purposes
    def update(self, cRect):
        self.rect.center = lineCenterCalc(cRect, self.iValue) # updates position to stay with car

# this class if for sensors in the form of lines as opposed to arcs
class ArcSensor(pygame.sprite.Sprite):
    def __init__(self, width, height, startAngle, stopAngle, aWidth, iValue):
        super(ArcSensor, self).__init__()
        self.width = width
        self.height = height
        self.iValue = iValue
        self.surf = pygame.Surface((width, height))
        self.surf.fill(BL)
        self.surf.set_colorkey(BL) # says I want everything colored black to actually be transparent
        self.rect = self.surf.get_rect()
        self.startAngle = startAngle
        self.stopAngle = stopAngle
        self.arc = pygame.draw.arc(self.surf, G, self.rect, startAngle, stopAngle, aWidth)
        self.aWidth = aWidth
        self.mask = pygame.mask.from_surface(self.surf) # makes a mask (used for collision purposes) out of the arc I just drew
        self.rect.center = arcCenterCalc(car.polyPoints, car.rect.top, car.rect.left, i)
    def update(self, pPoints, cLeft, cTop, cAngle):
        self.rect.center = arcCenterCalc(pPoints, cTop, cLeft, self.iValue) # updates position to stay with car
        self.surf.fill(BL)
        self.arc = pygame.draw.arc(self.surf, G, (0,0, self.width, self.height), self.startAngle - cAngle, self.stopAngle - cAngle, self.aWidth)
        self.mask.clear()
        self.mask.draw(pygame.mask.from_surface(self.surf), (0,0))

# this class is for the street lines
class LaneLine(pygame.sprite.Sprite):
    def __init__(self, width, height, startingx, startingy):
        super(LaneLine, self).__init__()
        self.width = width
        self.height = height
        self.surf = pygame.Surface((width, height))
        self.surf.fill(W)
        self.rect = self.surf.get_rect()
        self.rect.x, self.rect.y = startingx, startingy
    def update(self, tSpeed):
        self.rect.move_ip(0, tSpeed)
        if self.rect.top > SCREEN_HEIGHT + self.height:
            self.rect.bottom = self.rect.top - (SCREEN_HEIGHT + self.height)
        elif self.rect.bottom < 0:
            self.rect.top = SCREEN_HEIGHT + self.height + self.rect.bottom


### Instantiating sprites and sprite groups

## sprite groups
allSprites = pygame.sprite.Group() #mostly for usefulness when using screen.blit()
sensors = pygame.sprite.Group() #mostly for how easy it makes calling the update function
laneLinesGroup = pygame.sprite.Group()

## the car
car = Car(carWidth, carHeight, maxSpeed, acceleration, carTurnSpeed, friction)
allSprites.add(car)

## line sensor(s)
lines = []
for i in range(len(lineLengths)):
    thisLineCenter = lineCenterCalc(car.rect, i)
    lines.append(LineSensor((car.rect.centerx, car.rect.top), (car.rect.centerx, (car.rect.top-lineLengths[i])), sensorWidth))


## arc sensors
# using nested for loops to create each individual arc for each sensor
arcs = list() # this list will hold every group of arc sensors, each item in the list will be another list with each individual arc for each individual sensor

for i in range(len(arcAngles)): # this for loop goes through each sensor position, one top right, one top left, one back right, one back left
    # arcs is a list of list, so I'm defining each index of arc as an empty list
    arcs.append([])
    # this for loop creates every individual arc within a sensor
    for j in range(arcNumber):
        thisArcSize = arcDistanceMin+arcIncrement*j
        arcs[i].append(ArcSensor(thisArcSize, thisArcSize, arcAngles[i][0], arcAngles[i][1], sensorWidth, i))
        sensors.add(arcs[i][j]) # adding arc to group

# adds each individual arc and line to sensors
for sprite in sensors:
    allSprites.add(sprite)

laneLines = list()
for i in range(len(lanexPos)):
    laneLines.append(list())
    for j in range((math.ceil(SCREEN_HEIGHT/(laneLineHeight*2)))+1):
        thisLaneStartingy = laneLineHeight*2*j
        laneLines[i].append(LaneLine(laneLineWidth, laneLineHeight, lanexPos[i], thisLaneStartingy))
        laneLinesGroup.add(laneLines[i][j])
        allSprites.add(laneLines[i][j])

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
    totalSpeed = car.update(keyPressed, totalSpeed) #using the pressed key to update the cars position (and, accordingly, the total speed variable)
    sensors.update(pPoints = car.polyPoints, cLeft = car.rect.left, cTop = car.rect.top, cAngle = car.angle) #adjusting the sensors so that they stay with the car
    laneLinesGroup.update(totalSpeed)

    for sprite in allSprites:
        screen.blit(sprite.surf, sprite)

    pygame.display.flip()

    clock.tick(30)

pygame.quit()