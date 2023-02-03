# Name: Nathan Yeager
# andrewid: ntyeager


from cmu_112_graphics import *
import random
import sys
import math
import copy
sys.setrecursionlimit(1000000000)

def appStarted(app):
    app.width = 800
    app.height = 800
    app.started = False

def startGame(app):
    #canvas/screen
    app.realWidth = app.realHeight = 5000
    app.rows = app.cols = 30
    app.gridWidth = app.gridHeight = app.realWidth / app.rows

    #zones/map
    (app.map, app.start) = generateMap(app.rows, app.cols)

    #entities
    app.players = []
    app.projectiles = []
    app.monsterProjectiles = []
    app.monsters = []
    app.droppedItems = []

    #player
    app.screenToPlayerRatio = 25
    app.p1 = createArcher(app)
    app.players.append(app.p1)

    #misc.
    app.timerDelay = 25
    app.maxMonsters = 2

    #for view of map in console
    print2dList(app.map)

def createArcher(app):
    x = app.start[1]*app.gridWidth
    y = app.start[0]*app.gridHeight
    height = width = int(min(app.height, app.width)/app.screenToPlayerRatio)
    inventory = [None,None,None,None,None,None,None,None,None,None]
    return Archer(app, x, y, height, width, inventory)

def spawnMonster(app, x, y, zone):
    if zone == 1:
        monster = Zone1Monster(app, x, y)
    else:
        chance = random.randint(1,10)
        if chance <= 3:
            monster = OtherMonster(app, x, y)
        else:
            monster = Zone1Monster(app, x, y)
    app.monsters.append(monster)

def spawnBoss(app, x, y, zone):
    boss = Boss1(app, x, y)
    app.monsters.append(boss)

def getCell(app, x, y):
    col = int(x / app.gridWidth)
    row = int(y / app.gridHeight)
    return app.map[row][col]

def getCellCoordinates(app, x, y):
    col = int(x / app.gridWidth)
    row = int(y / app.gridHeight)
    return (row, col)

#gets cordinate within field of view that lies within the map
def getRandomCoordinateOnScreen(app):
    screenX = random.randint(-app.width/2, app.width/2)
    screenY = random.randint(-app.height/2, app.height/2)
    x = screenX + app.p1.x
    y = screenY + app.p1.y
    if ((x <= 0) or (x >= app.realWidth) or 
        (distanceBetween(x, y, app.p1.x, app.p1.y) <= app.width/3) or
        (y <= 0) or (y >= app.realHeight)):
        return getRandomCoordinateOnScreen(app)
    return (x, y)

def distanceBetween(x1, y1, x2, y2):
    return ((x2-x1)**2 + (y2-y1)**2)**(1/2)

# explanation of A* from 0:00-6:05 of this video:
# https://youtu.be/-L-WgKMFuhE

#### A* Algorithm Functions ##################################################
def generateGrid(app, monster):
    (monsterRow, monsterCol) = getCellCoordinates(app, monster.x, monster.y)
    (playerRow, playerCol) = getCellCoordinates(app, app.p1.x, app.p1.y)
    newMap = copy.deepcopy(app.map)
    newMap[monsterRow][monsterCol] = 'm'
    newMap[playerRow][playerCol] = 'p'
    return (newMap, playerRow, playerCol, monsterRow, monsterCol)

def fillSurroundings(app, starMap, pRow, pCol, mRow, mCol):
    if starMap[mRow][mCol] == 'm':
        distanceTraveled = 0
    else:
        #second value in list is distanceT
        distanceTraveled = starMap[mRow][mCol][1]
    for direction in [(-1,-1),(0,-1),(1,-1),
                      (-1,0),        (1,0),
                      (-1,1), (0,1), (1,1)]:
        nRow = mRow + direction[0]
        nCol = mCol + direction[1]
        if ((nRow < 0) or (nRow >= app.rows) or (nCol < 0) or 
            (nCol >= app.cols) or (starMap[nRow][nCol] == 0)):
            continue
        if ((direction[0] + direction[1] == 0) or 
            (direction[0] + direction[1] == 2) or 
            (direction[0] + direction[1] == -2)):
            #grid length/width set to arbitrary value 10
            distanceT = distanceTraveled + (1 * 10)
        else:
            distanceT = distanceTraveled + (int(math.sqrt(2) * 10))
        distanceAway = distanceBetween(pRow, pCol, nRow, nCol) * 10
        total = distanceT + distanceAway
        if ((type(starMap[nRow][nCol]) == int) or 
            (type(starMap[nRow][nCol]) == str)):
            starMap[nRow][nCol] = [total, distanceT, distanceAway, False]
        else:
            starMap[nRow][nCol] = [total, distanceT, distanceAway, True]
    return starMap

