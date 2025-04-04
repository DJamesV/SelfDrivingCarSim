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
screenLightness = 75 # how light a gray the background is - higher means lighter lower means darker, range 0-255
screenColor = (screenLightness, screenLightness, screenLightness) # the color of the screen as a tuple (r,g,b)

##screen vars
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
fRate = 30 #frameRate
clock=pygame.time.Clock()

## Car vars
carWidth = 50
carHeight = carWidth*(7/3) #would recommend keeping this ratio - approximately the ratio with actual cars
maxSpeed = 225/fRate #this is set relative to frame rate so that the speed stays constant even if the frame rate changes - would recommend choosing between 200 and 250
acceleration = 30/fRate #this is set  relative to frame rate so that it will stay the same as the frame rate changes
friction = 1/fRate #set relative to frame rate so it stays constant
carTurnSpeed = 1.5*(1/8)*math.pi/fRate

# custom rotate function for polygons (centers in surface) - under car vars because used solely by car
# note: this function is optimized, so it only works for polygons with each point equidistant from the center of rotation
#   honestly by this point it's not even a rotate function - it just returns a new polygon given the information
def rotate(polyPoints, polyRadius, newAngle, angleDiffs : list, centerOfRotation: tuple):
    # translating polygon so that it has the origin as the centerOfRotation (so it'll get rotated around the centerOfRotation)
    # note: polygon points use the top left corner of the surface as the automatic point of origin
    for i in range(len(polyPoints)):
        px, py = polyPoints[i]
        px -= centerOfRotation[0]
        py -= centerOfRotation[1]
        polyPoints[i] = (px, py)

    # this is the part where rotating the polygon actually happens - distance from center and theta are used to rotate each point
    newPoints = list()

    for i in range(len(polyPoints)):
        theta = newAngle + angleDiffs[i]
        px = polyRadius*math.cos(theta)
        py = polyRadius*math.sin(theta)

        newPoints.append((px, py))

    # translating polygon back to where it was
    for i in range(len(newPoints)):
        px, py = newPoints[i]
        px += centerOfRotation[0]
        py += centerOfRotation[1]
        newPoints[i] = (px, py)

    return newPoints


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


## Wall vars
wallWidth = 30
wallLightness = 70
wallColor = (wallLightness, wallLightness, wallLightness)


## Shared vars
totalSpeed = 0 # note: this var is positive for forward motion and negative for backwards motion


### Initialize pygame
pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) #setting up screen


### Setting up classes

