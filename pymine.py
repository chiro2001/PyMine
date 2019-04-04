from tkinter import *
import tkinter.font as tkFont
import random
import numpy as np
import queue
import copy

from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
FR_PRIVATE = 0x10
FR_NOT_ENUM = 0x20


# https://stackoverflow.com/questions/11993290/truly-custom-font-in-tkinter
def load_font(fontpath, private=True, enumerable=False):
    if isinstance(fontpath, str):
        pathbuf = create_string_buffer(fontpath)
        AddFontResourceEx = windll.gdi32.AddFontResourceExA
    # elif isinstance(fontpath, unicode):
    elif isinstance(fontpath, bytes):
        pathbuf = create_unicode_buffer(fontpath)
        AddFontResourceEx = windll.gdi32.AddFontResourceExW
    else:
        # raise TypeError('fontpath must be of type str or unicode')
        raise TypeError('fontpath must be of type str')

    flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
    numFontsAdded = AddFontResourceEx(byref(pathbuf), flags, 0)
    return bool(numFontsAdded)


class Mine:
    def __init__(self, w, h, n):
        self.w, self.h = w, h
        # 地雷数
        self.n = n
        # 这次用[x][y]格式
        # code:
        # -1 - 地雷
        # 数字 - 周围数字
        # 0 - 安全
        self.map = [[0 for i in range(w)] for j in range(h)]
        self.dis = [[False for i in range(w)] for j in range(h)]
        self.init_mine()
        self.update_weights()

    def init_mine(self):
        # 这种数组生成方式好像还不错
        self.map = [[0 for i in range(self.w)] for j in range(self.h)]
        sample = [(i, j) for j in range(self.w) for i in range(self.h)]
        mlist = random.sample(sample, self.n)
        for li in mlist:
            self.map[li[0]][li[1]] = -1

    def update_weights(self):
        # 用np.array才能进行二维数组切片操作
        a = np.array(self.map)
        for x in range(self.w):
            for y in range(self.h):
                if a[x][y] == -1:
                    continue
                low_x = max(0, x - 1)
                low_y = max(0, y - 1)
                s = a[low_x:x + 2, low_y:y + 2]
                self.map[x][y] = list(s.reshape(s.size)).count(-1)

    # 返回值： True - 挖到地雷； False - 安全
    def dig(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return False
        if self.map[x][y] == -1:
            return True
        self.digging(x, y)
        return False

    # 更新挖掘状态，使用宽度优先搜索
    def digging(self, x, y):
        # 不挖挖过的块，不挖地雷
        if self.dis[x][y] is True:
            return
        # 总之先挖起来
        self.dis[x][y] = True
        if self.map[x][y] == -1:
            return
        searched = []
        q = queue.Queue()
        q.put((x, y))
        searched.append((x, y))
        directions = ((0, 1, 0, -1), (-1, 0, 1, 0))
        while not q.empty():
            ix, iy = q.get()
            for k in range(4):
                dx = ix + directions[0][k]
                dy = iy + directions[1][k]
                if 0 <= dx < self.w and 0 <= dy < self.h and self.dis[dx][dy] is False:
                    if self.map[dx][dy] == 0:
                        q.put(copy.deepcopy((dx, dy)))
                        searched.append(copy.deepcopy((dx, dy)))
                        self.dis[dx][dy] = True

        # 最后扩展一次，显现数字
        a = np.array(self.map)
        for search in searched:
            ix, iy = search
            low = (max(0, ix - 1), max(0, iy - 1))
            s = a[low[0]:ix + 2, low[1]:iy + 2]
            for ii in range(s.shape[0]):
                for ij in range(s.shape[1]):
                    if self.map[ii + ix][ij + iy] != -1:
                        self.dis[ii + ix][ij + iy] = True


class MineUi:
    def __init__(self, w=10, h=10, n=10):
        self.h, self.w, self.n = w, h, n
        self.mine = Mine(w, h, n)

        self.root = Tk()
        self.root.resizable(width=False, height=False)
        # self.root.attributes("-toolwindow", 1)
        self.root.title("PyMine - 扫雷")

        # 检查字体环境
        # if '5x5 Dots' not in tkFont.families():
        if '42' not in tkFont.families():
            # res = load_font('5x5dots.ttf')
            res = load_font('42.ttf')
            if not res:
                print("字体安装失败")
                exit(1)
            print("字体安装成功")

        self.var_time = StringVar()
        self.var_num = StringVar()
        self.var_face = StringVar()
        self.var_num.set("%03d" % self.n)
        self.var_time.set("000")
        self.var_face.set("J")

        # 笑脸J， 哭脸L
        self.font_face = tkFont.Font(family='Wingdings', size=12, weight=tkFont.NORMAL)
        # self.font_num = tkFont.Font(family='5x5 Dots', size=24, weight=tkFont.NORMAL)
        self.font_num = tkFont.Font(family='42', size=24, weight=tkFont.NORMAL)

        Label(self.root, textvariable=self.var_time, font=self.font_num).grid(row=0, column=0)
        Button(self.root, textvariable=self.var_face, font=self.font_face).grid(row=0, column=1)
        Label(self.root, textvariable=self.var_num, font=self.font_num).grid(row=0, column=2)

        print(tkFont.families())


if __name__ == '__main__':
    ui = MineUi(w=10, h=10, n=10)
    ui.root.mainloop()

