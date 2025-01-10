import pygame, time, sys, random, math
pygame.init()

vec2 = pygame.math.Vector2

res = vec2(1280,640)

window = pygame.display.set_mode(res)

def scaleUp(img, scale=1):
    w,h = img.get_size()
    return pygame.transform.scale(img, (w*scale, h*scale)).convert_alpha()

def loadImage(path, scale=1):
    img = pygame.image.load(path).convert_alpha()
    return scaleUp(img, scale)

def clamp(val, mini, maxi):
    if val >= maxi:
        return maxi
    if val <= mini:
        return mini
    return val


def distance(v1, v2):
    return math.sqrt(math.pow(v2.x - v1.x, 2) + math.pow(v2.y - v1.y, 2))

### required classes
class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.timer = 0
        self.finsied = False
    
    def update(self, deltaTime):
        self.timer += deltaTime
        if self.timer >= self.duration:
            self.finsied = True

    def percentCompleted(self):
        return clamp(self.timer/self.duration, 0, 1)

    def isOver(self):
        return self.finsied
    
    def end(self):
        self.timer = 0
        self.finsied = True

    def reset(self):
        self.timer = 0
        self.finsied = False

class Cell:
    def __init__(self, pos, size, typeC="none"):
        self.pos = pos + size/2
        self.size = size
        self.type = typeC


        self.flagged = False  ### flaggign as done in the original game

        self.value = 0
        self.textImage = None
        self.textRect = None

        # self.rect = self.surf.get_rect(center=self.pos)
        self.rect = pygame.Rect(0, 0, size.x, size.y)
        self.rect.center = self.pos

        self.isHovered = False

        self.isRevealed = False

        self.revealStartTimer = None
        
        self.revealTime = 0.5
        self.revealTimer = Timer(self.revealTime)
        self.revealAnimating = False
        self.revealValue = 0
        self.startRevealing = False


        self.revealCoverShow = False ### showing the white fillered rect

        self.revealRect = self.rect.copy()

    def flagit(self):
        self.flagged = not self.flagged

    def setValue(self, value, textImage):
        self.value = value
        self.textImage = textImage
        self.textRect = self.textImage.get_rect(center=self.pos)

    def reveal(self, time=1):
        self.revealAnimating = True
        self.revealStartTimer = Timer(time-self.revealTime)


    def update(self, dt=1/60):
        mousePos = vec2(*pygame.mouse.get_pos())

        self.isHovered = False
        if self.rect.collidepoint(mousePos):
            self.isHovered = True

        # if pygame.mouse.get_pressed()[0]:
        #     if self.isHovered:
        #         print(self.value)

        if self.revealAnimating and not self.startRevealing:
            self.revealStartTimer.update(dt)

            if self.revealStartTimer.percentCompleted() >= 0.80:
                self.revealCoverShow = True

            if self.revealStartTimer.isOver():
                self.startRevealing = True
                self.revealCoverShow = True
                # self.isRevealed = True

        if self.startRevealing:
            self.revealTimer.update(dt)

            factor = (1-self.revealTimer.percentCompleted())

            self.revealRect.height = self.rect.height * factor
            self.revealRect.width = self.rect.width * factor

            self.revealRect.center = self.rect.center

            if self.revealTimer.isOver():
                self.startRevealing = False
                self.isRevealed = True
                self.revealCoverShow = False
        


    def draw(self, window):
        if self.isRevealed:
            if self.textImage:
                window.blit(self.textImage, self.textRect)

        if self.revealAnimating and self.revealCoverShow:
            if self.textImage:
                window.blit(self.textImage, self.textRect)
            pygame.draw.rect(window, (255,255,255), self.revealRect)


        if self.isHovered:
            pygame.draw.rect(window, (255,255,255), self.rect, 7)

        if self.flagged:
            pygame.draw.rect(window, (255,20,20), self.rect, 5)
            pygame.draw.line(window, (255,20,20), self.rect.topleft, self.rect.bottomright, 5)
            pygame.draw.line(window, (255,20,20), self.rect.topright, self.rect.bottomleft, 5)