# this class is for the Car the AI (or user) will be driving
class Car(pygame.sprite.Sprite):
    def __init__(self, width, height, mSpeed, accel, turnSpeed, friction):
        super(Car, self).__init__() # initializing the super useful Sprite class
        self.width = width
        self.height = height
        self.surfDims = (width**2 + height**2)**0.5 # using the pythagorean theorem to find the max space a given rect can take up
        self.mSpeed = mSpeed # maximum speed
        self.accel = accel # acceleration rate
        self.friction = friction # amount of friction (makes sure car stops)
        self.surf = pygame.Surface((self.surfDims, self.surfDims))
        self.surf.set_colorkey(BL) # here so that when I rotate everything it makes the extra padding transparent
        self.surf.fill(BL) # using colorkey to make the whole surface transparent
        xDiff = width/2 - self.surfDims/2 # used to setup polygon
        yDiff = height/2 - self.surfDims/2 #used to setup polygon
        self.polyPoints = [(-xDiff, -yDiff), (width - xDiff, -yDiff), (width - xDiff, height - yDiff), (-xDiff, height - yDiff)] # defining initial polygon points
        self.polygon = pygame.draw.polygon(self.surf, W, self.polyPoints) # drawing polygon
        self.mask = pygame.mask.from_surface(self.surf) # getting a bitmask (used for collision, pixel perfect collision for polygon)
        self.rect = self.surf.get_rect() # useful for moving things, etc.
        self.rect.center = ((SCREEN_WIDTH)/2, (SCREEN_HEIGHT)/2) #moving rect to center of the screen
        self.angle = 0 # 0 is set as pointing straight up - used to keep track of the car's angle (matters for sensors)
        self.turnSpeed = turnSpeed # rate at which the car turns - varies dependent on speed of car
        self.maxTurnSpeed = turnSpeed # max rate at which the car can turn
        self.totalSpeed = 0 # used to keep track of speed of car
        self.leftoverSideMovement = 0 # used to keep motion smooth even when motion is less than a bit per frame
        self.leftoverUpMovement = 0
        self.reverseCoefficient = 0.4 # cars move slower when backing up - this*speed = reverseSpeed
        self.angleDiffs = list()
        self.polygonRadius = ((self.polyPoints[0][0]-self.surfDims/2)**2 + (self.polyPoints[0][1]-self.surfDims/2)**2)**0.5

        for i in range(len(self.polyPoints)):
            if self.polyPoints[i][0] != 0:
                thisTheta = math.atan(((self.polyPoints[i][1] - self.surfDims/2)/(self.polyPoints[i][0]- self.surfDims/2)))
                if (self.polyPoints[i][0] - self.surfDims/2) < 0:
                    thisTheta += math.pi
            else:
                thisTheta = 0.5*math.pi
                if (self.polyPoints[i][1] - self.surfDims/2) < 0:
                    thisTheta += math.pi
            self.angleDiffs.append(thisTheta)

    def update(self, kPressed, tSpeed):
        ## moving things
        # cars y value won't change, but will move side to side and rotate
        # going 'faster' or 'slower' will change total speed (speed screen moves by), which will change perception of motion
        self.turnSpeed = self.maxTurnSpeed * (self.totalSpeed/self.mSpeed) # making sure can't turn super fast when not moving
        if kPressed[K_UP]: # moves car forward by accel (otherwise set car's speed to max)
            if (self.totalSpeed + self.accel) <= self.mSpeed:
                self.totalSpeed += self.accel
            else:
                self.totalSpeed = self.mSpeed
        if kPressed[K_DOWN]: # moves car forward by accel (otherwise set car's speed to max)
            if (self.totalSpeed - self.accel) >= - self.reverseCoefficient * self.mSpeed:
                self.totalSpeed -= self.accel
            else:
                self.totalSpeed = - self.reverseCoefficient * self.mSpeed
        if kPressed[K_RIGHT]: # rotating car right
            self.angle += self.turnSpeed
            if abs(self.angle) < 0.01: self.angle = 0
            
            self.polyPoints = rotate(self.polyPoints, self.polygonRadius, self.angle, self.angleDiffs, (self.surfDims/2, self.surfDims/2)) # using custom rotate function to rotate car            
            self.surf.fill(BL)
            pygame.draw.polygon(self.surf, W, self.polyPoints) #clearing then drawing the new polygon
        if kPressed[K_LEFT]: #rotating car left
            self.angle -= self.turnSpeed
            if abs(self.angle) < 0.01: self.angle = 0
            
            self.polyPoints = rotate(self.polyPoints, self.polygonRadius, self.angle, self.angleDiffs, (self.surfDims/2, self.surfDims/2)) # using custom rotate function to rotate car            
            self.surf.fill(BL)
            pygame.draw.polygon(self.surf, W, self.polyPoints) #clearing then drawing the new polygon
        
        # friction
        if self.totalSpeed > 0: # if car moving forwards
            if self.totalSpeed - self.friction >= 0:
                self.totalSpeed -= self.friction
            else:
                self.totalSpeed = 0
        elif self.totalSpeed < 0: # if car moving backwards
            if self.totalSpeed + self.friction <= 0:
                self.totalSpeed += self.friction
            else:
                self.totalSpeed = 0

        # making sure motion stays smooth (keeps track of leftover fractional pixels of movement)
        realUpMovement = self.totalSpeed * math.cos(self.angle) + self.leftoverUpMovement
        realSideMovement = self.totalSpeed * math.sin(self.angle) + self.leftoverSideMovement
        roundedUpMovement = realUpMovement.__floor__()
        self.leftoverUpMovement = realUpMovement - roundedUpMovement
        roundedSideMovement = realSideMovement.__floor__()
        self.leftoverSideMovement = realSideMovement - roundedSideMovement

        tSpeed = roundedUpMovement # uses the whole number of the current movement speed
        
        self.rect.move_ip(roundedSideMovement, 0) # moving rect side to side
        
        ## creates a new mask for the new shapemaskSurf
        self.mask.clear()
        self.mask.draw(pygame.mask.from_surface(self.surf), (0, 0)) # you can test this by setting 'self. = self.mask.to_surface(setcolor = (255,0, 0, 255))' then blitting car.maskSurf onto the screen

        return tSpeed # returns the total speed so the screen can be updated
    

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
        self.collided = False
    def update(self, pPoints, cLeft, cTop, cAngle):
        self.rect.center = arcCenterCalc(pPoints, cTop, cLeft, self.iValue) # updates position to stay with car

        # updating arc on surface
        self.surf.fill(BL)
        self.arc = pygame.draw.arc(self.surf, G, (0,0, self.width, self.height), self.startAngle - cAngle, self.stopAngle - cAngle, self.aWidth)

        # updating arc's mask
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
        # moving the lane lines proportionate to total speed
        self.rect.move_ip(0, tSpeed)
        # wrapping the lane lines if off screen
        if self.rect.top > SCREEN_HEIGHT + self.height:
            self.rect.bottom = self.rect.top - (SCREEN_HEIGHT + self.height)
        elif self.rect.bottom < 0:
            self.rect.top = SCREEN_HEIGHT + self.height + self.rect.bottom

