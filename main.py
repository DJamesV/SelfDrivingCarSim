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


### NEW SECTION: Setting up vars


## color codes
class Colors:
    def __init__(self):
        self.W = (255,255,255) #white
        self.R = (255,0,0) #red
        self.G = (0,255,0) #green
        self.B = (0,0,255) #blue
        self.Y = (255,255,0) #yellow
        self.BL = (0,0,0) #black - note colors.B for blue (as in rgb) and colors.BL for BLack
colors = Colors()
screenLightness = 75 # how light a gray the background is - higher means lighter lower means darker, range 0-255
screenColor = (screenLightness, screenLightness, screenLightness) # the color of the screen as a tuple (r,g,b)

##screen vars
SCREEN_WIDTH = 400
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
carAngleRounder = carTurnSpeed/2

# custom rotate function for polygons (centers in surface); it's under car vars because used solely by car
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
def linePointsCalc(polyPoints, width, height, length, amtShown, angle, iVal: int): # function instead of list due to presence of values like carRect
    linePoints = [((width/2, height/2), (width/2 + length*math.sin(angle), height/2 - length*math.cos(angle)), (width/2 + amtShown*math.sin(angle), height/2 - amtShown*math.cos(angle)), (car.rect.left+(polyPoints[0][0]+polyPoints[1][0])/2, car.rect.top + (polyPoints[0][1]+polyPoints[1][1])/2))]
    return linePoints[iVal]
    # return (50,200), (60, 100), (200,200)

# arc vars - note: sensor generally refers to each group of arcs, arc refers to an individual arc
arcNumber = 6 # number of seperate arcs per sensor, distributed over arcDistanceMin to arcDistanceMax
arcDistanceMin = 10*2 # due to pygame quirks, this is half the distance the first arc will be put at from the car (hence the *2)
arcDistanceMax = 90*2 # half the distance the last arc will be put at
arcIncrement = (arcDistanceMax-arcDistanceMin)/(arcNumber-1) #distance between arcs
arcsHit = []
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


## Wall vars
wallWidth = 30
wallLightness = 70
wallColor = (wallLightness, wallLightness, wallLightness)

## Lane vars
laneLineWidth = 10
laneLineHeight = 50
lanexPos = [((SCREEN_WIDTH-2*wallWidth - 2*laneLineWidth) * 0.33333 + wallWidth), ((SCREEN_WIDTH-2*wallWidth-2*laneLineWidth) * 0.66667 + wallWidth + laneLineWidth)]
laneBoundaries = [(wallWidth, ((SCREEN_WIDTH-2*wallWidth - 2*laneLineWidth) * 0.33333 + wallWidth)), 
                  (((SCREEN_WIDTH-2*wallWidth - 2*laneLineWidth) * 0.33333 + wallWidth + laneLineWidth), ((SCREEN_WIDTH-2*wallWidth-2*laneLineWidth) * 0.66667 + wallWidth + laneLineWidth)),
                    (((SCREEN_WIDTH-2*wallWidth-2*laneLineWidth) * 0.66667 + wallWidth + laneLineWidth*2), (SCREEN_WIDTH-wallWidth))]

## Other car vars
coastSpeed = maxSpeed * 0.7
spawnxVal = []
mobs=[]
# for i in range(len(laneBoundaries)):
#     spawnxVal.append((laneBoundaries[i][0]+laneBoundaries[i][1])/2)
for tuple1 in laneBoundaries:
    spawnxVal.append((tuple1[0]+tuple1[1])/2)
    print(spawnxVal)
print(spawnxVal)
def spawnMob(mobs: dict, mobClass, mobSpawnxVals: list):
    amtOfMobsSpawned = random.randint(0, (len(mobSpawnxVals)))
    print(amtOfMobsSpawned)
    mobSpawnxVal = mobSpawnxVals.copy()
    randomIndex = random.randint(0, (len(mobSpawnxVals)-1))

    if amtOfMobsSpawned == 1:
        mobSpawnxVal = [mobSpawnxVal[randomIndex]]
    elif amtOfMobsSpawned == 2:
        mobSpawnxVal.pop(randomIndex)

    for i in range(amtOfMobsSpawned):
        mobs.append(mobClass(carWidth, carHeight, coastSpeed, (mobSpawnxVal[i], -carHeight)))
        print(mobSpawnxVal[i])

    obstacles.add(mobs)
    otherCarsGroup.add(mobs)
    allSprites.add(mobs)
    return mobs