class SineAnimation:
    def __init__(self, extreme, duration, base=0, nonNegative=False, nonPositive=False, variable=False, secondHalf=0.5):
        self.PI = 3.141
        self.base = base
        self.firstHaldExtreme = extreme
        self.duration = duration
        self.nonNegative = nonNegative
        self.nonPositive = nonPositive
        self.variable = variable
        self.secondHalfExtreme = secondHalf

        self.extreme = self.firstHaldExtreme

        self.speed = 2*self.PI/self.duration

        self.angle = 0

        self.value = 0
        self.counter = 0

        self.over = False

    def update(self, deltaTime):
        if not self.over:
            self.angle += self.speed * deltaTime

            if self.nonNegative:
                self.value = self.base + (abs(math.sin(self.angle))) * self.extreme
                # print(self.base)
            elif self.nonPositive:
                self.value = self.base - abs(math.sin(self.angle)) * self.extreme
            else:
                self.value = self.base + math.sin(self.angle) * self.extreme

            # if math.sin(self.angle) == 0:d

            if self.angle >= self.PI:
                if self.variable:
                    self.extreme = self.secondHalfExtreme
            else:
                self.extreme = self.firstHaldExtreme

            if self.angle >= self.PI*2:
                self.over = True
                self.angle = 0

    def restart(self):
        self.angle = 0
        self.over = False


    def continueRunning(self):
        self.over = False

    def getValue(self):
        return self.value

    def isOver(self):
        return self.over

### end