def findBestCell(starMap):
    bestCell = None
    bestTotal = None
    for row in range(len(starMap)):
        for col in range(len(starMap[0])):
            if ((type(starMap[row][col]) == int) or 
                (type(starMap[row][col]) == str) or 
                (starMap[row][col][3] == True)):
                continue
            total = starMap[row][col][0]
            if (bestCell == None) or (total < bestTotal):
                bestCell = (row, col)
                bestTotal = total
    (bestRow, bestCol) = (bestCell[0], bestCell[1])
    return (bestRow, bestCol)

def fillMap(app, starMap, mRow, mCol, pRow, pCol):
    #base recursive case
    for direction in [(-1,-1),(0,-1),(1,-1),
                      (-1,0),        (1,0),
                      (-1,1), (0,1), (1,1)]:
        nRow = mRow + direction[0]
        nCol = mCol + direction[1]
        if ((nRow < 0) or (nRow >= app.rows) or (nCol < 0) or 
            (nCol >= app.cols) or (starMap[nRow][nCol] == 0)):
            continue
        if distanceBetween(nRow, nCol, pRow, pCol) == 0:
            return starMap
    (bestRow, bestCol) = findBestCell(starMap)
    #changes "visited" value to True
    starMap[bestRow][bestCol][3] = True
    starMap = fillSurroundings(app, starMap, pRow, pCol, bestRow, bestCol)
    return fillMap(app, starMap, bestRow, bestCol, pRow, pCol)

def findInversePath(app, starMap, pRow, pCol, mRow, mCol):
    #base recursive case
    for direction in [(-1,-1),(0,-1),(1,-1),
                      (-1,0),        (1,0),
                      (-1,1), (0,1), (1,1)]:
        nRow = pRow + direction[0]
        nCol = pCol + direction[1]
        if ((nRow < 0) or (nRow >= app.rows) or (nCol < 0) or 
            (nCol >= app.cols) or (starMap[nRow][nCol] == 0)):
            continue
        if (nRow == mRow) and (nCol == mCol):
            return []
    bestCell = None
    bestDistanceT = None
    bestDirection = None
    for direction in [(-1,-1),(0,-1),(1,-1),
                      (-1,0),        (1,0),
                      (-1,1), (0,1), (1,1)]:
        nRow = pRow + direction[0]
        nCol = pCol + direction[1]
        if ((nRow < 0) or (nRow >= app.rows) or (nCol < 0) or 
            (nCol >= app.cols) or (starMap[nRow][nCol] == 0)):
            continue
        if ((type(starMap[nRow][nCol]) != int) and 
            (type(starMap[nRow][nCol]) != str) and 
            (starMap[nRow][nCol][3] == True)):
            #second value in map tuple is distanceTraveled
            if (bestCell == None) or (starMap[nRow][nCol][1] < bestDistanceT):
                bestCell = (nRow, nCol)
                bestDistanceT = starMap[nRow][nCol][1]
                bestDirection = direction
    return([bestDirection] + findInversePath(app, starMap, bestCell[0], 
                          bestCell[1], mRow, mCol))

def getPath(app, monster):
    (starMap, pRow, pCol, mRow, mCol) = generateGrid(app, monster)
    starMap = fillSurroundings(app, starMap, pRow, pCol, mRow, mCol)
    starMap = fillMap(app, starMap, mRow, mCol, pRow, pCol)
    inversePath = findInversePath(app, starMap, pRow, pCol, mRow, mCol)
    return inversePath
##############################################################################

