import pygame
import sys
import os
import settings as st
from messageEngine import MessageEngine

CS = 32 # cell size
SCREEN_RECT = pygame.Rect(0, 0, CS*25, CS*20)
SCREEN_NCOL = SCREEN_RECT.width // CS
SCREEN_NROW = SCREEN_RECT.height // CS
SCREEN_CENTER_X = SCREEN_RECT.width // 2 // CS
SCREEN_CENTER_Y = SCREEN_RECT.height // 2 // CS

def load_image(filename):
    image = pygame.image.load(filename).convert_alpha()
    return image

def get_image(sheet, x, y, width, height, useColorKey=False):
    image = pygame.Surface([width, height])
    image.blit(sheet, (0, 0), (x, y, width, height)) # source, dest, area
    image.convert()
    if useColorKey:
        colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image

class Cursor:
    def __init__(self):
        self.wx, self.wy = 1, 1
        self.map = None

    def set_map(self, map_):
        self.map = map_

    def handle_keys(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_DOWN] and self.wy < self.map.nrow:
            self.wy += 1
        elif pressed_keys[pygame.K_LEFT] and self.wx > 0:
            self.wx -= 1
        elif pressed_keys[pygame.K_RIGHT] and self.wx < self.map.ncol:
            self.wx += 1
        elif pressed_keys[pygame.K_UP] and self.wy > 0:
            self.wy -= 1
 
    def update(self):
        self.handle_keys()

SAVE_WAIT_COUNT = 120

