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
    sys.stdout.flush()

def write_char(char):
    sys.stdout.write(char)
    sys.stdout.flush()

def clear():
    sys.stdout.write("\033[0m\033[2J\033[1;1H")
    sys.stdout.flush()

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

def start(*vals):
    clear()
    print("Terminal Minesweeper v0.1 by Alexander Liao (c) 2018.")
    print("This software is provided as-is with no warranty.")
    print("See LICENSE for more information. This software is licensed under the MIT License.")
    print()
    diff = vals[0] if len(vals) >= 1 else input("Please select a difficulty [easy | medium | hard | custom]: ").lower()
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
        width  = vals[1] if len(vals) >= 2 and type(vals[1]) == int else getIntInput("Please enter a width between 1 and %d: " % (size()[1] - 5), "Not a valid integer in the range. Please try again: ", 1, size()[1] - 3)
        height = vals[2] if len(vals) >= 3 and type(vals[2]) == int else getIntInput("Please enter a height between 1 and %d: " % (size()[0] - 5), "Not a valid integer in the range. Please try again: ", 1, size()[0] - 3)
        mines  = vals[3] if len(vals) >= 4 and type(vals[3]) == int else getIntInput("Please enter a number of mines between 1 and %d: " % (width * height), "Not a valid integer in the range. Please try again: ", 1, width * height)
    grid = [[0] * width for _ in range(height)]
    coords = [(r, c) for r in range(height) for c in range(width) if r or c]
    random.shuffle(coords)
    coords = set(coords[:mines])
    neighbor_info = [[0] * width for _ in range(height)]
    for r, c in coords:
        grid[r][c] = 1
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i or j:
                    R, C = r + i, c + j
                    if 0 <= R < height and 0 <= C < width:
                        neighbor_info[R][C] += 1
    player_info = [[0] * width for _ in range(height)]
    cx = 0
    cy = 0
    strings = [
        " ",
        "\033[1;31mF",
        "\033[1;30m0",
        "\033[33m1",
        "\033[34m2",
        "\033[1;33m3",
        "\033[1;34m4",
        "\033[1;35m5",
        "\033[1;37m6",
        "\033[1;37m7",
        "\033[1;37m8"
    ]
    def reveal(R, C, current = False):
        passed = set()
        coords = {(R, C)}
        while coords:
            passed |= coords
            current = list(coords)
            coords = set()
            for r, c in current:
                if 0 <= r < height and 0 <= c < width and not grid[r][c]:
                    a = player_info[r][c] = neighbor_info[r][c] + 2
                    sys.stdout.write("\033[%d;%dH%s" % (r + 3, c + 3, strings[a] + "\033[0m"))
                    sys.stdout.flush()
                    subcoords = set()
                    total = 0
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            if (i or j) and 0 <= r + i < height and 0 <= c + j < width:
                                if player_info[r + i][c + j] == 1:
                                    total += 1
                                if (r + i, c + j) not in passed:
                                    subcoords.add((r + i, c + j))
                    if a == 2: #total + 2 == a: # TODO ask betseg about this
                        coords |= subcoords
    def display_border():
        print("\n +" + "-" * width + "+\n" + (" |" + " " * width + "|\n") * height + " +" + "-" * width + "+", end = "")
    def wipe_vcursors():
        sys.stdout.write("\033[1;1H\033[0m  " + " " * width)
        sys.stdout.flush()
    def wipe_hcursors():
        sys.stdout.write("\033[1;1H\033[0m\n " + "\n " * height)
        sys.stdout.flush()
    def show_grid():
        clear()
        h = len(str(height))
        w = len(str(width))
        print(" " * cx + "  v")
        print(" +" + "-" * width + "+")
        for j, r in enumerate(player_info):
            print((">" if j == cy else " ") + "|" + "".join(strings[e] + "\033[0m" for i, e in enumerate(r)) + "|")
        print(" +" + "-" * width + "+", end = "")
    clear()
    display_border()
    sys.stdout.write("\033[1;1H  v\n\n>\033[3;3H")
    sys.stdout.flush()
    start = time.time()
    flagged = set()
    while True:
        mode = getComboOption([[113], [102], [32], [27, 91, 65], [27, 91, 66], [27, 91, 67], [27, 91, 68]])
        if mode == [113]:
            sys.stdout.write("\033[%d;1H" % (height + 5))
            break
        elif mode == [102]:
            if player_info[cy][cx] == 1:
                flagged.remove((cy, cx))
                player_info[cy][cx] = 0
                sys.stdout.write("\033[%d;%dH\033[0m " % (cy + 3, cx + 3))
                sys.stdout.flush()
            elif player_info[cy][cx] == 0:
                flagged.add((cy, cx))
                player_info[cy][cx] = 1
                sys.stdout.write("\033[%d;%dH\033[1;31mF\033[0m" % (cy + 3, cx + 3))
                sys.stdout.flush()
            if flagged == coords:
                print("\033[%d;1HYou win!\nThe game took %.2f seconds." % (height + 5, time.time() - start))
                break
        elif mode == [32]:
            if player_info[cy][cx] == 1:
                continue
            if grid[cy][cx]:
                print("\033[%d;1HOops! You exploded. Better luck next time!" % (height + 5))
                break
            else:
                reveal(cy, cx)
        elif mode == [27, 91, 65]:
            cy -= 1
            cy %= height
        elif mode == [27, 91, 66]:
            cy += 1
            cy %= height
        elif mode == [27, 91, 67]:
            cx += 1
            cx %= width
        elif mode == [27, 91, 68]:
            cx -= 1
            cx %= width
        wipe_hcursors()
        wipe_vcursors()
        sys.stdout.write("\033[%d;1H>\033[1;%dHv\033[%d;%dH" % (cy + 3, cx + 3, cy + 3, cx + 3))
        sys.stdout.flush()

start()