class Walls(pygame.sprite.Sprite):
    def __init__(self, width, isRight: bool, color):
        super(Walls, self).__init__()
        self.width = width
        self.surf = pygame.surface.Surface((width, SCREEN_HEIGHT))
        self.surf.fill(color)
        self.rect = self.surf.get_rect()
        self.mask = pygame.mask.Mask((width, SCREEN_HEIGHT), True)
        if isRight: # if the wall is on the right side, move it to the right side
            self.rect.move_ip((SCREEN_WIDTH-width), 0)


### Instantiating sprites and sprite groups

## sprite groups
allSprites = pygame.sprite.Group() # mostly for usefulness when using screen.blit()
obstacles = pygame.sprite.Group() # for collision detection purposes
sensors = pygame.sprite.Group() # mostly for how easy it makes calling the update function
hiddenSensors = pygame.sprite.Group() # for when sensors see something and are no longer being blitted
laneLinesGroup = pygame.sprite.Group()
walls = pygame.sprite.Group()

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


## lane lines
laneLines = list()
for i in range(len(lanexPos)):
    laneLines.append(list())
    for j in range((math.ceil(SCREEN_HEIGHT/(laneLineHeight*2)))+1):
        thisLaneStartingy = laneLineHeight*2*j
        laneLines[i].append(LaneLine(laneLineWidth, laneLineHeight, lanexPos[i], thisLaneStartingy))
        laneLinesGroup.add(laneLines[i][j])
        allSprites.add(laneLines[i][j])

## walls
rightWall = Walls(wallWidth, True, wallColor)
leftWall = Walls(wallWidth, False, wallColor)
walls.add(rightWall)
walls.add(leftWall)
for sprite in walls:
    obstacles.add(sprite)
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
    totalSpeed = car.update(keyPressed, totalSpeed) #using the pressed key to update the cars position (and, accordingly, the total speed variable)
    sensors.update(pPoints = car.polyPoints, cLeft = car.rect.left, cTop = car.rect.top, cAngle = car.angle) #adjusting the sensors so that they stay with the car
    laneLinesGroup.update(totalSpeed)

    # if your car hits the wall, you die
    if pygame.sprite.spritecollideany(car, walls, pygame.sprite.collide_mask):
        car.kill()
        running = False

    # finding out if any sensors have been 'hit'
    for sprite in sensors:
        if sprite not in hiddenSensors:
            if pygame.sprite.spritecollideany(sprite, obstacles, pygame.sprite.collide_mask):
                allSprites.remove(sprite)
                hiddenSensors.add(sprite)
                sprite.collided = True

    # finding out if any 'hit' sensors are now 'un-hit'
    for sprite in hiddenSensors:
        if not pygame.sprite.spritecollideany(sprite, obstacles, pygame.sprite.collide_mask):
            allSprites.add(sprite)
            hiddenSensors.remove(sprite)
            sprite.collided = False

    # putting things on screen
    for sprite in allSprites:
        screen.blit(sprite.surf, sprite)

    pygame.display.flip() # updating screen

    clock.tick(fRate) # setting frame rate

pygame.quit()