class Map:
    COLOR = (255, 0, 0)
    WIDTH = 1
    LAYER_BOTTOM = 1
    LAYER_TOP = 2
    LAYER_BOTH = 3
    showGrid = False
    def __init__(self, screen, cursor, palette):
        self.ncol = 0
        self.nrow = 0
        self.screen = screen
        self.cursor = cursor
        self.palette = palette
        self.defaultPaletteIdx = st.defaultPaletteIdx
        self.defaultIdx = st.defaultIdx
        self.mapDataBottom = []
        self.mapDataTop = []
        self.layer = self.LAYER_TOP
        self.save_cnt = 0
        self.load_cnt = 0
        self.mapSaved = False
        self.mapLoaded = False
        self.createNewMap()
    
    def createNewMap(self):
        self.ncol = st.ncol
        self.nrow = st.nrow
        self.mapDataBottom = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]
        self.mapDataTop = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]

    def loadMap(self):
        # load map file
        mapchipDefFiles = []
        with open(st.mapFileName, "r") as fi:
            num_def_file = int(fi.readline())
            for i in range(num_def_file):
                def_f = fi.readline().strip()
                mapchipDefFiles.append(def_f)
            self.defaultPaletteIdx, self.defaultIdx = [int(tok) for tok in fi.readline().split(",")]
            self.ncol, self.nrow = [int(tok) for tok in fi.readline().split(",")]

            def readMapData(mapData):
                for row in range(self.nrow):
                    colDatas = [tuple(int(tok2) for tok2 in tok.split(":")) for tok in fi.readline().strip().split(",")]
                    for col, colData in enumerate(colDatas):
                        mapData[row][col] = colData

            # buttom
            line = fi.readline()
            if not line.startswith("Bottom"):
                print("Format Error")
            self.mapDataTop = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]
            readMapData(self.mapDataBottom)

            # top
            line = fi.readline()
            if not line.startswith("Top"):
                print("Format Error")
            self.mapDataBottom = [[(self.defaultPaletteIdx, self.defaultIdx) for col in range(self.ncol)] for row in range(self.nrow)]
            readMapData(self.mapDataTop)
            
         # load mapchip definition file 
        st.mapchipFiles = []
        self.palette.mapchipDatas = []
        for mapchipDefFile in mapchipDefFiles:
            with open(mapchipDefFile, "r") as fi:
                png_f = fi.readline().strip()
                data = MapchipData()
                st.mapchipFiles.append(png_f)
                self.palette.mapchipDatas.append(data)
                data.sheet = load_image(png_f)
                data.ncol, data.nrow = [int(tok) for tok in fi.readline().split(",")]
                for row in range(data.nrow):
                    for col in range(data.ncol):
                        idx, movable = [int(tok) for tok in fi.readline().split(",")]
                        data.mapchipData[idx] = movable
        self.palette.paletteIdx = 0
        self.palette.numPalette = len(mapchipDefFiles)

    def saveMap(self):
        # save mapchip definition file
        for i, mapchipFile in enumerate(st.mapchipFiles):
            mapchipDefFile = os.path.splitext(mapchipFile)[0] + ".mapchip"
            with open(mapchipDefFile, "w") as fo:
                fo.write("{}\n".format(mapchipFile))
                data = self.palette.mapchipDatas[i]
                fo.write('{}, {}\n'.format(data.ncol, data.nrow))
                idx = 0
                for row in range(data.nrow):
                    for col in range(data.ncol):
                        movable = data.mapchipData[idx]
                        fo.write("{}, {}\n".format(idx, movable))
                        idx += 1 
        # save map file
        with open(st.mapFileName, "w") as fo:
            fo.write("{}\n".format(len(st.mapchipFiles)))
            for mapchipFile in st.mapchipFiles:
                mapchipDefFile = os.path.splitext(mapchipFile)[0] + ".mapchip"
                fo.write("{}\n".format(mapchipDefFile))
            fo.write("{}, {}\n".format(self.defaultPaletteIdx, self.defaultIdx))
            fo.write("{}, {}\n".format(self.ncol, self.nrow))
            def writeMapData(mapData):
                for row in range(self.nrow):
                    colDatas = []
                    for col in range(self.ncol):
                        paletteIdx, idx = mapData[row][col]
                        colDatas.append([paletteIdx, idx])
                    colStr = ", ".join("{}:{}".format(paletteIdx, idx) for paletteIdx, idx in colDatas)
                    fo.write("{}\n".format(colStr))
            # buttom
            fo.write("Bottom\n")
            writeMapData(self.mapDataBottom)
            # top
            fo.write("Top\n")
            writeMapData(self.mapDataTop)


    def handle_keys(self):
        mouse_pressed = pygame.mouse.get_pressed()

        px, py = pygame.mouse.get_pos()
        sx = px // CS
        sy = py // CS
        screen_wx = self.cursor.wx - SCREEN_CENTER_X
        screen_wy = self.cursor.wy - SCREEN_CENTER_Y
        wx = screen_wx + sx
        wy = screen_wy + sy
        if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
            return 
        
        if mouse_pressed[0]:
            if self.layer == self.LAYER_BOTTOM:
                self.mapDataBottom[wy][wx] = self.palette.selected_mapchip
            else:
                self.mapDataTop[wy][wx] = self.palette.selected_mapchip
        elif mouse_pressed[2]:
            if self.layer == self.LAYER_BOTTOM:
                self.palette.selected_mapchip = self.mapDataBottom[wy][wx]
            else:
                self.palette.selected_mapchip = self.mapDataTop[wy][wx]

                  
    def update(self):
        self.handle_keys()

    def drawOutImage(self, sx, sy):
        pygame.draw.rect(self.screen, self.COLOR, (CS*sx, CS*sy, CS, CS), self.WIDTH)
        pygame.draw.line(self.screen, self.COLOR, (CS*sx, CS*sy), (CS*(sx+1), CS*(sy+1)), self.WIDTH)
    
    def drawImage(self, paletteIdx, idx, sx, sy):
        data = self.palette.mapchipDatas[paletteIdx]
        x, y = self.palette.to_xy(data, idx)
        self.screen.blit(data.sheet, (sx * CS, sy * CS), (x * CS, y * CS, CS, CS))

    def draw(self):
        screen_wx = self.cursor.wx - SCREEN_CENTER_X
        screen_wy = self.cursor.wy - SCREEN_CENTER_Y
        
        for sy in range(SCREEN_NROW):
            for sx in range(SCREEN_NCOL):
                wx = screen_wx + sx
                wy = screen_wy + sy
                if not (0 <= wx < self.ncol) or not (0 <= wy < self.nrow):
                    self.drawOutImage(sx, sy)
                else:
                    if self.layer == self.LAYER_BOTTOM:
                        paletteIdx, idx = self.mapDataBottom[wy][wx]
                        self.drawImage(paletteIdx, idx, sx, sy)
                    
                    elif self.layer == self.LAYER_TOP:
                        paletteIdx, idx = self.mapDataTop[wy][wx]
                        # self.drawImage(1, sx, sy)
                        self.drawImage(paletteIdx, idx, sx, sy)
                    else: # self.layer == self.LAYER_BOTH:
                        paletteIdx, idx = self.mapDataBottom[wy][wx]
                        self.drawImage(paletteIdx, idx, sx, sy)
                        paletteIdx, idx = self.mapDataTop[wy][wx]
                        self.drawImage(paletteIdx, idx, sx, sy)
                    # show grid
                    if self.showGrid:
                        pygame.draw.rect(self.screen, (0, 0, 0), (sx * CS, sy * CS, CS, CS), 1)



