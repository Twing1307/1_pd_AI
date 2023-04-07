#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import (Qt, QRectF, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView,
    QGraphicsObject, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QWidget, QRadioButton, QButtonGroup, 
    QDialog, QDialogButtonBox, QMessageBox)
from PyQt5.QtGui import (QPainter)

import queue

N = 8
MAX_DEPTH = 6

class MainWindow(QWidget):
    # Galvenais logs
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game")

        self.player_score = 0
        self.computer_score = 0
        
        self.board = Board()
        
        top_layout = QHBoxLayout()
        
        button = QPushButton("New")
        button.clicked.connect(self.onNew)

        self.label = QLabel()

        top_layout.addWidget(button)
        top_layout.addStretch()
        top_layout.addWidget(self.label)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.board)

        self.setLayout(layout)
        self.updateScore()

        self.board.playerWin.connect(self.playerWin)
        self.board.computerWin.connect(self.computerWin)

        self.board.restart("sheep")

    @pyqtSlot()
    def onNew(self):
        # Sākam jaunu spēli
        dialog = Dialog()
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

        if dialog.sheep_button.isChecked():
            self.board.restart("sheep")
        else:
            self.board.restart("wolfs")
    
    @pyqtSlot()
    def playerWin(self):
        self.player_score += 1
        self.updateScore()
        QMessageBox.information(self, "Victory", "Player win!")

    @pyqtSlot()
    def computerWin(self):
        self.computer_score += 1
        self.updateScore()
        QMessageBox.information(self, "Victory", "Computer win!")

    def updateScore(self):
        self.label.setText(f'{self.player_score}:{self.computer_score}')

class Dialog(QDialog):
    # Spēlētāja atlases logs
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Dialog")
        self.setGeometry(100, 100, 200, 100)

        self.sheep_button = QRadioButton("Sheep")
        self.wolfs_button = QRadioButton("Wolfs")
        self.sheep_button.setChecked(True)

        group = QButtonGroup()
        group.addButton(self.sheep_button)
        group.addButton(self.wolfs_button)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        vbox = QVBoxLayout()

        vbox.addWidget(self.sheep_button)
        vbox.addWidget(self.wolfs_button)
        vbox.addWidget(buttonBox)
        self.setLayout(vbox)
 