def timerFired(app):
    if app.started == True:
        #movement
        if ((app.p1.x < app.realWidth - app.p1.speed) and 
            (getCell(app, app.p1.x + app.p1.speed, app.p1.y) != 0)):
            if 'Right' in app.p1.movement:
                app.p1.x += app.p1.speed
        if ((app.p1.x > app.p1.speed) and 
            (getCell(app, app.p1.x - app.p1.speed, app.p1.y) != 0)):
            if 'Left' in app.p1.movement:
                app.p1.x -= app.p1.speed
        if ((app.p1.y < app.realHeight - app.p1.speed) and 
            (getCell(app, app.p1.x, app.p1.y + app.p1.speed) != 0)):
            if 'Down' in app.p1.movement:
                app.p1.y += app.p1.speed
        if ((app.p1.y > app.p1.speed) and 
            (getCell(app, app.p1.x, app.p1.y - app.p1.speed) != 0)):
            if 'Up' in app.p1.movement:
                app.p1.y -= app.p1.speed

        #check for projectile connection
        for monster in app.monsters:
            for projectile in app.projectiles:
                if (distanceBetween(monster.x, monster.y, projectile.x, 
                                    projectile.y) <= monster.width):
                    monster.health -= projectile.damage
                    app.projectiles.remove(projectile)

        for player in app.players:
            for projectile in app.monsterProjectiles:
                if (distanceBetween(player.x, player.y, projectile.x, 
                                    projectile.y) <= player.width/2):
                    player.health -= projectile.damage
                    app.monsterProjectiles.remove(projectile)

        #moves monsters
        for monster in app.monsters:
            #zone 1 monsters get random movement outside a radius
            if monster.zone == 1:
                if (distanceBetween(monster.x, monster.y, app.p1.x, app.p1.y) >= 
                    (app.width/4)):
                    if monster.isMoving == True:
                        if monster.walkedPixels <= 5:
                            if ((monster.x+monster.dx <= 0) or 
                                (monster.x+monster.dx >= app.realWidth) or 
                                (getCell(app, monster.x+monster.dx, monster.y) == 
                                0)):
                                monster.dx = 0
                            if ((monster.y+monster.dy <= 0) or 
                                (monster.y+monster.dy >= app.realHeight) or 
                                (getCell(app, monster.x, monster.y+monster.dy) == 
                                0)):
                                monster.dy = 0
                            monster.x += monster.dx
                            monster.y += monster.dy
                            monster.walkedPixels += 1
                        else:
                            if monster.walkedPixels >= 15:
                                monster.walkedPixels = 0
                                monster.isMoving = False
                            monster.walkedPixels += 1
                    else:
                        monster.dx = random.randint(-monster.speed,monster.speed)
                        monster.dy = random.randint(-monster.speed,monster.speed)
                        monster.isMoving = True
                else:
                    if monster.cooldown == 0:
                        monster.attack(app)
                        monster.cooldown += 1
                    else:
                        monster.cooldown += 1
                        if monster.cooldown >= monster.maxCooldown:
                            monster.cooldown = 0
            #A* pathfinding if not a zone 1 monster
            else:
                if monster.isBoss == False:
                    monster.path = getPath(app, monster)
                    if len(monster.path) > 0:
                        monster.dx = -(monster.path[-1][1])
                        monster.dy = -(monster.path[-1][0])
                        monster.x += monster.dx * monster.speed
                        monster.y += monster.dy * monster.speed
                    monster.attack(app)

        #boss attacks
        for boss in app.monsters:
            if boss.isBoss == False:
                continue
            else:
                if boss.cooldown == 0:
                    if boss.health > boss.maxHealth/2:
                        boss.attack1(app)
                    elif boss.health <= boss.maxHealth/2:
                        boss.attack2(app)
                    boss.cooldown += 1
                else:
                    boss.cooldown += 1
                    if boss.cooldown >= 15:
                        boss.cooldown = 0
                
        #check for death
        if app.p1.health <= 0:
            app.started = False
        for monster in app.monsters:
            if monster.health <= 0:
                app.monsters.remove(monster)
                monster.dropItem(app)
        
        #moves player projectiles
        if len(app.projectiles) > 0:
            for projectile in app.projectiles:
                projectile.attack(app)
        
        #moves monster projectiles
        if len(app.monsterProjectiles) > 0:
            for projectile in app.monsterProjectiles:
                projectile.attack(app)

        #spawns monsters/bosses
        if len(app.monsters) < app.maxMonsters:
            chance = random.randint(1,20)
            (x, y) = getRandomCoordinateOnScreen(app)
            zone = getCell(app, x, y)
            #1/20 chance of spawning boss, cannot be in first zone
            if (chance == 1) and (zone >= 2):
                spawnBoss(app, x, y, zone)
            #spawns normal enemy otherwise
            elif (chance > 1) and (zone != 0):
                spawnMonster(app, x, y, zone)

        #despawns monsters if not on screen
        for monster in app.monsters:
            if (distanceBetween(monster.x, monster.y, app.p1.x, app.p1.y) >= 
                (app.height/2)*1.5):
                app.monsters.remove(monster)

        #despawns dropped items after x timerFireds
        for item in app.droppedItems:
            item.secondsSpawned += 1
            if item.secondsSpawned >= 250:
                app.droppedItems.remove(item)

        #picking up items
        if None in app.p1.inventory:
            for item in app.droppedItems:
                if (distanceBetween(item.x, item.y, app.p1.x, app.p1.y) <= 
                    min(item.height, item.width)):
                    index = app.p1.inventory.index(None, 2)
                    app.p1.inventory.pop(index)
                    app.p1.inventory.insert(index, item)
                    app.droppedItems.remove(item)

        #leveling up
        if app.p1.experience >= app.p1.experienceToNextLevel:
            app.p1.levelUp(app)

        #regenerating mana
        if app.p1.manaCooldown == 0:
            if app.p1.mana < app.p1.maxMana:
                app.p1.mana += 1
            app.p1.manaCooldown += 1
        else:
            app.p1.manaCooldown += 1
            if app.p1.manaCooldown == 300:
                app.p1.manaCooldown = 0

