import pygame
import sys
import os
import random
import math
# GIFを分解するために標準ライブラリを使用
import tkinter as tk

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


# --- 変更: 背景の透過処理（透明判定＋白色除外）を強化した関数 ---
def load_gif_frames(filepath, target_size):
    """
    pipを使わず、標準のtkinterを使ってGIFから全フレームを抽出し、
    背景を完全に透過させたPygameのSurfaceのリストに変換する関数
    """
    frames = []
    # tkinterの非表示ウィンドウを作成（GIF解析用）
    root = tk.Tk()
    root.withdraw()
    
    frame_idx = 0
    while True:
        try:
            photo = tk.PhotoImage(file=filepath, format=f"gif -index {frame_idx}")# tkinterでGIFの特定のフレームを読み込む
            width, height = photo.width(), photo.height()# 空のPygame Surfaceを作成 (アルファチャンネルありの透明な土台)
            surf = pygame.Surface((width, height), pygame.SRCALPHA)# 各ピクセルの色データをPygame Surfaceにコピー
            for y in range(height):
                for x in range(width):
                    try:
                        if photo.transparency_get(x, y):#tkinterの機能でこのピクセルが透明かチェック
                            continue # 透明ならPygame側に何も書き込まずスキップ
                        color_str = photo.get(x, y)
                        if color_str:# 戻り値が数値のリスト(R, G, B)で返る場合と文字列の場合をケア
                            if isinstance(color_str, (list, tuple)):
                                r, g, b = color_str[0], color_str[1], color_str[2]
                            else:# tkinterの返す文字列からrgbのタプルを取得
                                r, g, b = photo.tk.call("winfo", "rgb", root, color_str)# 16bit(0-65535)を8bit(0-255)に変換
                                r, g, b = r >> 8, g >> 8, b >> 8
                            if r == 255 and g == 255 and b == 255:# 透明部分が「真っ白(255, 255, 255)」として取得されてしまった場合のセーフティ
                                continue # 白い背景部分なら書き込まずスキップ
                            surf.set_at((x, y), (r, g, b, 255))# 色のついている部分だけを不透明で書き込む
                    except Exception:# エラーが起きたピクセルも透明扱いにしてスキップ
                        continue
            surf = pygame.transform.scale(surf, target_size)# 指定されたマス目のサイズにリサイズ
            frames.append(surf)
            frame_idx += 1
        except tk.TclError:
            break
            
    root.destroy()
    return frames
class Effect:
    """
    エフェクトGIFを再生するためのクラス
    引数：x (int): エフェクトのX座標
          y (int): エフェクトのY座標
          frames (list): アニメーションのフレーム（Surfaceのリスト）
          frame_delay (int): 1コマを何フレーム表示するか（速度調整用）
    戻り値：なし
    """
    def __init__(self, x, y, frames, frame_delay=3):
        self.x = x
        self.y = y
        self.frames = frames      # アニメーションのコマ（Surfaceのリスト）
        self.current_frame = 0    # 現在のコマ番号
        self.frame_delay = frame_delay  # 1コマを何フレーム表示するか（速度調整用）
        self.timer = 0

    def update(self):
        """アニメーションのコマを進める。全フレーム再生が終わったらFalseを返す"""
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.timer = 0
            self.current_frame += 1
        return self.current_frame < len(self.frames)# 現在のコマが最大フレーム数を超えたらエフェクト終了

    def draw(self, surface):
        """現在のコマの画像を石の中心に合わせて描画"""
        if self.current_frame < len(self.frames):
            img = self.frames[self.current_frame]
            center_x = self.x * GRID_SIZE + GRID_SIZE // 2
            center_y = self.y * GRID_SIZE + GRID_SIZE // 2
            rect = img.get_rect(center=(center_x, center_y))
            surface.blit(img, rect)


class Othello:
    def __init__(self):
        self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        mid = BOARD_SIZE // 2
        self.board[mid - 1][mid - 1] = WHITE
        self.board[mid - 1][mid] = BLACK
        self.board[mid][mid - 1] = BLACK
        self.board[mid][mid] = WHITE
        self.turn = BLACK

        # --- 追加: アニメーションエフェクトの初期化 ---
        self.effects = []
        gif_path = "fig/reverse.gif"
        self.effect_frames = load_gif_frames(gif_path, (GRID_SIZE, GRID_SIZE)) #アニメーションのフレームをロード
    def draw_board(self):
        screen.fill(GREEN)
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, BLACK, rect, 1)
                if self.board[x][y] is not None:
                    self.draw_stone(x, y, self.board[x][y])
                    
        # --- アニメーションエフェクトの描画と更新 ---
        active_effects = []
        for effect in self.effects:
            effect.draw(screen)
            if effect.update():  # アニメーションが継続中のものだけ残す
                active_effects.append(effect)
        self.effects = active_effects

    def draw_stone(self, x, y, color):
        pygame.draw.circle(screen, color, (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2 - 4)

    def is_valid_move(self, x, y):
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
                    # --- アニメーションエフェクトを生成 ---
                    if self.effect_frames:
                        self.effects.append(Effect(px, py, self.effect_frames, frame_delay=3))

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

def main():
    game = Othello()
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                x //= GRID_SIZE
                y //= GRID_SIZE
                game.next_move(x, y)
        game.draw_board()
        pygame.display.flip()
        clock.tick(60) # 60FPSで動作
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()