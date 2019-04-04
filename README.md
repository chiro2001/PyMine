## PyMine - 扫雷 for Python

emmmm...闲来无事...?

总之这个是我在这个~~「悲喜交加」的~~清明+三月三假期做的。

## 过程

```python
# 这里是开始UI，负责相关设置
class ConfigUi:...

# 这个是计算部分 
class Mine:...

# 这个是主窗口的UI
class MineUi:...

# 这个...是每个按钮绑定的一个类
# 这个貌似会很耗费内存
# 要怪就怪Tk的command指向的函数调用的时候不能加参数
class MineUnit:...

# 这个字体加载解决方法：
# 做到了加载TTF字体
# <https://stackoverflow.com/questions/11993290/truly-custom-font-in-tkinter>
def load_font(fontpath, private=True, enumerable=False):...

```

## 截图
![开始界面](https://github.com/LanceLiang2018/PyMine/raw/master/imgs/img1.png)

![游戏中](https://github.com/LanceLiang2018/PyMine/raw/master/imgs/img3.png)

![You Lost](https://github.com/LanceLiang2018/PyMine/raw/master/imgs/img4.png)

![You Win](https://github.com/LanceLiang2018/PyMine/raw/master/imgs/img5.png)

## 蛤

我已经写完了