## Shared vars
totalSpeed = 0 # note: this var is positive for forward motion and negative for backwards motion


### Initialize pygame
pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) #setting up screen


### NEW SECTION: Setting up classes

# this class is for the Car the AI (or user) will be driving
class Car(pygame.sprite.Sprite):
    def __init__(self, width, height, mSpeed, accel, turnSpeed, friction, angleRounder):
        super(Car, self).__init__() # initializing the super useful Sprite class
        self.width = width
        self.height = height
        self.surfDims = (width**2 + height**2)**0.5 # using the pythagorean theorem to find the max space a given rect can take up
        self.mSpeed = mSpeed # maximum speed
        self.accel = accel # acceleration rate
        self.friction = friction # amount of friction (makes sure car stops)
        self.surf = pygame.Surface((self.surfDims, self.surfDims))
        self.surf.set_colorkey(colors.BL) # here so that when I rotate everything it makes the extra padding transparent
        self.surf.fill(colors.BL) # using colorkey to make the whole surface transparent
        xDiff = width/2 - self.surfDims/2 # used to setup polygon
        yDiff = height/2 - self.surfDims/2 #used to setup polygon
        self.polyPoints = [(-xDiff, -yDiff), (width - xDiff, -yDiff), (width - xDiff, height - yDiff), (-xDiff, height - yDiff)] # defining initial polygon points
        self.polygon = pygame.draw.polygon(self.surf, colors.W, self.polyPoints) # drawing polygon
        self.mask = pygame.mask.from_surface(self.surf) # getting a bitmask (used for collision, pixel perfect collision for polygon)
        self.rect = self.surf.get_rect() # useful for moving things, etc.
        self.rect.center = ((SCREEN_WIDTH)/2, (SCREEN_HEIGHT)/2) #moving rect to center of the screen
        self.angle = 0 # 0 is set as pointing straight up - used to keep track of the car's angle (matters for sensors)
        self.angleUsed = 0 # used to make sure we don't have super small angles we have to deal with
        self.angleRounder = angleRounder
        self.turnSpeed = turnSpeed # rate at which the car turns - varies dependent on speed of car
        self.maxTurnSpeed = turnSpeed # max rate at which the car can turn
        self.totalSpeed = 0 # used to keep track of speed of car
        self.leftoverSideMovement = 0 # used to keep motion smooth even when motion is less than a bit per frame
        self.leftoverUpMovement = 0
        self.reverseCoefficient = 0.4 # cars move slower when backing up - this*speed = reverseSpeed
        self.angleDiffs = list()
        self.polygonRadius = ((self.polyPoints[0][0]-self.surfDims/2)**2 + (self.polyPoints[0][1]-self.surfDims/2)**2)**0.5
        self.tick = 0

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
        turned = False
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
            self.angleUsed = self.angleRounder * (round((self.angle/(self.angleRounder))))
            if abs(self.angleUsed) < (self.angleRounder)/2 or abs(2*math.pi - self.angleUsed) < (self.angleRounder)/2: self.angleUsed = 0
            turned = True
            
            self.polyPoints = rotate(self.polyPoints, self.polygonRadius, self.angleUsed, self.angleDiffs, (self.surfDims/2, self.surfDims/2)) # using custom rotate function to rotate car            
            self.surf.fill(colors.BL)
            pygame.draw.polygon(self.surf, colors.W, self.polyPoints) #clearing then drawing the new polygon
        if kPressed[K_LEFT]: #rotating car left
            self.angle -= self.turnSpeed
            self.angleUsed = self.angleRounder * (round((self.angle/(self.angleRounder))))
            if abs(self.angleUsed) < (self.angleRounder * math.pi)/2 or abs(2*math.pi - self.angleUsed) < (self.angleRounder * math.pi)/2: self.angleUsed = 0
            turned = True
            
            self.polyPoints = rotate(self.polyPoints, self.polygonRadius, self.angleUsed, self.angleDiffs, (self.surfDims/2, self.surfDims/2)) # using custom rotate function to rotate car            
            self.surf.fill(colors.BL)
            pygame.draw.polygon(self.surf, colors.W, self.polyPoints) #clearing then drawing the new polygon
        
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
        realUpMovement = self.totalSpeed * math.cos(self.angleUsed) + self.leftoverUpMovement
        realSideMovement = self.totalSpeed * math.sin(self.angleUsed) + self.leftoverSideMovement
        roundedUpMovement = realUpMovement.__floor__()
        self.leftoverUpMovement = realUpMovement - roundedUpMovement
        roundedSideMovement = realSideMovement.__floor__()
        self.leftoverSideMovement = realSideMovement - roundedSideMovement

        # useful for things you don't want running every time (i.e. print statements used while debugging)
        self.tick += 1
        if self.tick >= fRate:
            if not turned and abs(self.angle) < (self.turnSpeed)*(5/6) or abs(2*math.pi - self.angleUsed) < (self.angleRounder)*(5/6):
                self.angle = 0
            self.tick = 0

        tSpeed = roundedUpMovement # uses the whole number of the current movement speed
        
        self.rect.move_ip(roundedSideMovement, 0) # moving rect side to side
        
        ## creates a new mask for the new shapemaskSurf
        self.mask.clear()
        self.mask.draw(pygame.mask.from_surface(self.surf), (0, 0)) # you can test this by setting 'self. = self.mask.to_surface(setcolor = (255,0, 0, 255))' then blitting car.maskSurf onto the screen

        return tSpeed # returns the total speed so the screen can be updated
    

