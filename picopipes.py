from picoboy import PicoBoy
from random import randint, randrange
from array import array
import time

pb = PicoBoy()

CENTER = 0
UP = 1<<0
RIGHT = 1<<1
DOWN = 1<<2
LEFT = 1<<3
UP_ON = 1<<4
RIGHT_ON = 1<<5
DOWN_ON = 1<<6
LEFT_ON = 1<<7

delta_for_dir = { UP : (0,-1), RIGHT : (+1,0), DOWN : (0,+1), LEFT : (-1,0)}
opposite = { UP : DOWN, DOWN : UP, LEFT : RIGHT, RIGHT : LEFT}

MAX_WIDTH = 10
MAX_HEIGHT = 5
SCREEN = (128,64)
TILE_SIZE = 12
CONNECTOR_WIDTH=2


board_size=(4,4)

NUM_STARS = 20
stars = [(float(randrange(0,SCREEN[0])),float(randrange(0,SCREEN[1]))) for _ in range(NUM_STARS)]

start_tick = 0

def up(val):
   return (val & UP == UP, val & UP_ON == UP_ON)

def right(val):
   return (val & RIGHT == RIGHT, val & RIGHT_ON == RIGHT_ON)

def down(val):
   return (val & DOWN == DOWN, val & DOWN_ON == DOWN_ON)

def left(val):
   return (val & LEFT == LEFT, val & LEFT_ON == LEFT_ON)


def rotate(state):

    return (state & UP) << 1 | (state & UP_ON) << 1 \
         | (state & RIGHT) << 1 | (state & RIGHT_ON) << 1 \
         | (state & DOWN) << 1 | (state & DOWN_ON) << 1 \
         | (state & LEFT) >> 3 | (state & LEFT_ON) >> 3

def get_adjacent(cell, direction, board_size):

    delta = delta_for_dir[direction]

    x, y = (cell[0]+delta[0], cell[1]+delta[1])

    if x < 0 or x >= board_size[0] or y < 0 or y >= board_size[1]:
        return None
    else:
        return (x,y)

def bfs(board, start, board_size, callback, visited, edge_callback = None):

    queue = [start]

    while len(queue) > 0:

        x,y = queue.pop()
        state = board[x][y]

        callback(x,y)

        dirs = [d for d in [UP, RIGHT, DOWN, LEFT] if d & state == d]

        for d in dirs:
            neighbor = get_adjacent((x,y), d, board_size)

            if neighbor != None:

                nx, ny = neighbor

                if board[nx][ny] & opposite[d] == 0:
                    continue

                if edge_callback != None:
                    edge_callback(x,y,d)

                if not visited(neighbor[0], neighbor[1]):
                    queue.append(neighbor)
    


def generate_board(board_size):

    width, height = board_size

    union_map = [[ y + x * height for y in range(height)] for x in range(width)]
    board = [[ 0 for _ in range(height)] for _ in range(width)]

    start = (randint(1, width-2), randint(1, height-2))

    edge_count = 0

    while edge_count < width*height-1:
        x, y = randint(0, width-1), randint(0, height-1)

        state = board[x][y]

        available_dirs = [ d for d in [UP, RIGHT, DOWN, LEFT] if d & state == 0]

        if len(available_dirs) <= 0:
            continue

        while len(available_dirs) > 0:
            index = randrange(0,len(available_dirs))
            direction = available_dirs[index]
            del available_dirs[index]

            neighbor = get_adjacent((x,y), direction, board_size)

            if neighbor == None:
                continue

            nx, ny = neighbor

            if union_map[x][y] == union_map[nx][ny]:
                continue

            def callback(cx, cy):
                union_map[cx][cy] = union_map[x][y]

            visited = lambda nx, ny: (union_map[nx][ny] == union_map[x][y])
            bfs(board, (nx,ny),  board_size, callback, visited)

            board[x][y] |= direction
            board[nx][ny] |= opposite[direction]

            edge_count += 1

    for x in range(width):
        for y in range(height):
            for _ in range(randint(0,4)):
                board[x][y] = rotate(board[x][y])


    return board, start