### minesweeper class
class Minesweeper:
    def __init__(self, res):
        self.res = res

        self.surf = pygame.Surface(res)
        self.surf.fill((0,0,0))
        self.surf.set_alpha(0)

        self.cellSize  = vec2(64, 64)
        self.numCells = vec2(self.res.x//self.cellSize.x, self.res.y//self.cellSize.y)

        self.grid = []

        self.depthIncrease = 0.5
        self.depthBase = 0.2
        self.depthFactor = 1/3

        self.gameOver = False
        self.gameOverStartAnim = False
        self.gameOverTimer = Timer(1.5)
        self.gameState = None


        self.font = pygame.font.Font("cute_love.ttf", 80)

        self.restartText = self.font.render("Press [R] to restart", True, (200,200,200), None)
        self.restartTextBase = self.font.render("Press [R] to restart", True, (200,200,200), None)
        self.restartAnimRot = SineAnimation(5, 0.9)
        self.restartAnimScale = SineAnimation(0.15, 0.6, 1)
        self.restartTextRect = self.restartText.get_rect(center=(self.res.x//2, self.res.y*0.75))


        self.gameStateText = None
        self.gameTextRect = None


        self.generate()

    def generate(self):
        self.grid.clear()

        self.numMines = 18

        minesPlaced = 0
        for y in range(int(self.numCells.y)):

            self.grid.append([])

            for x in range(int(self.numCells.x)):

                if random.random() < 0.1 and minesPlaced < self.numMines:
                    minesPlaced += 1
                    self.grid[y].append(Cell(vec2(x*self.cellSize.x, y*self.cellSize.y), self.cellSize, "mine"))

                else:
                    self.grid[y].append(Cell(vec2(x*self.cellSize.x, y*self.cellSize.y), self.cellSize))

        self.assignValues()

    def assignValues(self):
        font = pygame.font.Font("cute_love.ttf", 35)

        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                # print(y,x, len(grid))
                cell = self.grid[y][x]

                global numMines
                numMines = 0
                neighBours = 0
                
                if cell.type == "none":
                    for i in range(y-1, y+2):
                        for j in range(x-1, x+2):
                            if (i >= 0 and j >= 0):
                                if (i < len(self.grid) and j < len(self.grid[y])):
                                    if self.grid[i][j].type == "mine":
                                        numMines += 1
                            neighBours += 1
                else:
                    numMines = "x"

                cell.setValue(numMines, font.render(str(numMines), True, (200,200,200), None))

    def startRevealing(self, x, y, depth):
        ### check if the point or eleemnt is in the bounds 
        if x < 0 or x >= len(self.grid[0]):
            return -1
        if y < 0 or y >= len(self.grid):
            return -1
        

        ### ensuring we do not go again on a cell already checked
        if not self.grid[y][x].revealAnimating:

            if self.grid[y][x].value != 0:
                self.grid[y][x].reveal(self.depthBase + depth*self.depthFactor)
                
            elif self.grid[y][x].value == 0:

                self.grid[y][x].reveal(self.depthBase + depth*self.depthFactor)

                self.startRevealing(x-1, y-1, depth + self.depthIncrease)
                self.startRevealing(x-1, y, depth + self.depthIncrease)
                self.startRevealing(x-1, y+1, depth + self.depthIncrease)

                self.startRevealing(x, y-1, depth + self.depthIncrease)
                self.startRevealing(x, y+1, depth + self.depthIncrease)

                self.startRevealing(x+1, y-1, depth + self.depthIncrease)
                self.startRevealing(x+1, y, depth + self.depthIncrease)
                self.startRevealing(x+1, y+1, depth + self.depthIncrease)
        
    def drawGrids(self, window):
        for i in range(int(self.numCells.x)):
            pygame.draw.line(window, (200,200,200), (i*self.cellSize.x, 0), (i*self.cellSize.x, res.y))

        for j in range(int(self.numCells.y)):
            pygame.draw.line(window, (200,200,200), (0, j*self.cellSize.y), (res.x, j*self.cellSize.y))

    def eventUpdate(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.gameOver:
                self.generate()

                self.gameOver = False
                self.gameOverStartAnim = False
                self.gameOverTimer = Timer(1.5)
                self.gameState = None


                self.restartText = self.font.render("Press [R] to continue", True, (200,200,200), None)
                self.restartTextBase = self.font.render("Press [R] to continue", True, (200,200,200), None)
                self.restartAnimRot = SineAnimation(5, 0.9)
                self.restartAnimScale = SineAnimation(0.15, 0.6, 1)
                self.restartTextRect = self.restartText.get_rect(center=(self.res.x//2, self.res.y*0.75))


                self.gameStateText = None
                self.gameTextRect = None


        if not self.gameOver:
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    xpos,ypos = pygame.mouse.get_pos()
                    y = int(ypos//self.cellSize.y)
                    x = int(xpos//self.cellSize.x)


                    if self.grid[y][x].value == "x":
                        #### game over - lost
                        self.grid[y][x].isRevealed = True


                        self.gameOverStartAnim= True
                        self.gameState = "lost"


                    else:
                        self.startRevealing(x, y, 0)
                elif event.button == 3:
                    xpos,ypos = pygame.mouse.get_pos()
                    y = int(ypos//self.cellSize.y)
                    x = int(xpos//self.cellSize.x)

                    self.grid[y][x].flagit()     

        # print(self.gameState)


    def updateAndDraw(self,dt, window):
        self.cellsNonRevealed = 0
        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                if not self.gameOver:
                    self.grid[y][x].update(dt)
                self.grid[y][x].draw(window)

                if not self.grid[y][x].isRevealed:
                    self.cellsNonRevealed += 1

        if self.cellsNonRevealed == self.numMines and not self.gameOver:
            #### game over - won
            self.gameOverStartAnim = True
            self.gameState = "won"

        if self.gameOverStartAnim:
            self.gameOverTimer.update(dt)

            #### setting game state text
            if not self.gameStateText:
                self.gameStateText = self.font.render(f"You {self.gameState.capitalize()}", True, (200,200,200), None)
                self.gameTextRect = self.gameStateText.get_rect(center=(self.res.x//2, self.res.y * 0.25))

            factor = (self.gameOverTimer.percentCompleted())**2
            alpha = 255 * factor

            self.surf.set_alpha(alpha)

            if self.gameOverTimer.isOver():
                self.gameOver = True

        self.drawGrids(window)

        ### drawing onto the surface
        if self.gameOverStartAnim or self.gameOver:
            self.surf.fill((0,0,0))

            self.restartAnimRot.update(dt)
            self.restartAnimScale.update(dt)

            if self.restartAnimScale.isOver():
                self.restartAnimScale.restart()

            if self.restartAnimRot.isOver():
                self.restartAnimRot.restart()

            self.restartText = pygame.transform.rotozoom(self.restartTextBase, -self.restartAnimRot.getValue(), self.restartAnimScale.getValue())


            self.restartTextRect = self.restartText.get_rect(center=(self.res.x//2, self.res.y*0.75))
            # self.gameTextRect = self.gameStateText.get_rect(center=(self.res.x//2, self.res.y * 0.25))

            self.surf.blit(self.gameStateText, self.gameTextRect)
            self.surf.blit(self.restartText, self.restartTextRect)


            window.blit(self.surf, (0, 0))


clock = pygame.time.Clock()
dt = 1/60
fps = 60


ms = Minesweeper(res)

while 1:
    clock.tick(1000000)
    window.fill((30,30,30))


    fps = clock.get_fps() 

    dt = 1/fps if fps else 1/60

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        ms.eventUpdate(event)
        
    
    ms.updateAndDraw(dt, window)
    

    pygame.display.flip()