class OtherCars(pygame.sprite.Sprite):
    def __init__(self, width, height, speed, spawnPoint):
        super(OtherCars, self).__init__()
        self.width = width
        self.height = height
        self.speed = speed
        self.surf = pygame.surface.Surface((width, height))
        self.rect = self.surf.get_rect()
        self.surf.fill(colors.W)
        self.mask = pygame.mask.from_surface(self.surf)
        self.rect.topleft = spawnPoint
    def update(self, tSpeed):
        self.rect.move_ip(0, -(self.speed-tSpeed))
        self.mask.draw(pygame.mask.from_surface(self.surf), (0,0))

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# this class is for sensors in the form of lines as opposed to arcs
class LineSensor(pygame.sprite.Sprite):
    def __init__(self, startPoint, endPoint, center, length, lWidth, iVal):
        super(LineSensor, self).__init__()
        self.width = lWidth
        self.length = length
        self.p0 = startPoint
        self.p1 = endPoint
        self.sensorType = 'line'
        self.collided = False
        self.surfDims = (lWidth**2 + length**2)**.5
        self.iVal = iVal
        #self.surf = pygame.Surface((self.surfDims, self.surfDims))
        self.surf = pygame.Surface((self.surfDims*2, self.surfDims*2))
        self.surf.fill(colors.BL)
        self.surf.set_colorkey(colors.BL) # says I want everything colored black to actually be transparent
        self.rect = self.surf.get_rect()
        self.line = pygame.draw.line(self.surf, colors.G, startPoint, endPoint, lWidth) # line and not rect is important because that means I can use the rect.clipline() function for collision detection purposes
        self.rect.center = center
        self.amtShown = self.length
        self.pShown = endPoint

        self.p0actual = self.p0[0] + self.rect.x, self.p0[1] + self.rect.y
        self.p1actual = self.p1[0] + self.rect.x, self.p1[1] + self.rect.y

        self.tick = 0
    def update(self, pPoints, cAngle, **kwargs):
        self.p0, self.p1, self.pShown, newCenter = linePointsCalc(pPoints, self.rect.width, self.rect.height, self.length, self.amtShown, cAngle, self.iVal)
        self.rect.center = newCenter
        self.surf.fill(colors.BL)
        self.line = pygame.draw.line(self.surf, colors.G, self.p0, self.pShown, self.width)

        self.p0actual = self.p0[0] + self.rect.x, self.p0[1] + self.rect.y
        self.p1actual = self.p1[0] + self.rect.x, self.p1[1] + self.rect.y

        # self.tick+=1
        # if self.tick >= fRate:
        #     self.tick=0