def keyPressed(app, event):
    if app.started == False:
        if event.key == 'Space':
            app.started = True
            startGame(app)
    if app.started == True:
        #movement
        if len(app.p1.movement) < 2:
            if event.key == 'd':
                if 'Right' not in app.p1.movement:
                    app.p1.movement.append('Right')
            if event.key == 'a':
                if 'Left' not in app.p1.movement:
                    app.p1.movement.append('Left')
            if event.key == 'w':
                if 'Up' not in app.p1.movement:
                    app.p1.movement.append('Up')
            if event.key == 's':
                if 'Down' not in app.p1.movement:
                    app.p1.movement.append('Down')

        #attacking
        if ((len(app.projectiles) == 0) or 
            (app.projectiles[-1].distance >= app.projectiles[-1].cooldown)):
            if event.key == 'Right':
                app.p1.attack(app, 'Right')
            elif event.key == 'Left':
                app.p1.attack(app, 'Left')
            elif event.key == 'Up':
                app.p1.attack(app, 'Up')
            elif event.key == 'Down':
                app.p1.attack(app, 'Down')

        #using items
        if event.key == '1':
            if app.p1.inventory[2] != None:
                app.p1.inventory[2].use(app)
        if event.key == '2':
            if app.p1.inventory[3] != None:
                app.p1.inventory[3].use(app)
        if event.key == '3':
            if app.p1.inventory[4] != None:
                app.p1.inventory[4].use(app)
        if event.key == '4':
            if app.p1.inventory[5] != None:
                app.p1.inventory[5].use(app)
        if event.key == '5':
            if app.p1.inventory[6] != None:
                app.p1.inventory[6].use(app)
        if event.key == '6':
            if app.p1.inventory[7] != None:
                app.p1.inventory[7].use(app)
        if event.key == '7':
            if app.p1.inventory[8] != None:
                app.p1.inventory[8].use(app)
        if event.key == '8':
            if app.p1.inventory[9] != None:
                app.p1.inventory[9].use(app)

        #debugging/spawn a boss
        if event.key == 'b':
            spawnBoss(app, app.p1.x + 100, app.p1.y - 100, 2)

def keyReleased(app, event):
    if app.started == True:
        if event.key == 'd':
            if 'Right' in app.p1.movement:
                app.p1.movement.remove('Right')
        if event.key == 'a':
            if 'Left' in app.p1.movement:
                app.p1.movement.remove('Left')
        if event.key == 'w':
            if 'Up' in app.p1.movement:
                app.p1.movement.remove('Up')
        if event.key == 's':
            if 'Down' in app.p1.movement:
                app.p1.movement.remove('Down')

#modified version of getCellBounds from:
#https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html#exampleGrids
def getCellBounds(app, row, col):
    # returns (x0, y0, x1, y1) corners/bounding box of given cell in grid
    gridWidth  = app.realWidth
    gridHeight = app.realHeight
    cellWidth = gridWidth / app.cols
    cellHeight = gridHeight / app.rows
    #gets x and y coordinates of center of screen
    center = (app.width/2, app.height/2)
    #determines how much to shift each cell by
    shift = (app.p1.x - center[0], app.p1.y - center[1])
    x0 = col * cellWidth - shift[0]
    x1 = (col+1) * cellWidth - shift[0]
    y0 = row * cellHeight - shift[1]
    y1 = (row+1) * cellHeight - shift[1]
    return (x0, y0, x1, y1)

def getFill(app, row, col):
    value = app.map[row][col]
    if value == 0:
        return('black')
    if value == 1:
        return('green')
    if value == 2:
        return('blue')
    if value == 3:
        return('red')
    if value == 4:
        return('orange')
    else:
        return('purple')

def getPlayerBounds(app, x, y, height, width):
    #gets x and y coordinates of center of screen
    center = (app.width/2, app.height/2)
    #determines how much to shift each cell by
    shift = (app.p1.x - center[0], app.p1.y - center[1])
    x0 = (x-width/2) - shift[0]
    x1 = (x+width/2) - shift[0]
    y0 = (y-height/2) - shift[1]
    y1 = (y+height/2) - shift[1]
    return (x0, y0, x1, y1)

def getProjectileBounds(app, direction, x, y, height, width):
    #gets x and y coordinates of center of screen
    center = (app.width/2, app.height/2)
    #determines how much to shift each cell by
    shift = (app.p1.x - center[0], app.p1.y - center[1])
    if (direction == 'Right') or (direction == 'Left'):
        x0 = (x-height/2) - shift[0]
        x1 = (x+height/2) - shift[0]
        y0 = (y-width/2) - shift[1]
        y1 = (y+width/2) - shift[1]
    elif (direction == 'Up') or (direction == 'Down'):
        x0 = (x-width/2) - shift[0]
        x1 = (x+width/2) - shift[0]
        y0 = (y-height/2) - shift[1]
        y1 = (y+height/2) - shift[1]
    return (x0, y0, x1, y1)

def getMonsterProjectileBounds(app, x, y, r):
    center = (app.width/2, app.height/2)
    shift = (app.p1.x - center[0], app.p1.y - center[1])
    x0 = (x-r) - shift[0]
    x1 = (x+r) - shift[0]
    y0 = (y-r) - shift[1]
    y1 = (y+r) - shift[1]
    return (x0, y0, x1, y1)

