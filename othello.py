import pygame
import sys
import os
import random
import math

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 定数の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
YELLOW = (255, 155, 0)
SIZE = 600
BOARD_SIZE = 8
GRID_SIZE = SIZE // BOARD_SIZE

# Pygameの初期化
pygame.init()
screen = pygame.display.set_mode((SIZE, SIZE))
pygame.display.set_caption("オセロゲーム")

class Othello:
    def __init__(self):
        self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        mid = BOARD_SIZE // 2
        self.board[mid - 1][mid - 1] = WHITE
        self.board[mid - 1][mid] = BLACK
        self.board[mid][mid - 1] = BLACK
        self.board[mid][mid] = WHITE
        self.turn = BLACK
        # スキル関連
        self.skill = None
        self.locked = {}
        self.sp = {
            BLACK: 100,
            WHITE: 100
        }
        self.used_skill = False
        
    def draw_board(self):
        screen.fill(GREEN)
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                # 封印マス
                if (x, y) in self.locked:
                    pygame.draw.rect(screen, (180, 0, 0), rect)
                pygame.draw.rect(screen, BLACK, rect, 1)
                if self.board[x][y] is not None:
                    self.draw_stone(x, y, self.board[x][y])
                    # ×マーク表示
                    if (x, y) in self.locked:
                        font = pygame.font.Font(None, 40)
                        text = font.render("X", True, WHITE)
                        screen.blit(text, text.get_rect(center=rect.center))
        font = pygame.font.Font(None, 30)
        turn = "BLACK" if self.turn == BLACK else "WHITE"
        text = font.render(
                f"Turn:{turn}  SP:{self.sp[self.turn]}   L:Lock C:Corner B:Bomb",
                True,
                WHITE
            )
        if self.skill == "lock":
            text = font.render("LOCK MODE : Click a square", True, (255, 0, 0))
        if self.skill == "corner":
            text = font.render("CORNER MODE : Click a corner", True, (0,255,255))
        if self.skill == "corner":
            for x, y in [(0,0),(0,7),(7,0),(7,7)]:

                rect = pygame.Rect(
                    x*GRID_SIZE,
                    y*GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )

                pygame.draw.rect(
                    screen,
                    (0,255,255),
                    rect,
                    4
                )
        if self.skill == "bomb":
            text = font.render("BOMB MODE : click a square", True, (255, 0, 255))
        screen.blit(text,(10,10))

    def draw_stone(self, x, y, color):
        pygame.draw.circle(screen, color, (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2 - 4)

    def is_valid_move(self, x, y):
        if (x, y) in self.locked:
            return False
        if self.board[x][y] is not None:
            return False
        opponent = WHITE if self.turn == BLACK else BLACK
        valid = False
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == opponent:
                while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    nx += dx
                    ny += dy
                    if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                        break
                    if self.board[nx][ny] is None:
                        break
                    if self.board[nx][ny] == self.turn:
                        valid = True
                        break
        return valid

    def is_board_full(self):
        for row in self.board:
            if None in row:
                return False
        return True
    
    def flip_stones(self, x, y):
        opponent = WHITE if self.turn == BLACK else BLACK
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            pieces_to_flip = []
            nx, ny = x + dx, y + dy
            while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == opponent:
                pieces_to_flip.append((nx, ny))
                nx += dx
                ny += dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == self.turn:
                for px, py in pieces_to_flip:
                    self.board[px][py] = self.turn

    def has_valid_move(self):
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.is_valid_move(x, y):
                    return True
        return False

    def game_end(self):
        black_count = sum(row.count(BLACK) for row in self.board)
        white_count = sum(row.count(WHITE) for row in self.board)
        if black_count > white_count:
            return "Winner black"
        elif white_count > black_count:
            return "Winner white"
        else:
            return "Draw"

    def next_move(self, x, y):
        if self.is_board_full():
            result = self.game_end()
            self.display_result(result)
        elif self.is_valid_move(x, y):
            self.board[x][y] = self.turn
            self.flip_stones(x, y)
            self.turn = WHITE if self.turn == BLACK else BLACK
            self.used_skill = False
            self.update_locked()
            if not self.has_valid_move() or self.is_board_full():
                self.turn = WHITE if self.turn == BLACK else BLACK
                if not self.has_valid_move():
                    result = self.game_end()
                    self.display_result(result)

    def display_result(self, result):
        font = pygame.font.Font(None, 74)
        text = font.render(result, True, YELLOW)
        text_rect = text.get_rect(center=(SIZE // 2, SIZE // 2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(10000)
        pygame.quit()
        sys.exit()
        
    def update_locked(self):
        """
        封印スキルのターン数管理
        """
        remove = []

        for pos in self.locked:
            self.locked[pos] -= 1
            if self.locked[pos] <= 0:
                    remove.append(pos)

        for pos in remove:
            del self.locked[pos]
            
    def use_lock(self, x, y):
        """
        封印スキル
        Lキーで発動
        """
        if self.used_skill:
            return
        
        if self.sp[self.turn] < 3:
            return

        if self.board[x][y] is not None:
            return

        if (x, y) in self.locked:
            return

        self.locked[(x, y)] = 2
        self.sp[self.turn] -= 3
        self.used_skill = True
        self.skill = None

    def use_corner(self, x, y):
        """
        強制角取りスキル
        """
        if self.used_skill:
            return

        if self.sp[self.turn] < 8:
            return

        corners = [(0,0),(0,7),(7,0),(7,7)]

        if (x, y) not in corners:
            return

        if self.board[x][y] is not None:
            return

        if (x, y) in self.locked:
            return

        self.board[x][y] = self.turn
        self.sp[self.turn] -= 8
        self.used_skill = True
        self.skill = None

    def use_bomb(self, x, y):
        """
        爆弾スキル
        """
        if self.used_skill:
            return

        if self.sp[self.turn] < 5:
            return

        if not self.is_valid_move(x, y):
            return

        self.board[x][y] = self.turn
        self.flip_stones(x, y)
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:

                nx = x + dx
                ny = y + dy

                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if self.board[nx][ny] is not None:
                        self.board[nx][ny] = self.turn

        self.sp[self.turn] -= 5
        self.used_skill = True
        self.skill = None
        self.turn = WHITE if self.turn == BLACK else BLACK
        self.used_skill = False
        self.update_locked()

def main():
    game = Othello()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                x //= GRID_SIZE
                y //= GRID_SIZE
                if game.skill == "lock":
                    game.use_lock(x, y)
                elif game.skill == "corner":
                    game.use_corner(x, y)
                elif game.skill == "bomb":
                    game.use_bomb(x, y)
                else:
                    game.next_move(x, y)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l:
                    if game.skill == "lock":
                        game.skill = None
                    else:
                        game.skill = "lock"
                if event.key == pygame.K_c:
                    if game.skill == "corner":
                        game.skill = None
                    else:
                        game.skill = "corner"
                if event.key == pygame.K_b:
                    if game.skill == "bomb":
                        game.skill = None
                    else:
                        game.skill = "bomb"
        game.draw_board()
        pygame.display.flip()
    pygame.quit()
    sys.exit()
    

if __name__ == "__main__":
    main()