from tkinter import *
import tkinter.font as tkFont
import random
import numpy as np
import queue
import copy
import time
import threading
import sys
import os

#生成资源文件目录访问路径
def resource_path(relative_path):
    if getattr(sys, 'frozen', False): #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
FR_PRIVATE = 0x10
FR_NOT_ENUM = 0x20


# https://stackoverflow.com/questions/11993290/truly-custom-font-in-tkinter
def load_font(fontpath, private=True, enumerable=False):
    if isinstance(fontpath, bytes):
        pathbuf = create_string_buffer(fontpath)
        AddFontResourceEx = windll.gdi32.AddFontResourceExA
    # elif isinstance(fontpath, unicode):
    elif isinstance(fontpath, str):
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
        # 挖到数字，只挖这个数字
        if self.map[x][y] != 0:
            self.dis[x][y] = True
            return False
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
            low = max(0, ix - 1), max(0, iy - 1)
            s = a[low[0]:ix + 2, low[1]:iy + 2]
            for ii in range(s.shape[0]):
                for ij in range(s.shape[1]):
                    tx, ty = ii + ix - 1, ij + iy - 1
                    if 0 <= tx and tx < self.w and 0 <= ty and ty < self.h \
                            and self.map[tx][ty] != -1 and self.map[tx][ty] != 0:
                        self.dis[tx][ty] = True

    def win(self):
        for x in range(self.w):
            for y in range(self.h):
                if self.map[x][y] != -1 and self.dis[x][y] is False:
                    return False
        return True


class MineUi:
    def __init__(self, root, w=10, h=10, n=10):
        self.h, self.w, self.n = w, h, n
        self.mine = Mine(w, h, n)

        self.root = root
        self.root.resizable(width=False, height=False)
        # self.root.attributes("-toolwindow", 1)
        self.root.attributes('-alpha', 0.9)
        self.root.title("PyMine - 扫雷")

        # 检查字体环境
        if '5x5 Dots' not in tkFont.families():
            res = load_font(resource_path('5x5dots.ttf'))
            if not res:
                print("字体安装失败")
                exit(1)

        # 配置可变变量和常量
        self.var_time = StringVar()
        self.var_num = StringVar()
        self.var_face = StringVar()
        self.var_num.set("%03d" % self.n)
        self.var_time.set("000")
        self.var_face.set("K")
        self.win = None
        self.stated = False
        self.time = 0
        self.thread = None

        self.CODE_MINE = '۞'
        self.CODE_BLANK = ''
        self.CODE_CHECKED = ''
        self.CODE = {
            -2: self.CODE_BLANK,
            -1: self.CODE_MINE,
            0: self.CODE_CHECKED,
        }
        for i in range(1, 10):
            self.CODE[i] = "%d" % i

        self.COLORS = {
            -2: 'snow',
            -1: 'Black',
            0: 'LightGrey',
            1: 'Peru',
            2: 'DarkGoldenrod',
            3: 'OrangeRed',
            4: 'RosyBrown',
            5: 'LightSeaGreen',
            6: 'Aqua',
            7: 'SpringGreen',
            8: 'Lime',
        }

        self.signs = [[False for i in range(self.w)] for j in range(self.h)]

        # 笑脸J， 哭脸L，面瘫脸K
        self.font_face = tkFont.Font(family='Wingdings', size=15, weight=tkFont.NORMAL)
        self.font_num = tkFont.Font(family='5x5 Dots', size=24, weight=tkFont.NORMAL)
        self.font_unit = tkFont.Font(family='Consolas', size=9, weight=tkFont.NORMAL)

        Label(self.root, textvariable=self.var_time, font=self.font_num).grid(row=0, column=0)
        Button(self.root, textvariable=self.var_face, font=self.font_face, command=self.restart, relief='groove',).grid(row=0, column=1)
        Label(self.root, textvariable=self.var_num, font=self.font_num).grid(row=0, column=2)

        self.frame = Frame(self.root)

        self.vars = [[StringVar() for i in range(self.w)] for j in range(self.h)]
        self.buttons = [[None for i in range(self.w)] for j in range(self.h)]
        self.units = [[MineUnit(self, j, i) for i in range(self.w)] for j in range(self.h)]

        for x in range(self.w):
            for y in range(self.h):
                self.buttons[x][y] = Button(self.frame,
                                            textvariable=self.vars[x][y],
                                            command=self.units[x][y].click,
                                            relief='groove',
                                            bd=1,
                                            font=self.font_unit,
                                            width=3, height=1,
                                            activebackground='gray',
                                            bg='snow')
                self.buttons[x][y].bind("<Button-3>", self.units[x][y].right_click)
                self.buttons[x][y].grid(row=y, column=x)

        self.frame.grid(row=1, columnspan=3)

        self.refresh()

    def init_data(self):
        self.mine = Mine(self.w, self.h, self.n)

        self.var_num.set("%03d" % self.n)
        self.var_time.set("000")
        self.var_face.set("K")
        self.win = None
        self.stated = False
        self.time = 0
        self.thread = None

        for x in self.buttons:
            for y in x:
                y.grid_forget()

        self.vars = [[StringVar() for i in range(self.w)] for j in range(self.h)]
        self.buttons = [[None for i in range(self.w)] for j in range(self.h)]
        self.units = [[MineUnit(self, j, i) for i in range(self.w)] for j in range(self.h)]
        self.signs = [[False for i in range(self.w)] for j in range(self.h)]

        for x in range(self.w):
            for y in range(self.h):
                self.buttons[x][y] = Button(self.frame,
                                            textvariable=self.vars[x][y],
                                            command=self.units[x][y].click,
                                            relief='groove',
                                            bd=1,
                                            font=self.font_unit,
                                            width=3, height=1,
                                            activebackground='gray',
                                            bg='snow')
                self.buttons[x][y].bind("<Button-3>", self.units[x][y].right_click)
                self.buttons[x][y].grid(row=y, column=x)

        self.refresh()

    def time_loop(self):
        while self.stated is True:
            try:
                time.sleep(1)
                self.time = self.time + 1
                self.var_time.set("%03d" % self.time)
            except Exception as e:
                print(e)
                continue

    def refresh(self):
        for x in range(self.w):
            for y in range(self.h):
                self.buttons[x][y].configure(fg=self.COLORS[self.mine.map[x][y]])

                if self.mine.dis[x][y] is True:
                    self.vars[x][y].set(self.CODE[self.mine.map[x][y]])
                    if self.mine.map[x][y] == 0:
                        self.buttons[x][y].configure(bg=self.COLORS[self.mine.map[x][y]])
                else:
                    self.vars[x][y].set(self.CODE[-2])
                if self.win is True:
                    if self.signs[x][y] is True:
                        if self.mine.map[x][y] == -1:
                            self.buttons[x][y].configure(bg='green')
                        else:
                            self.buttons[x][y].configure(bg='red')
                    if self.mine.map[x][y] == -1:
                        self.vars[x][y].set(self.CODE[self.mine.map[x][y]])

    def restart(self):
        # self.root.destroy()
        # self.__init__(Tk(), w=self.w, h=self.h, n=self.n)
        self.init_data()