def getMonsterBounds(app, x, y, height, width):
    #gets x and y coordinates of center of screen
    center = (app.width/2, app.height/2)
    #determines how much to shift each cell by
    shift = (app.p1.x - center[0], app.p1.y - center[1])
    x0 = (x-width/2) - shift[0]
    x1 = (x+width/2) - shift[0]
    y0 = (y-height/2) - shift[1]
    y1 = (y+height/2) - shift[1]
    return (x0, y0, x1, y1)

def getInventoryBounds(app, slot):
    cellWidth = app.width/14
    cellHeight = app.height/14
    #separates first 2 inventory slots
    if slot < 2:
        x0 = cellWidth * (2+slot)
    else:
        x0 = cellWidth * (2+slot) + cellWidth/2
    x1 = x0 + cellWidth
    y0 = app.height * (9/10)
    y1 = y0 + cellHeight
    return (x0, y0, x1, y1)

def redrawAll(app, canvas):
    if app.started == False:
        (x, y) = (app.width/2, app.height/2)
        canvas.create_text(x, app.height/4, text="Darza's Dominion Python", 
                           font='Arial 20 bold')
        canvas.create_text(x, y, text='Press Space to Start', 
                           font='Arial 20 bold')
        canvas.create_text(x, app.height*3/4, 
                           text='WASD to move', font='Arial 16 bold')
        canvas.create_text(x, app.height*3/4+20, 
                           text='Arrow keys to shoot', font='Arial 16 bold')
        canvas.create_text(x, app.height*3/4+40, 
                           text='Keys 1-8 to use inventory slots', 
                           font='Arial 16 bold')
        
    if app.started == True:
        #map/background
        for row in range(app.rows):
            for col in range(app.cols):
                (x0, y0, x1, y1) = getCellBounds(app, row, col)
                fill = getFill(app, row, col)
                canvas.create_rectangle(x0, y0, x1, y1, fill=fill, width=0)
        
        #projectiles
        for projectile in app.projectiles:
            (x0, y0, x1, y1) = getProjectileBounds(app, projectile.direction, 
                                                projectile.x, projectile.y, 
                                                projectile.height, 
                                                projectile.width)
            canvas.create_rectangle(x0, y0, x1, y1, fill='black', width=0)

        #monster projectiles
        for projectile in app.monsterProjectiles:
            (x0, y0, x1, y1) = getMonsterProjectileBounds(app, projectile.x, 
                                                        projectile.y, 
                                                        projectile.radius)
            canvas.create_oval(x0, y0, x1, y1, fill='black', width=1)


        #monsters
        for monster in app.monsters:
            (x0, y0, x1, y1) = getMonsterBounds(app, monster.x, monster.y, 
                                                monster.height, monster.width)
            canvas.create_rectangle(x0, y0, x1, y1, fill='pink', width=1)

        #items on ground ... uses getPlayerBounds as inputs and result are same
        for item in app.droppedItems:
            (x0, y0, x1, y1) = getPlayerBounds(app, item.x, item.y, 
                                            item.height, item.width)
            canvas.create_oval(x0, y0, x1, y1, fill=item.fill, width=1)

        #player
        for player in app.players:
            (x0, y0, x1, y1) = getPlayerBounds(app, player.x, player.y, 
                                            player.height, player.width)
            canvas.create_oval(x0, y0, x1, y1, fill='purple', width=1)

        #inventory
        for slot in range(len(app.p1.inventory)):
            (x0, y0, x1, y1) = getInventoryBounds(app, slot)
            canvas.create_rectangle(x0, y0, x1, y1, fill='blue', width=3)

        for item in app.p1.inventory:
            if item != None:
                index = app.p1.inventory.index(item)
                (x0, y0, x1, y1) = getInventoryBounds(app, index)
                canvas.create_oval(x0, y0, x1, y1, fill=item.fill, width=1)
        
        #health, mana, experience bar
        healthWidth = app.p1.health/app.p1.maxHealth
        manaWidth = app.p1.mana/app.p1.maxMana
        experienceWidth = app.p1.experience/app.p1.experienceToNextLevel

        (hx0, hy0, hx1, hy1) = (10, 10, 10+app.width/5, 30)
        canvas.create_rectangle(hx0, hy0, hx1, hy1, fill='black')
        (mx0, my0, mx1, my1) = (10, 40, 10+app.width/5, 60)
        canvas.create_rectangle(mx0, my0, mx1, my1, fill='black')
        (ex0, ey0, ex1, ey1) = (app.width * (2/5), 10, app.width * (3/5), 30)
        canvas.create_rectangle(ex0, ey0, ex1, ey1, fill='black')

        (hx0, hy0, hx1, hy1) = (10, 10, 10+(app.width/5 * healthWidth), 30)
        canvas.create_rectangle(hx0, hy0, hx1, hy1, fill='red', width=1)
        (mx0, my0, mx1, my1) = (10, 40, 10+(app.width/5 * manaWidth), 60)
        canvas.create_rectangle(mx0, my0, mx1, my1, fill='blue', width=1)
        (ex0, ey0, ex1, ey1) = (app.width * (2/5), 10, (app.width * (2/5)) + 
                                (app.width/5 * experienceWidth), 30)
        canvas.create_rectangle(ex0, ey0, ex1, ey1, fill='yellow')

        #text
        canvas.create_text(app.width/4+10, 20, text=f'Health = {app.p1.health}')
        canvas.create_text(app.width/4+10, 50, text=f'Mana = {app.p1.mana}')
        canvas.create_text(app.width/2, 40, text=f'Level = {app.p1.level}')
        canvas.create_text(app.width*2/9-38, app.height*9/10+15, 
                           text=f'Level {app.p1.level}', 
                           font='Arial 10 bold')
        canvas.create_text(app.width*2/9-38, app.height*9/10+30, text='Bow', 
                           font='Arial 10 bold')
        canvas.create_text(app.width*2/9+20, app.height*9/10+15, 
                           text=f'Level {app.p1.level}', 
                           font='Arial 10 bold')
        canvas.create_text(app.width*2/9+20, app.height*9/10+30, text='Armor', 
                           font='Arial 10 bold')