# this class if for sensors in the form of lines as opposed to arcs
class ArcSensor(pygame.sprite.Sprite):
    def __init__(self, width, height, startAngle, stopAngle, aWidth, iValue):
        super(ArcSensor, self).__init__()
        self.width = width
        self.height = height
        self.iValue = iValue
        self.sensorType = 'arc'
        self.surf = pygame.Surface((width, height))
        self.surf.fill(colors.BL)
        self.surf.set_colorkey(colors.BL) # says I want everything colored black to actually be transparent
        self.rect = self.surf.get_rect()
        self.startAngle = startAngle
        self.stopAngle = stopAngle
        self.arc = pygame.draw.arc(self.surf, colors.G, self.rect, startAngle, stopAngle, aWidth)
        self.aWidth = aWidth
        self.mask = pygame.mask.from_surface(self.surf) # makes a mask (used for collision purposes) out of the arc I just drew
        self.rect.center = arcCenterCalc(car.polyPoints, car.rect.top, car.rect.left, i)
        self.collided = False
    def update(self, pPoints, cAngle, **kwargs):
        cLeft, cTop = kwargs.get('cLeft'), kwargs.get('cTop')
        self.rect.center = arcCenterCalc(pPoints, cTop, cLeft, self.iValue) # updates position to stay with car

        # updating arc on surface
        self.surf.fill(colors.BL)
        self.arc = pygame.draw.arc(self.surf, colors.G, (0,0, self.width, self.height), self.startAngle - cAngle, self.stopAngle - cAngle, self.aWidth)

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
        self.surf.fill(colors.W)
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


### NEW SECTION: Instantiating sprites and sprite groups

## sprite groups
allSprites = pygame.sprite.Group() # mostly for usefulness when using screen.blit()
obstacles = pygame.sprite.Group() # for collision detection purposes
sensors = pygame.sprite.Group() # mostly for how easy it makes calling the update function
hiddenSensors = pygame.sprite.Group() # for when sensors see something and are no longer being blitted
laneLinesGroup = pygame.sprite.Group()
walls = pygame.sprite.Group()
otherCarsGroup = pygame.sprite.Group() # MOBS!!! MUAHAHAHA

mobSpawnTimer = pygame.USEREVENT + 1
pygame.time.set_timer(mobSpawnTimer, 1200) # REPLACE NUMBER WITH VARIABLE

## the car
car = Car(carWidth, carHeight, maxSpeed, acceleration, carTurnSpeed, friction, carAngleRounder)
allSprites.add(car)

## line sensor(s)
lines = []
for i in range(len(lineLengths)): # initializing line sensors
    sD = (lineLengths[i]**2 + sensorWidth**2)**.5
    linePoint0, linePoint1, lineSensorAmtShown, center0 = linePointsCalc(car.polyPoints, 2*sD, sD, lineLengths[i], lineLengths[i], 0, i)
    lines.append(LineSensor(linePoint0, linePoint1, center0, lineLengths[i], sensorWidth, i))
    sensors.add(lines[i]) # please note that the sensors group is bulk added to allSprites


## arc sensors
# using nested for loops to create each individual arc for each sensor
arcs = list() # this list will hold every group of arc sensors, each item in the list will be another list with each individual arc for each individual sensor

for i in range(len(arcAngles)): # this for loop goes through each sensor position, one top right, one top left, one back right, one back left
    # arcs is a list of list, so I'm defining each index of arc as an empty list
    arcs.append([])
    arcsHit.append([])
    # this for loop creates every individual arc within a sensor
    for j in range(arcNumber):
        thisArcSize = arcDistanceMin+arcIncrement*j
        arcs[i].append(ArcSensor(thisArcSize, thisArcSize, arcAngles[i][0], arcAngles[i][1], sensorWidth, i))
        sensors.add(arcs[i][j]) # adding arc to group

# adds each individual arc and line to sensors
allSprites.add(sensors)


## lane lines
laneLines = list()
for i in range(len(lanexPos)): # initializes lane lines
    laneLines.append(list())
    for j in range((math.ceil(SCREEN_HEIGHT/(laneLineHeight*2)))+1):
        thisLaneStartingy = laneLineHeight*2*j
        laneLines[i].append(LaneLine(laneLineWidth, laneLineHeight, lanexPos[i], thisLaneStartingy))
        laneLinesGroup.add(laneLines[i][j])
        allSprites.add(laneLines[i][j])