class MineUnit:
    def __init__(self, ui_: MineUi, x: int, y: int):
        self.ui = ui_
        self.x, self.y = x, y

    def click(self):
        if self.ui.win is not None:
            return
        if self.ui.win is None and self.ui.stated is False:
            self.start_timer()
        res = self.ui.mine.dig(self.x, self.y)
        # You lost
        if res is True:
            # self.ui.mine.dis = [[True for i in range(self.ui.w)] for j in range(self.ui.h)]
            for x in range(self.ui.w):
                for y in range(self.ui.h):
                    if self.ui.mine.map[x][y] == -1:
                        self.ui.mine.dis[x][y] = True
                        self.ui.buttons[x][y].configure(bg='red')
            self.ui.win = False
            self.ui.var_face.set("L")
            self.ui.stated = False
            self.ui.refresh()
            return

        if self.ui.mine.win():
            self.ui.win = True
            self.ui.var_face.set("J")
            self.ui.stated = False
            self.ui.refresh()
            return

        self.right_judge()

        self.ui.refresh()

    def right_click(self, argv):
        if self.ui.win is not None:
            return
        if self.ui.signs[self.x][self.y] is False:
            self.ui.signs[self.x][self.y] = True
            self.ui.buttons[self.x][self.y].configure(bg='blue')
        else:
            self.ui.signs[self.x][self.y] = False
            self.ui.buttons[self.x][self.y].configure(bg='snow')
        self.right_judge()

    def right_judge(self):
        sumi = 0
        for x in range(self.ui.w):
            sumi = sumi + self.ui.signs[x].count(True)
        if sumi == self.ui.n:
            flag = True
            for x in range(self.ui.w):
                if flag is True:
                    for y in range(self.ui.h):
                        if self.ui.signs[x][y] is True and self.ui.mine.map[x][y] != -1:
                            flag = False
                            break
            if flag is True:
                self.ui.win = True
                self.ui.var_face.set("J")
                self.ui.stated = False
                self.ui.refresh()
                return

    def start_timer(self):
        if self.ui.thread is not None:
            return
        self.ui.thread = threading.Thread(target=self.ui.time_loop)
        self.ui.thread.setDaemon(True)
        self.ui.stated = True
        self.ui.thread.start()


class ConfigUi:
    def __init__(self, root):
        self.root = root
        self.frame = Frame(self.root)
        self.vars = [StringVar() for i in range(3)]
        self.w = Entry(self.frame, textvariable=self.vars[0])
        self.h = Entry(self.frame, textvariable=self.vars[1])
        self.n = Entry(self.frame, textvariable=self.vars[2])
        self.w.insert(0, "15")
        self.h.insert(0, "15")
        self.n.insert(0, "10")
        Label(self.frame, text="宽度").grid(row=0, column=0)
        Label(self.frame, text="高度").grid(row=1, column=0)
        Label(self.frame, text="雷数").grid(row=2, column=0)
        self.w.grid(row=0, column=1)
        self.h.grid(row=1, column=1)
        self.n.grid(row=2, column=1)
        Button(self.frame, text='开始',
               command=lambda: (self.frame.destroy(),
                                MineUi(self.root, w=int(self.vars[0].get()), h=int(self.vars[1].get()), n=int(self.vars[2].get()))))\
            .grid(row=3, columnspan=2, sticky=W+E)
        self.frame.grid()


if __name__ == '__main__':
    # ui = MineUi(Tk(), w=20, h=20, n=5)
    # ui.root.mainloop()
    _root = Tk()
    cui = ConfigUi(_root)
    cui.root.mainloop()