########### Map Generation Functions ##########################################
def generateStart(rows, cols):
    midCoordinate = random.randint(0,rows)
    otherIndex = random.randint(0,1)
    if otherIndex == 0:
        otherCoordinate = 0
    elif otherIndex == 1:
        otherCoordinate = rows-1
    placement = random.randint(0,1)
    if placement == 0:
        return (midCoordinate, otherCoordinate)
    else:
        return (otherCoordinate, midCoordinate)

def generateBlankMap(rows, cols):
    return [([0] * cols) for row in range(rows)]

def getRandomDirection():
    directions = [(-1,-1),(0,-1),(1,-1),
                  (-1,0),        (1,0),
                  (-1,1), (0,1), (1,1)]
    randomDir = random.randint(0,len(directions)-1)
    return directions[randomDir]

def generateRandomMap(rows, cols, x, y, randomMap, zones, zone, minimum, 
                      count=0):
    #print2dList(randomMap)
    if zone == (zones):
        return
    for direction in [(-1,-1),(0,-1),(1,-1),
                      (-1,0), (0,0), (1,0),
                      (-1,1), (0,1), (1,1)]:
        (newX, newY) = (x+direction[0], y+direction[1])
        if ((newX < 0) or (newX >= rows) or (newY < 0) or 
            (newY >= cols) or (randomMap[newX][newY] != 0)):
            continue
        else:
            randomMap[newX][newY] = zone
            count += 1
    newDir = getRandomDirection()
    x += newDir[0]
    y += newDir[1]
    while ((x < 0) or (x >= rows) or (y < 0) or (y >= cols)):
        x -= newDir[0]
        y -= newDir[1]
        newDir = getRandomDirection()
        x += newDir[0]
        y += newDir[1]
    if count >= minimum:
        generateRandomMap(rows, cols, x, y, randomMap, zones, zone+1, 
                          minimum, 0)
    else:
        generateRandomMap(rows, cols, x, y, randomMap, zones, zone, 
                          minimum, count)

def generateMap(rows, cols):
    zones = 5 #amount of zones wanted
    #generate start coordinate
    start = generateStart(rows, cols)
    (x, y) = (start[0], start[1])
    total = rows * cols
    minimum = total / zones
    startingZone = 1
    randomMap = generateBlankMap(rows, cols)
    generateRandomMap(rows, cols, x, y, randomMap, zones, startingZone, minimum)
    return (randomMap, start)
###############################################################################

#Player classes
class Player(object):
    def __init__(self, app, x, y, height, width, inventory):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.inventory = inventory
        self.speed = 10
        self.health = 100
        self.mana = 10
        self.movement = []

class Archer(Player):
    def __init__(self, app, x, y, height, width, inventory):
        super().__init__(app, x, y, height, width, inventory)
        self.health = 150
        self.maxHealth = 150
        self.mana = 15
        self.manaCooldown = 0
        self.maxMana = 15
        self.speed = 8
        self.damage = 501
        self.experience = 0
        self.experienceToNextLevel = 10
        self.level = 0
    def attack(self, app, direction):
        bow = app.p1.inventory[0]
        if bow == None:
            app.arrow = DefaultArrow(app, direction, self.damage)
            app.projectiles.append(app.arrow)
    def levelUp(self, app):
        self.maxHealth = int(self.maxHealth * 1.1)
        self.maxMana = int(self.maxMana * 1.1)
        self.mana = self.maxMana
        self.damage = int(self.damage * 1.1)
        self.experience -= self.experienceToNextLevel
        self.experienceToNextLevel = int(self.experienceToNextLevel * 1.5)
        self.level += 1