class MapchipData:
    def __init__(self):
        self.sheet = None
        self.ncol = 0
        self.nrow = 0
        self.mapchipData = {}
        self.startRow = 0

class MapchipPalette:
    OUT_COLOR = (255, 255, 255)
    OUT_WIDTH = 1
    CURSOR_COLOR = (0, 255, 0)
    CURSOR_WIDTH = 3
    def __init__(self, screen):
        self.screen = screen
        self.mapchipDatas = []
        self.paletteIdx = 0
        self.numPalette = len(st.mapchipFiles)
        for filename in st.mapchipFiles:
            self.mapchipDatas.append(self.readMapchipFile(filename))
        self.selected_mapchip = (0, 0) # paletteIdx, mapchipIdx
    
    def to_xy(self, data, idx):
        return (idx % data.ncol, idx // data.ncol)

    def to_idx(self, data, x, y):
        return y * data.ncol + x
    
    def changeMovable(self):
        paletteIdx, idx = self.selected_mapchip
        data = self.mapchipDatas[paletteIdx]
        movable = data.mapchipData[idx]
        data.mapchipData[idx] = 1 if not movable else 0

    def readMapchipFile(self, filename):
        data = MapchipData()
        data.sheet = load_image(filename)
        data.ncol = data.sheet.get_width() // CS
        data.nrow = data.sheet.get_height() // CS
        idx = 0
        for row in range(data.nrow):
            for col in range(data.ncol):
                data.mapchipData[idx] = 1 # movabeFlag
                idx += 1
        return data
    
    def handle_mouse(self, button):
        data = self.mapchipDatas[self.paletteIdx]
        if button == 4:
            if data.startRow > 0:
                data.startRow -= 1
        elif button == 5:
            if data.startRow - 1 < data.nrow:
                data.startRow += 1


    def handle_keys(self):
        data = self.mapchipDatas[self.paletteIdx]
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_UP]:
            if data.startRow > 0:
                data.startRow -= 1
        elif pressed_keys[pygame.K_DOWN]:
            if data.startRow - 1 < data.nrow:
                data.startRow += 1

        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            px, py = pygame.mouse.get_pos()
            sx = px // CS
            sy = py // CS
            if 0 <= sx < data.ncol and 0 <= sy < data.nrow:
                sy2 = data.startRow + sy
                try:
                    idx = self.to_idx(data, sx, sy2)
                    self.selected_mapchip = (self.paletteIdx, idx)
                    self.paletteIdx = 0
                    pygame.time.wait(500)
                    return True
                except:
                    pass
        return False

    def update(self):
        return self.handle_keys()

    def drawOutImage(self, sx, sy):
        pygame.draw.rect(self.screen, self.OUT_COLOR, (CS*sx, CS*sy, CS, CS), self.OUT_WIDTH)
        pygame.draw.line(self.screen, self.OUT_COLOR, (CS*sx, CS*sy), (CS*(sx+1), CS*(sy+1)), self.OUT_WIDTH)
    
    def drawImage(self, sheet, x, y, sx, sy):
        self.screen.blit(sheet, (sx * 32, sy * 32), (x * 32, y * 32, 32, 32))
    
    def draw(self):
        # draw out
        for sy in range(SCREEN_NROW):
            for sx in range(SCREEN_NCOL):
                self.drawOutImage(sx, sy)

        # draw mapchip
        data = self.mapchipDatas[self.paletteIdx]
        for sy in range(data.nrow):
            for sx in range(data.ncol):
                sy2 = data.startRow + sy
                try:
                    idx = self.to_idx(data, sx, sy2)
                    x, y = self.to_xy(data, idx)
                    self.drawImage(data.sheet, x, y, sx, sy)
                except:
                    pass
        
        # draw cursor
        px, py = pygame.mouse.get_pos()
        sx = px // CS
        sy = py // CS        
        pygame.draw.rect(self.screen, self.CURSOR_COLOR, (CS*sx, CS*sy, CS, CS), self.CURSOR_WIDTH)

