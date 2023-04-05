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
    # Главное окно
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
        # Начинаем новую игру
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
    # Окно выбора игрока
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
    # Клетка доски
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
    # Игровая фигура
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
        # Перемещение фигуры
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
    # Дерево решений

    def __init__(self, type, move, score):
        # Конструктор
        self.score = score  # Оценка хода
        self.type = type    # Тип фигуры
        self.move = move    # Ход (prev_pos, next_pos)  

        self.children = []  # Список дочерних узлов

    def addChild(self, child):
        # Добавление узла
        self.children.append(child)



class Board(QGraphicsView):
    # Игровая доска
    playerWin = pyqtSignal()
    computerWin = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Создаём графическую сцену
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        size = 60

        indent = 5

        self.MAX_DEPTH = MAX_DEPTH


        self.cells = [[None] * N for _ in range(N)]

        # Создаём клетки доски
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

        
        # Направления ходов фигур
        self.wolf_direction = [(1, -1), (1, 1)]
        self.sheep_direction = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        # Добавляем волков
        self.wolfs = []
        for i in range(N // 2):
            wolf = Circle(0, 1 + 2 * i, size)
            wolf.onClick.connect(self.clicked)
            wolf.setBrush(Qt.green)
            wolf.direction = self.wolf_direction
            self.scene.addItem(wolf)
            self.wolfs.append(wolf)

        # Добавляем овцу
        self.sheep = Circle(N - 1, 2, size)
        self.sheep.onClick.connect(self.clicked)
        self.sheep.setBrush(Qt.yellow)
        self.sheep.direction = self.sheep_direction
        self.scene.addItem(self.sheep)

        # Список всех фигур
        self.figures = list(self.wolfs)
        self.figures.append(self.sheep)

        # Текущая фигура
        self.current = self.sheep

        # Устанавливаем размер доски
        width  = N * size + 2 * indent
        height = N * size + 2 * indent
        self.setFixedSize(width, height)
        
        self.show()

    def restart(self, player):
        # Начинаем игру заново
        if self.current:
            self.highlightFigure(self.current, Qt.gray)

        self.current_player = player

        # Начальное положение овцы
        self.sheep.setCell(N - 1, 2)

        index = 1

        # Начальное положение волков
        for wolf in self.wolfs:
            wolf.setCell(0, index)
            index += 2

        self.sheep_step()

    def update(self):
        self.scene.update()

    def initMap(self):
        # Инициализируем карту
        self.map = [["E"] * N for _ in range(N)]
        self.map[self.sheep.row][self.sheep.col] = "S"
        for wolf in self.wolfs:
            self.map[wolf.row][wolf.col] = "W"

    def canMove(self, move):
        # Проверяем, можно ли сделать ход
        if self.isOutOfBorder(move[0], move[1]):
            return False

        if self.map[move[0]][move[1]] == "E":
            return True
        else:
            return False

    def doMove(self, prev_pos, next_pos):
        # Делаем ход
        if self.canMove(next_pos):
            figure = self.map[prev_pos[0]][prev_pos[1]]
            self.map[prev_pos[0]][prev_pos[1]] = "E"
            self.map[next_pos[0]][next_pos[1]] = figure

    def heuristic(self, sheep):
        # Эвристическая функция оценивает, за сколько ходов овца
        # может достичь победы, при условии, что волки неподвижны
        # Чем меньше тем лучше
        # Сложность O(n)
        if self.sheep.row == 0:
            # Овца в верхнем ряду
            # Цель достигнута
            return 0

        self.map[sheep[0]][sheep[1]] = 0 # Инициализируем начальное
                                         # положение овцы

        # Используем очередь и поиск в ширину
        q = queue.Queue() # Создаём пустую очередь
        q.put(sheep)      # Добавляем начальное положение в очередь

        while not q.empty():  # Поиск пока в очереди есть элементы
            current = q.get() # Извлекаем элемет из начала очереди 

            for direction in self.sheep_direction:
                # Провереяем все возможные ходы из текущей позиции
                move = (current[0] + direction[0], 
                        current[1] + direction[1])
                if self.isOutOfBorder(move[0], move[1]):
                    # Проверяем, выходит ли фигура за границы доски
                    continue
                if self.map[move[0]][move[1]] == "E":
                    # Если поле свободно, заполняем его значением
                    # равным длине пути
                    self.map[move[0]][move[1]] = (
                        self.map[current[0]][current[1]] + 1)
                    q.put(move) # Добавляем новую позицию в очередь

        # Находим минимальный путь до верхней строки
        min_value = float("inf")
        for i in range(N // 2):
            # Проверяем значения в верхней строке
            if ((not self.map[0][2 * i + 1] in ["E", "S", "W"]) and
                    self.map[0][2 * i + 1] < min_value):
                # Рассматриваем только числовые значения
                # и находим минимальное
                min_value = self.map[0][2 * i + 1]

        self.map[sheep[0]][sheep[1]] = "S" # Сбрасываем значение в
                                           # клетке с овцой

        # Сбрасываем состояние карты
        for row in range(N):
            for col in range(N):
                if not self.map[row][col] in ["E", "S", "W"]:
                    # Если в ячейке число то помечаем её, 
                    # как E(empty)

                    self.map[row][col] = "E"

        return min_value

    def min_max(self, tree, type, depth, alpha, beta):
        # Алгоритм мини-макс c альфа-бета отсечением
        # Выбирается ход максимально выгодный для компьютера
        # для волков - максимальная оценка, для овцы - минимальная
        if depth == 0:
            # Если это начальный вызов алгоритма, то
            # инициализируем карту
            self.initMap()


        # Инициализируем начальные значения
        sheep = None  # Позиция овцы
        wolfs = []    # Список позиций волков
        best_move = None  # Лучший ход

        # Находим начальное положение овцы и волков 
        for row in range(N):
            for col in range(N):
                if self.map[row][col] == "S":
                    sheep = (row, col)
                elif self.map[row][col] == "W":
                    wolfs.append((row, col))

        if depth > self.MAX_DEPTH:
            # Достигли максимальной глубины поиска
            # Используем эвристику и выходим из рекурсии
            score = self.heuristic(sheep)
            tree.score = score
            return tree

        if type == "sheep":
            # Ход овцы
            best_score = float("inf") # Начальное значение лучшей оценки
            for direction in self.sheep_direction:
                # Проверяем все возможные варианты ходов
                current_pos = sheep # Текущая позиция
                # Находим следующий ход
                next_pos = (current_pos[0] + direction[0],
                            current_pos[1] + direction[1])
                if self.canMove(next_pos): # Если ход возможен
                    # Делаем ход
                    self.doMove(current_pos, next_pos)
                    move = (current_pos, next_pos)
                    # Создаём дочерний узел дерева решений
                    child = Tree("wolf", move, 0)
                    # Делаем рекурсивный вызов
                    self.min_max(child, "wolf", 
                        depth + 1, alpha, beta)
                    result = child.score
                    # Добавляем дочерний узел в дерево
                    tree.addChild(child)
                    # Отменяем ход
                    self.doMove(next_pos, current_pos)

                    if not best_move or result < best_score:
                        # Ищем лучший ход
                        best_move = (current_pos, next_pos)
                        best_score = result

                    # Меняем значание беты
                    beta = min(beta, result)
                    
                    # Альфа-бета отсечение
                    if beta <= alpha:
                        break
        else:
            # Ход волков
            best_score = float("-inf") # Начальное значание лучшей оценки
            for wolf in wolfs:
                # Для всех волков
                for direction in self.wolf_direction:
                    # Проверяем все варианты ходов
                    current_pos = wolf # Текущая позиция

                    # Находим следующий ход
                    next_pos = (current_pos[0] + direction[0],
                                current_pos[1] + direction[1])
                    if self.canMove(next_pos): # Если ход возможен
                        # Делаем ход
                        self.doMove(current_pos, next_pos)
                        move = (current_pos, next_pos)
                        # Создаём дочерний узел дерева решений
                        child = Tree("sheep", move, 0)
                        # Делаем рекурсивный вызов
                        self.min_max(child, "sheep", 
                                depth + 1, alpha, beta)
                        result = child.score
                        # Добавляем дочерний узел в дерево
                        tree.addChild(child)
                        # Отменяем ход
                        self.doMove(next_pos, current_pos)

                        if not best_move or result > best_score:
                            # Ищем лучший ход
                            best_move = (current_pos, next_pos)
                            best_score = result
                        
                        # Корректируем значения альфы 
                        alpha = max(alpha, result)

                        # Альфа-бета отсечение
                        if beta <= alpha:
                            break

        if not best_move:
            # Не нашли лучший ход
            # Используем эвристическую оценку
            score = self.heuristic(sheep)
            tree.score = score
            return tree

        if depth == 0:
            # Если глубина 0
            # Компьютер делает ход
            if type == "sheep":
                # Ходит овца
                (prev_pos, next_pos) = best_move
                self.highlightFigure(self.current, Qt.gray)
                # Делаем ход
                self.current.setCell(next_pos[0], next_pos[1])
                # Передаём ход игроку
                self.wolfs_step()
            else:
                # Ходит волк
                (prev_pos, next_pos) = best_move
                current = None
                for wolf in self.wolfs:
                    # Находим фигуру волка, который будет ходить
                    if (wolf.row == prev_pos[0] and 
                        wolf.col == prev_pos[1]):
                        current = wolf
                        break
                # Делаем ход
                current.setCell(next_pos[0], next_pos[1])
                # Передаём ход игроку
                self.sheep_step()

        tree.score = best_score # Сохраняем лучшую оценку
        return tree             # Возвращаем результат


    def highlightCells(self, cells, color):
        for cell in cells:
            self.cells[cell[0]][cell[1]].setBrush(color)


    def isOutOfBorder(self, row, col):
        if row < 0 or row >= N or col < 0 or col >= N:
            return True
        return False

    def getPossibleMoves(self, figure):
        # Получаем список возможных ходов
        moves = [(figure.row + e[0], figure.col + e[1]) 
            for e in figure.direction]
        moves = [x for x in moves if not self.isOutOfBorder(x[0], x[1])]
        
        filled = [(x.row, x.col) for x in self.figures]

        moves = [x for x in moves if not x in filled]

        return moves

    def highlightFigure(self, figure, color):
        # Подсветка возможных ходов
        if figure:
            moves = self.getPossibleMoves(figure)
            self.highlightCells(moves, color)
   
    def checkVictory(self):
        # Проверка условий победы
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
        # Ход овцы
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
        # Ход волков
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
        # Обработка клика
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