#### LINES BECAUSE I NEED THEM!!!!!!
for i in range(laneBoundaries):
    x=1

## walls
rightWall = Walls(wallWidth, True, wallColor)
leftWall = Walls(wallWidth, False, wallColor)
walls.add(rightWall)
walls.add(leftWall)
for sprite in walls:
    obstacles.add(sprite)
    allSprites.add(sprite)

running = True
thisT = 0

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running=False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running=False
        elif event.type == mobSpawnTimer:
            spawnMob(mobs, OtherCars, spawnxVal)
            print("MOBS!!! RUN!!!!")

    screen.fill(screenColor)
    
    keyPressed = pygame.key.get_pressed() #figuring out what key was pressed
    totalSpeed = car.update(keyPressed, totalSpeed) #using the pressed key to update the cars position (and, accordingly, the total speed variable)
    otherCarsGroup.update(totalSpeed)
    sensors.update(pPoints = car.polyPoints, cAngle = car.angle, cLeft = car.rect.left, cTop = car.rect.top) #adjusting the sensors so that they stay with the car
    laneLinesGroup.update(totalSpeed)

    # if your car hits the wall, you die
    if pygame.sprite.spritecollideany(car, obstacles, pygame.sprite.collide_mask):
        car.kill()
        running = False

    # finding out if any sensors have been 'hit'
    for sprite in sensors:
        if sprite not in hiddenSensors:
            if sprite.sensorType != 'line':
                if pygame.sprite.spritecollideany(sprite, obstacles, pygame.sprite.collide_mask):
                    allSprites.remove(sprite)
                    hiddenSensors.add(sprite)
                    sprite.collided = True
            else:
                for obstacle in obstacles:
                    if obstacle.rect.clipline(sprite.p0actual, sprite.p1actual):
                        hiddenSensors.add(sprite)
                        sprite.collided = True

                        if obstacle in mobs and thisT == 0:
                            print("that one")
                            print(obstacle.rect.clipline(sprite.p0actual, sprite.p1actual))

                        break

    # finding out if any 'hit' sensors are now 'un-hit'
    for sprite in hiddenSensors:
        if sprite.sensorType != 'line':
            if not pygame.sprite.spritecollideany(sprite, obstacles, pygame.sprite.collide_mask):
                allSprites.add(sprite)
                hiddenSensors.remove(sprite)
                sprite.collided = False
        else:
            collidedOnce = False
            disSquared = 2*(sprite.length)**2
            for obstacle in obstacles:
                p0x, p0y = sprite.p0
                pColls = obstacle.rect.clipline(sprite.p0actual, sprite.p1actual)

                if len(pColls) > 0:
                    pColl0, pColl1 = pColls

                    absxDiff0 = abs((pColl0[0]-p0x))
                    absxDiff1 = abs((pColl1[0]-p0x))

                    if absxDiff0 < absxDiff1:
                        newDisSquared = ((p0x-pColl0[0])**2+(p0y-pColl0[1])**2)
                    elif absxDiff0 != absxDiff1:
                        newDisSquared = ((p0x-pColl1[0])**2+(p0y-pColl1[1])**2)
                    else:
                        absyDiff0 = abs((pColl0[1]-p0y))
                        absyDiff1 = abs((pColl1[1]-p0y))
                        if absyDiff0 < absyDiff1:
                            newDisSquared = ((p0x-pColl0[0])**2+(p0y-pColl0[1])**2)
                        elif absyDiff0 != absyDiff1:
                            newDisSquared = ((p0x-pColl1[0])**2+(p0y-pColl1[1])**2)
                        else:
                            newDisSquared = 0
                    
                    if newDisSquared < disSquared:
                        disSquared = newDisSquared
                    
                    collidedOnce = True
                    
            sprite.amtShown = disSquared**.5

            if not collidedOnce:
                hiddenSensors.remove(sprite)
                sprite.amtShown = sprite.length

    # putting things on screen
    for sprite in allSprites:
        screen.blit(sprite.surf, sprite)

    pygame.display.flip() # updating screen

    thisT+=1
    if thisT >= 30:
        thisT = 0

    clock.tick(fRate) # setting frame rate

pygame.quit()