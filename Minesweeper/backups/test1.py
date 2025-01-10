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

        self.isRevealed = True

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

        # self.isHovered = False
        # if self.rect.collidepoint(mousePos):
        #     self.isHovered = True

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

### end


### minesweeoer class
class Minesweeper:
    def __init__(self, res, pos):
        self.res = res

        self.pos = pos

        self.surf = pygame.Surface(res)

        self.rect =self.surf.get_rect(center=self.pos)

        self.cellSize  = vec2(32, 32)
        self.numCells = vec2(self.res.x//self.cellSize.x, self.res.y//self.cellSize.y)

        self.grid = []

        self.depthIncrease = 0.5
        self.depthBase = 0.2
        self.depthFactor = 1/3


        self.generate()

    def generate(self):
        self.grid.clear()
        for y in range(int(self.numCells.y)):

            self.grid.append([])

            for x in range(int(self.numCells.x)):

                if random.random() < 0.1:
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
        for i in range(int(self.numCells.x)+2):
            pygame.draw.line(window, (200,200,200), (i*self.cellSize.x, 0), (i*self.cellSize.x, res.y))

        for j in range(int(self.numCells.y)+2):
            pygame.draw.line(window, (200,200,200), (0, j*self.cellSize.y), (res.x, j*self.cellSize.y))



    def eventUpdate(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.generate()
            
        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                mousePos = pygame.mouse.get_pos()
                xpos,ypos = mousePos[0] - self.pos.x - self.res.x//2, mousePos[1] - self.pos.y - self.res.y//2
                y = int(ypos//self.cellSize.y)
                x = int(xpos//self.cellSize.x)

                self.startRevealing(x, y, 0)


            elif event.button == 3:
                mousePos = pygame.mouse.get_pos()
                xpos,ypos = mousePos[0] - self.pos.x - self.res.x//2, mousePos[1] - self.pos.y - self.res.y//2
                y = int(ypos//self.cellSize.y)
                x = int(xpos//self.cellSize.x)

                self.grid[y][x].flagit()     


    def inBounds(self, i ,j):
        if i >= 0 and i < len(self.grid[0]):
            if j >= 0 and j < len(self.grid):
                return 1
            
        return 0

    def update(self,dt):
        self.surf.fill((30,30,30))
        mousePos = pygame.mouse.get_pos()
        xpos,ypos = mousePos[0] - self.pos.x - self.res.x//2, mousePos[1] - self.pos.y - self.res.y//2
        ym = int(ypos//self.cellSize.y)
        xm = int(xpos//self.cellSize.x)
        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                self.grid[y][x].update(dt)

                self.grid[y][x].isHovered = False
                if self.inBounds(ym, xm):
                    self.grid[ym][xm].isHovered = True

                self.grid[y][x].draw(self.surf)
                # print("d")
            
        self.drawGrids(self.surf)

    def draw(self, window):
        
        
        window.blit(self.surf, self.rect)



clock = pygame.time.Clock()
dt = 1/60
fps = 60


ms = Minesweeper(vec2(res.x//2, res.y//2), vec2(res.x//2, res.y//2))

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
        
    
    ms.update(dt)
    ms.draw(window)
    

    pygame.display.flip()
