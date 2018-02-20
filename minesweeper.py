"""
MIT License

Copyright (c) 2018 Alexander Liao

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import print_function, division

import sys, os, fcntl, struct, termios, random, time

if sys.version[0] == "2": input = raw_input

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen. From http://code.activestate.com/recipes/134892/"""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchMacCarbon()
            except(AttributeError, ImportError):
                self.impl = _GetchUnix()
    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys, termios # import termios now or else you'll get the Unix version on the Mac
    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt
    def __call__(self):
        import msvcrt
        return chr(msvcrt.getch()[0])

class _GetchMacCarbon:
    """
    A function which returns the current ASCII key that is down;
    if no ASCII key is down, the null string is returned. The
    page http://www.mactech.com/macintosh-c/chap02-1.html was
    very helpful in figuring out how to do this.
    """
    def __init__(self):
        import Carbon
        Carbon.Evt #see if it has this (in Unix, it doesn't)
    def __call__(self):
        import Carbon
        if Carbon.Evt.EventAvail(0x0008)[0]==0: # 0x0008 is the keyDownMask
            return ''
        else:
            #
            # The event contains the following info:
            # (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            #
            # The message (msg) contains the ASCII char which is
            # extracted with the 0x000000FF charCodeMask; this
            # number is converted to an ASCII character with chr() and
            # returned
            #
            (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            return chr(msg & 0x000000FF)

def getKey():
    inkey = _Getch()
    while True:
        k = inkey()
        if k != '': break
    return k

def getOption(options):
    code = 0
    while True:
        code = ord(getKey())
        if code in options: return code

def getComboOption(options):
    code = []
    while True:
        code.append(ord(getKey()))
        if code in options: return code
        if not any(option[:len(code)] == code for option in options): code = []

def draw_char(r, c, char):
    sys.stdout.write("\033[%d;%dH%s\033[1B" % (r, c, char))

def write_char(char):
    sys.stdout.write(char)

def clear():
    sys.stdout.write("\033[2J\033[1;1H")

def reset():
    sys.stdout.write("\033[0m\033[40m")

def size():
    return struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))[:2]

def getIntInput(prompt, retry, MIN = None, MAX = None):
    try:
        val = int(input(prompt))
        if (MIN is None or val >= MIN) and (MAX is None or val <= MAX):
            return val
    except:
        pass
    while True:
        try:
            val = int(input(retry))
            if (MIN is None or val >= MIN) and (MAX is None or val <= MAX):
                return val
        except:
            pass

def start():
    print("Terminal Minesweeper v0.1 by Alexander Liao (c) 2018.")
    print("This software is provided as-is with no warranty.")
    print("See LICENSE for more information. This software is licensed under the MIT License.")
    print()
    diff = input("Please select a difficulty [easy | medium | hard | custom]: ").lower()
    while diff not in ["easy", "medium", "hard", "custom"]:
        diff = input("Invalid selection. Please choose from [easy | medium | hard | custom]: ").lower()
    if diff == "easy":
        width  = 8
        height = 8
        mines  = 10
    elif diff == "medium":
        width  = 16
        height = 16
        mines  = 40
    elif diff == "hard":
        width  = 30
        height = 16
        mines  = 99
    else:
        width  = getIntInput("Please enter a width between 1 and %d: " % size()[1], "Not a valid integer in the range. Please try again: ", 1, size()[1])
        height = getIntInput("Please enter a height between 1 and %d: " % size()[0], "Not a valid integer in the range. Please try again: ", 1, size()[0])
        mines  = getIntInput("Please enter a number of mines between 1 and %d: " % (width * height), "Not a valid integer in the range. Please try again: ", 1, width * height)
    grid = [[0] * width for _ in range(height)]
    coords = [(r, c) for r in range(height) for c in range(width)]
    random.shuffle(coords)
    coords = coords[:mines]
    neighbor_info = [[0] * width for _ in range(height)]
    for r, c in coords:
        grid[r][c] = 1
        for (R, C) in ((r + 1, c), (r, c + 1), (r - 1, c), (r, c - 1)):
            if 0 <= R < height and 0 <= C < width:
                neighbor_info[R][C] += 1
    player_info = [[0] * width for _ in range(height)]
    cx = 0
    cy = 0
    def show_grid():
        clear()
        h = len(str(height))
        w = len(str(width))
        print(" " * (h + cx) + "v")
        for i in range(w):
            q = 10 ** (w - i - 1)
            print(" " * h + "".join(str(j // q % (q * 10) if j >= q or (j == 0 and q == 1) else " ") for j in range(width)))
        for j, r in enumerate(player_info):
            print((">" if j == cy else " ") + str(j).rjust(w) + "".join(["-"][e] for e in r))
    show_grid()
    while True:
        mode = getComboOption([(27, 91, 65), (27, 91, 66), (27, 91, 67), (27, 91, 68)])
        if mode == (27, 91, 65):
            cy -= 1
            cy %= height
        elif mode == (27, 91, 66):
            cy += 1
            cy %= height
        elif mode == (27, 91, 67):
            cx += 1
            cx %= width
        elif mode == (27, 91, 68):
            cx -= 1
            cx %= width
        show_grid()

start()