def draw_selection(messageEngine, screen, palette, cursor, fieldMap, mapSaved, mapLoaded):
    # draw mapchip
    paletteIdx, idx = palette.selected_mapchip
    data = palette.mapchipDatas[paletteIdx]
    x, y = palette.to_xy(data, idx)
    screen.blit(data.sheet, (10, 10), (x * CS, y * CS, CS, CS))
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, CS, CS), 3)
    
    # draw movable
    paletteIdx, idx = palette.selected_mapchip
    data = palette.mapchipDatas[paletteIdx]
    movable = data.mapchipData[idx]
    movable_str = {True: "MOVABLE", False: "NOTMOVABLE"}[movable]
    messageEngine.draw_string(screen, (52, 10), movable_str)

    # draw mouse position
    px, py = pygame.mouse.get_pos()
    sx = px // CS
    sy = py // CS
    screen_wx = cursor.wx - SCREEN_CENTER_X
    screen_wy = cursor.wy - SCREEN_CENTER_Y
    wx = screen_wx + sx
    wy = screen_wy + sy
    messageEngine.draw_string(screen, (10, 56), "{}　{}". format(wx, wy))
    
    # draw layer
    layer_str = {fieldMap.LAYER_BOTTOM: "BOTTOM",
                    fieldMap.LAYER_TOP: "TOP",
                    fieldMap.LAYER_BOTH: "BOTH"}[fieldMap.layer]
    messageEngine.draw_string(screen, (10, 56+32), layer_str)
    
    # draw map saved
    if mapSaved:
        color = messageEngine.color
        messageEngine.set_color(MessageEngine.GREEN)
        messageEngine.draw_string(screen, (10, 56+32*2), "MAP SAVED")
        messageEngine.set_color(color)
    
    # draw map loaded
    if mapLoaded:
        color = messageEngine.color
        messageEngine.set_color(MessageEngine.GREEN)
        messageEngine.draw_string(screen, (10, 56+32*2), "MAP LOADED")
        messageEngine.set_color(color)
    
STATE_MAP = 0
STATE_PALETTE = 1

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_RECT.size)
    pygame.display.set_caption('Map Editor')
    palette = MapchipPalette(screen)
    cursor = Cursor()
    fieldMap = Map(screen, cursor, palette)
    cursor.set_map(fieldMap)
    messageEngine = MessageEngine()
    clock = pygame.time.Clock()
    state = STATE_MAP

    while True:
        clock.tick(60)
        screen.fill((0, 0, 0)) # background buffer clear
        if state == STATE_MAP:
            cursor.update()
            fieldMap.update()
            fieldMap.draw()
            draw_selection(messageEngine, screen, palette, cursor, fieldMap, fieldMap.mapSaved, fieldMap.mapLoaded)
            if fieldMap.mapSaved:
                fieldMap.save_cnt += 1
                if fieldMap.save_cnt > SAVE_WAIT_COUNT:
                    fieldMap.save_cnt = 0
                    fieldMap.mapSaved = False
            if fieldMap.mapLoaded:
                fieldMap.load_cnt += 1
                if fieldMap.load_cnt > SAVE_WAIT_COUNT:
                    fieldMap.load_cnt = 0
                    fieldMap.mapLoaded = False
        elif state == STATE_PALETTE:
            if palette.update():
                state = STATE_MAP
                pygame.event.clear()
                continue
            palette.draw()
            if fieldMap.mapSaved:
                fieldMap.save_cnt = 0
                fieldMap.mapSaved = False
            elif fieldMap.mapLoaded:
                fieldMap.load_cnt = 0
                fieldMap.mapLoaded = False

        pygame.display.update() # front buffer

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()           
                elif event.key == pygame.K_SPACE:
                    if state == STATE_MAP:
                        state = STATE_PALETTE
                    elif state == STATE_PALETTE:
                        palette.paletteIdx = (palette.paletteIdx + 1) % palette.numPalette
                        if palette.paletteIdx == 0:
                            state = STATE_MAP
                elif event.key == pygame.K_g:
                    fieldMap.showGrid = not fieldMap.showGrid
                elif event.key == pygame.K_m:
                    palette.changeMovable()
                elif event.key == pygame.K_1:
                    fieldMap.layer = fieldMap.LAYER_BOTTOM
                elif event.key == pygame.K_2:
                    fieldMap.layer = fieldMap.LAYER_TOP
                elif event.key == pygame.K_3:
                    fieldMap.layer = fieldMap.LAYER_BOTH
                elif event.key == pygame.K_s:
                    fieldMap.saveMap()
                    fieldMap.save_cnt = 0
                    fieldMap.mapSaved = True
                elif event.key == pygame.K_l:
                    fieldMap.loadMap()
                    fieldMap.load_cnt = 0
                    fieldMap.mapLoaded = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in [4, 5]:# wheel up or down
                    palette.handle_mouse(event.button)
if __name__ == '__main__':
    main()