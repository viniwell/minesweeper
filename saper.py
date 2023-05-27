import random
import time
from PyQt6 import QtGui

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

LEVELS = (
    (8, 10),
    (16, 40),
    (24, 99),
)

IMG_BOMB = QImage('./images/bomb.png')
IMG_CLOCK = QImage('./images/clock.png')
IMG_START = QImage('./images/rocket.png')

STATUS_READY=0
STATUS_PLAY=1
STATUS_FAIL=2
STATUS_SUCCESS=3

STATUS_ICONS={
    STATUS_READY:'./images/plus.png',
    STATUS_PLAY:'./images/smiley.png',
    STATUS_FAIL:'./images/cross.png',
    STATUS_SUCCESS:'./images/smiley-lol.png',
    }


class Cell(QWidget):
    expandable=pyqtSignal(int, int)
    clicked=pyqtSignal()

    def __init__(self, x, y):
        super().__init__()
        self.setFixedSize(20, 20)

        self.x = x
        self.y = y

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = event.rect()
        if self.is_revealed:
            color=self.palette().color(QPalette.ColorRole.NColorRoles.Window)
            outer, inner=color, color
        else:
            outer, inner = Qt.GlobalColor.gray, Qt.GlobalColor.lightGray
        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_revealed:
            if self.is_mine:
                p.drawPixmap(r, QPixmap(IMG_BOMB))
            elif self.is_start:
                p.drawPixmap(r, QPixmap(IMG_START))
            else:
                pen = QPen(Qt.GlobalColor.black)
                p.setPen(pen)
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, str(self.mines_around))

    def reset(self):
        self.is_start = False
        self.is_mine = False
        self.mines_around = 0
        self.is_revealed = False
        self.is_flagged = False
        self.is_end = False
        self.update()
    
    def click(self):
        if not self.is_revealed and not self.is_flagged:
            self.reveal()

    def reveal(self):
        if not self.is_revealed:
            self.reveal_self()
            if self.mines_around==0:
                self.expandable.emit(self.x, self.y)

    def reveal_self(self):
        self.is_revealed = True
        self.update()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        if event.button()==Qt.MouseButton.LeftButton:
            self.click()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.level = 0
        self.board_size, self.mines_count = LEVELS[self.level]

        self.setWindowTitle('Сапер')
        self.initUI()
        self.init_grid()
        self.update_status(STATUS_READY)
        self.reset()
        self.setFixedSize(self.sizeHint())
        self.show()

    def initUI(self):
        central_widget = QWidget()
        toolbar = QHBoxLayout()

        self.mines = QLabel(str(self.mines_count))
        self.mines.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clock = QLabel('000')
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = self.mines.font()
        font.setPointSize(24)
        font.setWeight(75)
        self.mines.setFont(font)
        self.clock.setFont(font)

        self.button = QPushButton()
        self.button.setFixedSize(32, 32)
        self.button.setIconSize(QSize(32, 32))
        self.button.setIcon(QIcon('./images/smiley.png'))
        self.button.setFlat(True)

        l = QLabel()
        l.setPixmap(QPixmap.fromImage(IMG_BOMB))
        l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        toolbar.addWidget(l)
        
        toolbar.addWidget(self.mines)
        toolbar.addWidget(self.button)
        toolbar.addWidget(self.clock)

        l = QLabel()
        l.setPixmap(QPixmap.fromImage(IMG_CLOCK))
        l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        toolbar.addWidget(l)

        main_layout = QVBoxLayout()
        main_layout.addLayout(toolbar)

        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        main_layout.addLayout(self.grid)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def init_grid(self):
        for x in range(self.board_size):
            for y in range(self.board_size):
                cell = Cell(x, y)
                self.grid.addWidget(cell, x, y)
                cell.expandable.connect(self.expand_reveal)
                cell.clicked.connect(self.handle_click)


    def reset(self):
        self.mines_count = LEVELS[self.level][1]
        self.mines.setText(f'{self.mines_count:03d}')
        self.clock.setText('000')

        for _, _, cell in self.get_all_cells():
            cell.reset()

        mine_positions = self.set_mines()
        self.calc_mines_around()
        self.set_start()

    def get_all_cells(self):
        for x in range(self.board_size):
            for y in range(self.board_size):
                yield (x, y, self.grid.itemAtPosition(x, y).widget())

    def set_mines(self):
        positions = []
        while len(positions) < self.mines_count:
            x = random.randint(0, self.board_size - 1)
            y = random.randint(0, self.board_size - 1)
            if (x, y) not in positions:
                self.grid.itemAtPosition(x, y).widget().is_mine = True
                positions.append((x, y))
        return positions
    
    def calc_mines_around(self):
        for x, y, cell in self.get_all_cells():
            cell.mines_around = self.get_mines_around_cell(x, y)

    def get_mines_around_cell(self, x, y):
        cells = [cell for _, _, cell in self.get_around_cells(x, y)]
        return sum(1 if cell.is_mine else 0 for cell in cells)

    def get_around_cells(self, x, y):
        positions = []
        for xi in range(max(0, x-1), min(x+2, self.board_size)):
            for yi in range(max(0, y-1), min(y+2, self.board_size)):
                positions.append((xi, yi, self.grid.itemAtPosition(xi, yi).widget()))
        return positions
    
    def set_start(self):
        empty_cells = [cell
                       for x, y, cell
                       in self.get_all_cells()
                       if not cell.is_mine and cell.mines_around == 0
                      ]
        start_cell = random.choice(empty_cells)
        start_cell.is_start = True

        for _, _, cell in self.get_around_cells(start_cell.x, start_cell.y):
            if not cell.is_mine:
                cell.click()
    
    def expand_reveal(self, x, y):
        for _, _, cell in self.get_revealable_cells(x, y):
            cell.reveal()

    def get_revealable_cells(self, x, y):
        for x1, y1, cell in self.get_around_cells(x, y):
            if not cell.is_mine and not cell.is_flagged and not cell.is_revealed:
                yield(x1, y1, cell)
    
    def update_status(self, status):
        self.status=status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def handle_click(self):
        if self.status==STATUS_READY:
            self.update_status(STATUS_PLAY)
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec()