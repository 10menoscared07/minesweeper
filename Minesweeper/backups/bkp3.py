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



cellSize  = vec2(64, 64)
numCells = vec2(res.x//cellSize.x, res.y//cellSize.y)

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


grid = []


def generate():
    global grid
    grid.clear()
    for y in range(int(numCells.y)):
        grid.append([])
        for x in range(int(numCells.x)):
            if random.random() < 0.1:
                grid[y].append(Cell(vec2(x*cellSize.x, y*cellSize.y), cellSize, "mine"))
            else:
                grid[y].append(Cell(vec2(x*cellSize.x, y*cellSize.y), cellSize))

    assignValues()

def assignValues():
    global grid

    font = pygame.font.Font("cute_love.ttf", 35)


    for y in range(int(numCells.y)):
        for x in range(int(numCells.x)):
            # print(y,x, len(grid))
            cell = grid[y][x]

            global numMines
            numMines = 0
            neighBours = 0
            
            if cell.type == "none":
                for i in range(y-1, y+2):
                    for j in range(x-1, x+2):
                        if (i >= 0 and j >= 0):
                            if (i < len(grid) and j < len(grid[y])):
                                if grid[i][j].type == "mine":
                                    numMines += 1
                        neighBours += 1
            else:
                numMines = "x"

            cell.setValue(numMines, font.render(str(numMines), True, (200,200,200), None))


depthIncrease = 0.5
depthBase = 0.2
depthFactor = 1/3


def startRevealing(x, y, depth):
    if x<0 or x>=len(grid[0]):
        return -1
    if y < 0 or y >= len(grid):
        return -1
    
    if not grid[y][x].revealAnimating:

        if grid[y][x].value != 0:
            grid[y][x].reveal(depthBase + depth*depthFactor)
            
        elif grid[y][x].value == 0:

            grid[y][x].reveal(depthBase + depth*depthFactor)

            startRevealing(x-1, y-1, depth + depthIncrease)
            startRevealing(x-1, y, depth + depthIncrease)
            startRevealing(x-1, y+1, depth + depthIncrease)

            startRevealing(x, y-1, depth + depthIncrease)
            startRevealing(x, y+1, depth + depthIncrease)

            startRevealing(x+1, y-1, depth + depthIncrease)
            startRevealing(x+1, y, depth + depthIncrease)
            startRevealing(x+1, y+1, depth + depthIncrease)
    

def drawGrids(window):
    for i in range(int(numCells.x)):
        pygame.draw.line(window, (200,200,200), (i*cellSize.x, 0), (i*cellSize.x, res.y))

    for j in range(int(numCells.y)):
        pygame.draw.line(window, (200,200,200), (0, j*cellSize.y), (res.x, j*cellSize.y))

generate()

clock = pygame.time.Clock()
dt = 1/60
fps = 60

while 1:
    clock.tick(1000000)
    window.fill((30,30,30))


    fps = clock.get_fps() 

    dt = 1/fps if fps else 1/60

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                generate()
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                xpos,ypos = pygame.mouse.get_pos()
                y = int(ypos//cellSize.y)
                x = int(xpos//cellSize.x)

                startRevealing(x, y, 0)
            elif event.button == 3:
                xpos,ypos = pygame.mouse.get_pos()
                y = int(ypos//cellSize.y)
                x = int(xpos//cellSize.x)

                grid[y][x].flagit()             


    for y in range(int(numCells.y)):
        for x in range(int(numCells.x)):
            grid[y][x].update(dt)
            grid[y][x].draw(window)
            

    drawGrids(window)

    pygame.display.flip()