def draw_stars(picoboy = None):
    global stars

    if picoboy == None:
        picoboy = pb

    for index in range(len(stars)):
        x, y = stars[index]
        picoboy.pixel(int(x),int(y),1)

        stars[index] = ((x+(index%2)/2+0.5) % SCREEN[0], y)

def draw_board(board, board_size, selected, start, blink = False, show_size = False):
    pb.fill(0)

    draw_stars()

    shift=((SCREEN[0]-(board_size[0]*TILE_SIZE))//2, (SCREEN[1]-(board_size[1]*TILE_SIZE))//2)

    ticks_diff = time.ticks_diff(time.ticks_us(), start_tick)

    skip = False
    if blink and (ticks_diff // 400000) % 2 == 0:
        skip = True

    for x in range(board_size[0]):
        if skip:
            break
        sx = shift[0] + x * TILE_SIZE
        for y in range(board_size[1]):

            sy = shift[1] + y * TILE_SIZE
    
            if (x,y) == selected:
                pb.rect(shift[0]+x*TILE_SIZE, shift[1]+y*TILE_SIZE, TILE_SIZE+1, TILE_SIZE+1, 1)

            center = (sx+TILE_SIZE//2, sy+TILE_SIZE//2)

            on = False

            up_present, up_on = up(board[x][y])

            if up_present:

                pb.line(center[0], center[1], center[0], sy, 1)
                if up_on:
                    on = True
                    pb.line(center[0]-CONNECTOR_WIDTH//2, center[1], center[0]-CONNECTOR_WIDTH//2, sy, 1)
                    pb.line(center[0]+CONNECTOR_WIDTH//2, center[1], center[0]+CONNECTOR_WIDTH//2, sy, 1)

            down_present, down_on = down(board[x][y])
            if down_present:
                pb.line(center[0], center[1], center[0], sy+TILE_SIZE, 1)
                
                if down_on:
                    on = True
                    pb.line(center[0]-CONNECTOR_WIDTH//2, center[1], center[0]-CONNECTOR_WIDTH//2, sy+TILE_SIZE, 1)
                    pb.line(center[0]+CONNECTOR_WIDTH//2, center[1], center[0]+CONNECTOR_WIDTH//2, sy+TILE_SIZE, 1)

            left_present, left_on = left(board[x][y])
            if left_present:
                pb.line(sx, center[1], center[0], center[1], 1)
                if left_on:
                    on = True
                    pb.line(sx, center[1]-CONNECTOR_WIDTH//2, center[0], center[1]-CONNECTOR_WIDTH//2, 1)
                    pb.line(sx, center[1]+CONNECTOR_WIDTH//2, center[0], center[1]+CONNECTOR_WIDTH//2, 1)

            right_present, right_on = right(board[x][y])
            if right_present:

                pb.line(center[0], center[1], sx+TILE_SIZE, center[1], 1)

                
                if right_on:
                    on = True
                    pb.line(center[0], center[1]-CONNECTOR_WIDTH//2, sx+TILE_SIZE, center[1]-CONNECTOR_WIDTH//2, 1)
                    pb.line(center[0], center[1]+CONNECTOR_WIDTH//2, sx+TILE_SIZE, center[1]+CONNECTOR_WIDTH//2, 1)

            if (x,y) == start:
                pb.fill_rect(center[0]-CONNECTOR_WIDTH-1, center[1]-CONNECTOR_WIDTH-1, CONNECTOR_WIDTH+4, CONNECTOR_WIDTH+4, 0)
                pb.rect(center[0]-CONNECTOR_WIDTH-1, center[1]-CONNECTOR_WIDTH-1, CONNECTOR_WIDTH+4, CONNECTOR_WIDTH+4, 1)
            else:
                pb.fill_rect(center[0]-CONNECTOR_WIDTH+1, center[1]-CONNECTOR_WIDTH+1, CONNECTOR_WIDTH+1, CONNECTOR_WIDTH+1, 0)
                pb.rect(center[0]-CONNECTOR_WIDTH+1, center[1]-CONNECTOR_WIDTH+1, CONNECTOR_WIDTH+1, CONNECTOR_WIDTH+1, 1)

            
    if show_size:
        size_string = f"{board_size[0]}x{board_size[1]}"
        text_width = 8 * len(size_string)
        text_height = 8
        x = int(SCREEN[0]/2-text_width/2)
        y = int(SCREEN[1]/2-text_height/2)
        pb.fill_rect(x-4, y-4, text_width+8, text_height+8, 0)
        pb.rect(x-4, y-4, text_width+8, text_height+8, 1)

        pb.text(size_string, x, y, 1)

    pb.show()


def update_on(board, board_size, start):

    width, height = board_size
    active_cell_count = 0

    for x in range(width):
        for y in range(height):
            board[x][y] &= int('00001111',2)

    
    def edge_callback(x,y,d):
        board[x][y] |= (d<<4)

    def callback(x,y):
        nonlocal active_cell_count
        active_cell_count += 1

    bfs(board, start, board_size, callback, lambda x,y: board[x][y] & int('11110000',2) != 0, edge_callback)

    return active_cell_count



def handle_input(board, board_size, selected):

    dx, dy = 0, 0

    button = None

    if pb.pressedDown():
        button = pb.pressedDown
        dy = +1

    if pb.pressedUp():
        button = pb.pressedUp
        dy = -1

    if pb.pressedLeft():
        button = pb.pressedLeft
        dx = -1

    if pb.pressedRight():
        button = pb.pressedRight
        dx = +1

    if pb.pressedCenter():
        button = pb.pressedCenter
        x, y = selected
        board[x][y] = rotate(board[x][y])

    return (((selected[0] + dx + board_size[0]) % board_size[0], (selected[1] + dy + board_size[1]) % board_size[1]), button)

def win():

    inv = 0
    for _ in range(10):
        pb.LED_RED.toggle()
        pb.delay(100)
        pb.LED_YELLOW.toggle()
        pb.delay(100)
        pb.LED_GREEN.toggle()
        pb.delay(100)

        inv = 1-inv
        pb.invert(inv)
        pb.show()
    

    pb.invert(0)
    pb.LED_RED.off()
    pb.LED_GREEN.off()
    pb.LED_YELLOW.off()

def get_button(update_callback):
    button_fn = None
    button = None
    if pb.pressedRight():
        button_fn = pb.pressedRight
        button = RIGHT
    if pb.pressedLeft():
        button_fn = pb.pressedLeft
        button = LEFT
    if pb.pressedUp():
        button_fn = pb.pressedUp
        button = UP
    if pb.pressedDown():
        button_fn = pb.pressedDown
        button = DOWN

    if pb.pressedCenter():
        button = pb.pressedCenter
        button = CENTER

    while button_fn != None and button_fn():
        update_callback()
    else:
        return button

    
def setup(board_size):

    confirmed = False

    board, start = generate_board(board_size)

    while not confirmed:

        generate = False
        button = get_button(
            lambda : draw_board(board, board_size, None, start, True, True))

        if button == RIGHT:
            board_size = (min(MAX_WIDTH,board_size[0]+1), board_size[1])
        if button == LEFT:
            board_size = (max(3,board_size[0]-1), board_size[1])
        if button == UP:
            board_size = (board_size[0], min(MAX_HEIGHT, board_size[1]+1))
        if button == DOWN:
            board_size = (board_size[0], max(3,board_size[1]-1))

        if button == CENTER:
            confirmed = True

        if button != None and button != CENTER:
            board, start = generate_board(board_size)

        draw_board(board, board_size, None, start, True, True)

        yield 

    yield board, start, board_size

def game_loop(board, board_size, start):

    connected_cells = 0

    selected = start

    while connected_cells != board_size[0] * board_size[1]:

        draw_board(board, board_size, selected, start)

        selected, button = handle_input(board, board_size, selected)

        while button != None and button():
            draw_board(board, board_size, None, start)
        else:
            connected_cells = update_on(board, board_size, start)

        yield

    else:
        update_on(board, board_size, start)
        draw_board(board, board_size, selected, start)
        win()

def main():
    start_tick = time.ticks_us()
    pb.invert(0)
    selected = (0,0)
    board_size = (4,4)
    board = None
    start = None

    while True:
        for setup_results in setup(board_size):
            if setup_results != None:
                board, start, board_size = setup_results

            yield

        for _ in game_loop(board, board_size, start):
            yield


if __name__ == "__main__":
    for _ in main():
        pass