#Entity Classes
class DefaultArrow(object):
    def __init__(self, app, direction, damage):
        self.damage = damage
        self.direction = direction
        self.height = 25
        self.width = 5
        self.speed = 5
        self.x = app.p1.x
        self.y = app.p1.y
        self.maxDistance = min(app.width, app.height)/4
        self.distance = 0
        self.cooldown = self.maxDistance/10
    def attack(self, app):
        if self.direction == 'Right':
            self.x += self.speed
        elif self.direction == 'Left':
            self.x -= self.speed
        elif self.direction == 'Up':
            self.y -= self.speed
        elif self.direction == 'Down':
            self.y += self.speed
        self.distance += self.speed
        if self.distance >= self.maxDistance:
            app.projectiles.remove(self)

#Monster Classes
class Monster(object):
    def __init__(self, app, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.damage = 10
        self.speed = 5
        self.height = 25
        self.width = 25

class Zone1Monster(Monster):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
        self.dx = 0
        self.dy = 0
        self.zone = 1
        self.health = 50
        self.speed = 5
        self.height = 25
        self.width = 25
        self.isMoving = False
        self.walkedPixels = 0
        self.cooldown = 0
        self.maxCooldown = 20
        self.isBoss = False
    def attack(self, app):
        direction = (app.p1.x-self.x, app.p1.y-self.y)
        app.z1Projectile = Zone1Projectile(app, direction, self.x, self.y)
        app.monsterProjectiles.append(app.z1Projectile)
    def dropItem(self, app):
        app.p1.experience += 5
        chance = random.randint(1,10)
        if chance <= 5:
            app.smallPotion = SmallPotion(app, self.x, self.y)
            app.droppedItems.append(app.smallPotion)

class OtherMonster(Monster):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
        self.dx = 0
        self.dy = 0
        self.zone = 2
        self.damage = 5
        self.health = 100
        self.speed = 5
        self.height = 20
        self.width = 40
        self.isMoving = False
        self.walkedPixels = 0
        self.cooldown = 0
        self.maxCooldown = 25
        self.path = []
        self.isBoss = False
    def attack(self, app):
        direction = (app.p1.x-self.x, app.p1.y-self.y)
        app.otherProjectile = OtherProjectile(app, direction, self.x, self.y)
        app.monsterProjectiles.append(app.otherProjectile)
    def dropItem(self, app):
        app.p1.experience += 10
        chance = random.randint(1,10)
        if chance <= 3:
            app.smallPotion = SmallPotion(app, self.x, self.y)
            app.droppedItems.append(app.smallPotion)
        elif chance >= 7:
            app.mediumPotion = MediumPotion(app, self.x, self.y)
            app.droppedItems.append(app.mediumPotion)

#monster projectiles
class MonsterProjectile(object):
    def __init__(self, app, direction, x, y):
        self.x = x
        self.y = y
        self.direction = direction
        self.radius = 2

class Zone1Projectile(MonsterProjectile):
    def __init__(self, app, direction, x, y):
        super().__init__(app, direction, x, y)
        self.damage = 5
        self.radius = 5
        self.maxDistance = app.width/3
        self.distance = 0
        self.speed = 5
        self.dx = 0
        self.dy = 0
    def attack(self, app):
        if self.dx == 0 and self.dy == 0:
            distance = distanceBetween(self.x, self.y, app.p1.x, app.p1.y)
            timesX = distance/self.speed
            timesY = distance/self.speed
            self.dx = self.direction[0]/timesX
            self.dy = self.direction[1]/timesY
        self.x += self.dx
        self.y += self.dy
        self.distance += self.speed
        if self.distance >= self.maxDistance:
            app.monsterProjectiles.remove(self)

class OtherProjectile(MonsterProjectile):
    def __init__(self, app, direction, x, y):
        super().__init__(app, direction, x, y)
        self.damage = 1
        self.radius = 10
        self.maxDistance = app.width/3
        self.distance = 0
        self.speed = 20
        self.dx = 0
        self.dy = 0
    def attack(self, app):
        if self.dx == 0 and self.dy == 0:
            distance = distanceBetween(self.x, self.y, app.p1.x, app.p1.y)
            timesX = distance/self.speed
            timesY = distance/self.speed
            self.dx = self.direction[0]/timesX
            self.dy = self.direction[1]/timesY
        self.x += self.dx
        self.y += self.dy
        self.distance += self.speed
        if self.distance >= self.maxDistance:
            app.monsterProjectiles.remove(self)

#bosses
class Boss(object):
    def __init__(self, app, x, y):
        self.x = x
        self.y = y
        self.height = self.width = 50

class Boss1(Boss):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
        self.height = self.width = 80
        self.health = 1000
        self.maxHealth = 1000
        self.cooldown = 0
        self.trackingCooldown = 0
        self.zone = 2
        self.isBoss = True
    def attack1(self, app):
        for direction in [(-1,-1),(0,-1),(1,-1),
                          (-1,0),        (1,0),
                          (-1,1), (0,1), (1,1)]:
            app.phase1Projectile = Phase1Projectile(app, direction, 
                                                    self.x, self.y)
            app.monsterProjectiles.append(app.phase1Projectile)
        if self.trackingCooldown == 0:
            app.trackingProjectile = TrackingProjectile(app, (0,0), self.x, self.y)
            app.monsterProjectiles.append(app.trackingProjectile)
            self.trackingCooldown += 1
        else:
            self.trackingCooldown += 1
            if self.trackingCooldown == 3:
                self.trackingCooldown = 0
    def attack2(self, app):
        for direction in [      (0,-1),
                          (-1,0),      (1,0),
                                (0,1)       ]:
            app.phase1Projectile = Phase1Projectile(app, direction, 
                                                    self.x, self.y)
            app.monsterProjectiles.append(app.phase1Projectile)
        direction = (app.p1.x-self.x, app.p1.y-self.y)
        app.phase2Projectile = Phase2Projectile(app, direction, self.x, self.y)
        app.monsterProjectiles.append(app.phase2Projectile)
    def dropItem(self, app):
        app.p1.experience += 500

class Phase1Projectile(MonsterProjectile):
    def __init__(self, app, direction, x, y):
        super().__init__(app, direction, x, y)
        self.damage = 25
        self.radius = 10
        self.maxDistance = app.width/2
        self.distance = 0
        self.speed = 10
        self.dx = 0
        self.dy = 0
    def attack(self, app):
        if self.dx == 0 and self.dy == 0:
            self.dx = self.direction[0]
            self.dy = self.direction[1]
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.distance += self.speed
        if self.distance >= self.maxDistance:
            app.monsterProjectiles.remove(self)

class Phase2Projectile(MonsterProjectile):
    def __init__(self, app, direction, x, y):
        super().__init__(app, direction, x, y)
        self.damage = 20
        self.radius = 40
        self.maxDistance = app.width/2
        self.distance = 0
        self.speed = 8
        self.dx = 0
        self.dy = 0
    def attack(self, app):
        if self.dx == 0 and self.dy == 0:
            distance = distanceBetween(self.x, self.y, app.p1.x, app.p1.y)
            timesX = distance/self.speed
            timesY = distance/self.speed
            self.dx = self.direction[0]/timesX
            self.dy = self.direction[1]/timesY
        self.x += self.dx
        self.y += self.dy
        self.distance += self.speed
        if self.distance >= self.maxDistance:
            app.monsterProjectiles.remove(self)

class TrackingProjectile(MonsterProjectile):
    def __init__(self, app, direction, x, y):
        super().__init__(app, direction, x, y)
        self.damage = 50
        self.radius = 8
        self.maxDistance = app.width/3
        self.distance = 0
        self.speed = 2
        self.dx = 0
        self.dy = 0
    def attack(self, app):
        self.direction = (app.p1.x-self.x, app.p1.y-self.y)
        distance = distanceBetween(self.x, self.y, app.p1.x, app.p1.y)
        timesX = distance/self.speed
        timesY = distance/self.speed
        self.dx = self.direction[0]/timesX
        self.dy = self.direction[1]/timesY
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.distance += self.speed
        if self.distance >= self.maxDistance:
            app.monsterProjectiles.remove(self)

#dropped items
class Item(object):
    def __init__(self, app, x, y):
        self.x = x
        self.y = y
        self.secondsSpawned = 0

class SmallPotion(Item):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
        self.height = 20
        self.width = 20
        self.fill = 'red'
        self.heal = 20
        self.mana = -1
    def use(self, app):
        app.p1.health += self.heal
        app.p1.mana += self.mana
        if app.p1.health > app.p1.maxHealth:
            app.p1.health = app.p1.maxHealth
        index = app.p1.inventory.index(self)
        app.p1.inventory.remove(self)
        app.p1.inventory.insert(index, None)

class MediumPotion(Item):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
        self.height = 20
        self.width = 20
        self.fill = 'orange'
        self.heal = 40
        self.mana = -2
    def use(self, app):
        app.p1.health += self.heal
        app.p1.mana += self.mana
        if app.p1.health > app.p1.maxHealth:
            app.p1.health = app.p1.maxHealth
        index = app.p1.inventory.index(self)
        app.p1.inventory.remove(self)
        app.p1.inventory.insert(index, None)


################## Debugging/Scrap ############################################
#from https://www.cs.cmu.edu/~112/notes/notes-2d-lists.html
def maxItemLength(a):
    maxLen = 0
    rows = len(a)
    cols = len(a[0])
    for row in range(rows):
        for col in range(cols):
            maxLen = max(maxLen, len(str(a[row][col])))
    return maxLen

# Because Python prints 2d lists on one row,
# we might want to write our own function
# that prints 2d lists a bit nicer.
def print2dList(a):
    if (a == []):
        # So we don't crash accessing a[0]
        print([])
        return
    rows, cols = len(a), len(a[0])
    fieldWidth = maxItemLength(a)
    print('[')
    for row in range(rows):
        print(' [ ', end='')
        for col in range(cols):
            if (col > 0): print(', ', end='')
            print(str(a[row][col]).rjust(fieldWidth), end='')
        print(' ]')
    print(']')
##############################################################################


runApp(width=800, height=800)