class Cell(QGraphicsObject):
    # Dēļa rūts
    onClick = pyqtSignal(int, int)

    def __init__(self, row, col, size):
        super().__init__()
        self.row = row
        self.col = col

        self.x = col * size
        self.y = row * size
        self.w = size
        self.h = size

    def setBrush(self, brush):
        self.brush = brush

    def boundingRect(self):
        return QRectF(self.x, self.y, self.w, self.h)

    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.drawRect(self.x, self.y, self.w, self.h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.onClick.emit(self.row, self.col)

class Circle(QGraphicsObject):
    # Spēļu figūra
    onClick = pyqtSignal(int, int)

    def __init__(self, row, col, size):
        super().__init__()
        self.row = row
        self.col = col
        self.size = size

        self.radius = int(0.35 * size)

        self.w = 2 * self.radius
        self.h = 2 * self.radius

        self.setCell(row, col)

    def setCell(self, row, col):
        # Figuras pārvietošana
        self.row = row
        self.col = col

        self.x = int(col * self.size + 0.5 * self.size) - self.radius
        self.y = int(row * self.size + 0.5 * self.size) - self.radius

    def setBrush(self, brush):
        self.brush = brush

    def boundingRect(self):
        return QRectF(self.x, self.y, self.w, self.h)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush)
        painter.drawEllipse(self.x, self.y, self.w, self.h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.onClick.emit(self.row, self.col)

class Tree:
    # Risinājumu koks

    def __init__(self, type, move, score):
        # Konstruktors
        self.score = score  # Gajiena novertešana
        self.type = type    # Figuras tips
        self.move = move    # Gajiens (prev_pos, next_pos)  

        self.children = []  # Bērnmezglu saraksts

    def addChild(self, child):
        # Mezgla pievienošana
        self.children.append(child)


class Board(QGraphicsView):
    # Spēles tāfele
    playerWin = pyqtSignal()
    computerWin = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Izveidojam grafikas ainu
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        size = 60

        indent = 5

        self.MAX_DEPTH = MAX_DEPTH

        self.cells = [[None] * N for _ in range(N)]

        # Veidojam dēļa šūnas
        for row in range(N):
            for col in range(N):
                cell = Cell(row, col, size)

                cell.onClick.connect(self.clicked)

                if (row + col) % 2 == 0:
                    cell.setBrush(Qt.white)
                else:
                    cell.setBrush(Qt.gray)

                self.cells[row][col] = cell
                
                self.scene.addItem(cell)

        
        # Figuru virzieni
        self.wolf_direction = [(1, -1), (1, 1)]
        self.sheep_direction = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        # Pievienojam vilkus
        self.wolfs = []
        for i in range(N // 2):
            wolf = Circle(0, 1 + 2 * i, size)
            wolf.onClick.connect(self.clicked)
            wolf.setBrush(Qt.green)
            wolf.direction = self.wolf_direction
            self.scene.addItem(wolf)
            self.wolfs.append(wolf)

        # Pievienojam aitu
        self.sheep = Circle(N - 1, 2, size)
        self.sheep.onClick.connect(self.clicked)
        self.sheep.setBrush(Qt.yellow)
        self.sheep.direction = self.sheep_direction
        self.scene.addItem(self.sheep)

        # Visu figuru saraksts
        self.figures = list(self.wolfs)
        self.figures.append(self.sheep)

        # Pašreizējā figura
        self.current = self.sheep

        # Iestatām dēļa izmērus
        width  = N * size + 2 * indent
        height = N * size + 2 * indent
        self.setFixedSize(width, height)
        
        self.show()

    def restart(self, player):
        # Sākam spēli no jauna
        if self.current:
            self.highlightFigure(self.current, Qt.gray)

        self.current_player = player

        # Aitas sākumstāvoklis
        self.sheep.setCell(N - 1, 2)

        index = 1

        # Vilku sākumstāvoklis
        for wolf in self.wolfs:
            wolf.setCell(0, index)
            index += 2

        self.sheep_step()

    def update(self):
        self.scene.update()

    def initMap(self):
        # Inicializējam karti
        self.map = [["E"] * N for _ in range(N)]
        self.map[self.sheep.row][self.sheep.col] = "S"
        for wolf in self.wolfs:
            self.map[wolf.row][wolf.col] = "W"

    def canMove(self, move):
        # Pārbaudām, vai var veikt gājienu
        if self.isOutOfBorder(move[0], move[1]):
            return False

        if self.map[move[0]][move[1]] == "E":
            return True
        else:
            return False

    def doMove(self, prev_pos, next_pos):
        # Veicam gājienu
        if self.canMove(next_pos):
            figure = self.map[prev_pos[0]][prev_pos[1]]
            self.map[prev_pos[0]][prev_pos[1]] = "E"
            self.map[next_pos[0]][next_pos[1]] = figure

    def heuristic(self, sheep):
        # Heiristiskā funkcija izvērtē, cik gājienu laikā aita var sasniegt uzvaru
        # ar nosacījumu, ka vilki ir nekustīgi
        # Jo mazāk jo labāk
        # O(n) sarežģītība
        if self.sheep.row == 0:
            # Aita augšējā rindā
            # Mērķis sasniegts
            return 0

        self.map[sheep[0]][sheep[1]] = 0 # Inicializējam aitas 
                                         # sākumstāvokli

        # Izmantojam rindu un meklēšanu platumā
        q = queue.Queue() # Izveidojam tukšu rindu
        q.put(sheep)      # Pievienojam rindai sākuma pozīciju

        while not q.empty():  # Meklēt, kamēr rindā ir elementi
            current = q.get() # Izņemam elemetu no rindas sākuma 

            for direction in self.sheep_direction:
                # Izvētīsim visus iespējamos gājienus no pašreizējās pozīcijas
                move = (current[0] + direction[0], 
                        current[1] + direction[1])
                if self.isOutOfBorder(move[0], move[1]):
                    # Pārbaudām, vai figūra ir ārpus dēļa
                    continue
                if self.map[move[0]][move[1]] == "E":
                    # Ja lauks ir brīvs, aizpildām to ar vērtību
                    # kas ir vienāda ar ceļa garumu
                    self.map[move[0]][move[1]] = (
                        self.map[current[0]][current[1]] + 1)
                    q.put(move) # Rindai pievienojam jaunu pozīciju

        # Atrodam minimālo ceļu līdz augšējai rindai
        min_value = float("inf")
        for i in range(N // 2):
            # Parbaudam vērtības augšējā rindā
            if ((not self.map[0][2 * i + 1] in ["E", "S", "W"]) and
                    self.map[0][2 * i + 1] < min_value):
                # Apskatām tikai skaitliskās vērtības
                # un atrodam minimālo
                min_value = self.map[0][2 * i + 1]

        self.map[sheep[0]][sheep[1]] = "S" # Nometam vērtību
                                           # šunā ar aitu

        # Atiestatām kartes statusu
        for row in range(N):
            for col in range(N):
                if not self.map[row][col] in ["E", "S", "W"]:
                    # Ja šūnā ir skaitlis, mēs to atzīmējam,
                    # kā E(empty)

                    self.map[row][col] = "E"

        return min_value

    def min_max(self, tree, type, depth, alpha, beta):
        # Minimaksa algoritms ar alfa beta nogriešanu
        # Izvēlas datoram maksimāli izdevīgu gājienu
        # vilkiem - maksimālais vērtējums, aitai - minimālais
        if depth == 0:
            # Ja tas ir algoritma sākuma izsauksāna,
            # inicializējam karti
            self.initMap()

        # Inicializējam sākotnējās vērtības
        sheep = None  # Aitas pozīcija
        wolfs = []    # Vilku pozīciju saraksts
        best_move = None  # Labākais gājiens

        # Atrodam aitas un vilku sākumstāvokli 
        for row in range(N):
            for col in range(N):
                if self.map[row][col] == "S":
                    sheep = (row, col)
                elif self.map[row][col] == "W":
                    wolfs.append((row, col))

        if depth > self.MAX_DEPTH:
            # Sasniegts maksimālais meklēšanas dziļums
            # Izmantojam heiristiku un izejam no rekursijas
            score = self.heuristic(sheep)
            tree.score = score
            return tree

        if type == "sheep":
            # Aitas gajiens
            best_score = float("inf") # Labākā novērtējuma sākuma vērtība
            for direction in self.sheep_direction:
                # Pārbaudām visus iespējamos gājienu variantus
                current_pos = sheep # Pašreizējā pozīcija
                # Atrodam nākamo gājienu
                next_pos = (current_pos[0] + direction[0],
                            current_pos[1] + direction[1])
                if self.canMove(next_pos): # Ja gajiens ir iespējama
                    # Veicam gājienu
                    self.doMove(current_pos, next_pos)
                    move = (current_pos, next_pos)
                    # Izveidojam risinājuma koka bērnmezglu
                    child = Tree("wolf", move, 0)
                    # Veicam rekursīvu izsaukšanu
                    self.min_max(child, "wolf", 
                        depth + 1, alpha, beta)
                    result = child.score
                    # Kokam pievienojam bērnmēzglu
                    tree.addChild(child)
                    # Atcelt gajienu
                    self.doMove(next_pos, current_pos)

                    if not best_move or result < best_score:
                        # Meklējam labāko gājienu
                        best_move = (current_pos, next_pos)
                        best_score = result

                    # Mainām beta nozīmi
                    beta = min(beta, result)
                    
                    # Alfa-beta nogriešana
                    if beta <= alpha:
                        break
        else:
            # Vilku gajiens
            best_score = float("-inf") # Labākā novērtējuma sākuma vērtība
            for wolf in wolfs:
                # Visiem vilkiem
                for direction in self.wolf_direction:
                    # Pārbaudām visus gājienu variantus
                    current_pos = wolf # Pašreizējā pozīcija

                    # Atrodam nākamo gājienu
                    next_pos = (current_pos[0] + direction[0],
                                current_pos[1] + direction[1])
                    if self.canMove(next_pos): # Ja gaita ir iespējama
                        # Veicam gājienu
                        self.doMove(current_pos, next_pos)
                        move = (current_pos, next_pos)
                        # Izveidojam risinājuma koka bērnmezglu
                        child = Tree("sheep", move, 0)
                        # Veicam rekursīvu izaicinājumu
                        self.min_max(child, "sheep", 
                                depth + 1, alpha, beta)
                        result = child.score
                        # Kokam pievienojam bērnelementu
                        tree.addChild(child)
                        # Atcelt gajienu
                        self.doMove(next_pos, current_pos)

                        if not best_move or result > best_score:
                            # Meklējam labāko gājienu
                            best_move = (current_pos, next_pos)
                            best_score = result
                        
                        # Koriģējam Alfas vērtību 
                        alpha = max(alpha, result)

                        # Alfa-beta nogriešana
                        if beta <= alpha:
                            break

        if not best_move:
            # Nav atrasts labākais gājiens
            # izmantojam heiristisko novērtējumu
            score = self.heuristic(sheep)
            tree.score = score
            return tree

        if depth == 0:
            # Ja dziļums ir 0
            # Dators veic gājienu
            if type == "sheep":
                # Staigā aita
                (prev_pos, next_pos) = best_move
                self.highlightFigure(self.current, Qt.gray)
                # Veicam gājienu
                self.current.setCell(next_pos[0], next_pos[1])
                # Nododam gājienu spēlētājam
                self.wolfs_step()
            else:
                # Staigā vilks
                (prev_pos, next_pos) = best_move
                current = None
                for wolf in self.wolfs:
                    # Atrodam vilku, kas staigās
                    if (wolf.row == prev_pos[0] and 
                        wolf.col == prev_pos[1]):
                        current = wolf
                        break
                # Veicam gājienu
                current.setCell(next_pos[0], next_pos[1])
                # Nododam gājienu spēlētājam
                self.sheep_step()

        tree.score = best_score # Saglabājam labāko novērtējumu
        return tree             # Atgriežam rezultātu

    def highlightCells(self, cells, color):
        for cell in cells:
            self.cells[cell[0]][cell[1]].setBrush(color)

    def isOutOfBorder(self, row, col):
        if row < 0 or row >= N or col < 0 or col >= N:
            return True
        return False

    def getPossibleMoves(self, figure):
        # Iegūstam iespējamo gājienu sarakstu
        moves = [(figure.row + e[0], figure.col + e[1]) 
            for e in figure.direction]
        moves = [x for x in moves if not self.isOutOfBorder(x[0], x[1])]
        
        filled = [(x.row, x.col) for x in self.figures]

        moves = [x for x in moves if not x in filled]

        return moves

    def highlightFigure(self, figure, color):
        # Iespējamo gājienu izgaismošana
        if figure:
            moves = self.getPossibleMoves(figure)
            self.highlightCells(moves, color)
   
    def checkVictory(self):
        # Uzvaras apstākļu pārbaude
        if self.sheep.row == 0:
            if self.current_player == "sheep":
                self.playerWin.emit()
            else:
                self.computerWin.emit()

            return True
        
        moves = self.getPossibleMoves(self.sheep)
        if not moves:
            if self.current_player == "wolfs":
                self.playerWin.emit()
            else:
                self.computerWin.emit()

            return True

        moves = []
        for wolf in self.wolfs:
            moves = moves + self.getPossibleMoves(wolf)

        if not moves:
            if self.current_player == "sheep":
                self.playerWin.emit()
            else:
                self.computerWin.emit()
        
            return True

        return False
 
    def sheep_step(self):
        # Aitas gajiens
        self.current = self.sheep
        self.current_step = "sheep"
        self.update()
        
        flag = self.checkVictory()
        if flag:
            return
       
        if self.current_player == "wolfs":
            tree = Tree("sheep", None, 0)
            self.min_max(tree, "sheep", 0, 
                float("-inf"), float("inf"))
        else:
            self.highlightFigure(self.current, Qt.darkGray)
            self.update()
  
    def wolfs_step(self):
        # Vilku gajiens
        self.current = None
        self.current_step = "wolfs"

        self.update()
        
        flag = self.checkVictory()
        if flag:
            return
        
        if self.current_player == "sheep":
            tree = Tree("wolfs", None, 0)
            self.min_max(tree, "wolfs", 0, 
                float("-inf"), float("inf"))
        self.update()
 
    @pyqtSlot(int, int)
    def clicked(self, row, col):
        # Klikšķa apstrāde
        if self.current_step == "wolfs":
            wolfs = [(x.row, x.col) for x in self.wolfs]
            if (row, col) in wolfs:
                wolf = [x for x in self.wolfs 
                    if x.row == row and x.col == col]
                if wolf:
                    self.highlightFigure(self.current, Qt.gray)
                    self.current = wolf[0]
                    self.highlightFigure(self.current, Qt.darkGray)
        if self.current:
            moves = self.getPossibleMoves(self.current)
            if (row, col) in moves:
                self.highlightFigure(self.current, Qt.gray)
                self.current.setCell(row, col)
                
                self.update()
                
                if self.current_step == "wolfs":
                    self.sheep_step()
                else:
                    self.wolfs_step()

        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
