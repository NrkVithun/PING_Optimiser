import random
import math
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPainterPath
from PyQt5.QtWidgets import QWidget

class CherryBlossom:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.angle = random.uniform(0, 360)
        self.speed = random.uniform(1, 3)
        self.oscillation = random.uniform(-2, 2)
        self.alpha = 255
        self.is_packet = False
        self.packet_progress = 0
        self.initial_pos = QPointF(pos)

    def update(self, optimized):
        if not self.is_packet:
            self.pos.setY(self.pos.y() + self.speed)
            self.pos.setX(self.pos.x() + math.sin(self.pos.y() * 0.1) * self.oscillation)
            self.angle += 2
            
            if optimized and random.random() < 0.02:  # 2% chance to transform
                self.is_packet = True
                self.initial_pos = QPointF(self.pos)
        else:
            # Packet movement
            self.packet_progress += 5 if optimized else 2
            angle = math.radians(self.packet_progress)
            radius = 100
            self.pos = QPointF(
                self.initial_pos.x() + math.cos(angle) * radius,
                self.initial_pos.y() + math.sin(angle) * radius
            )

class CherryBlossomAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make widget transparent to mouse events
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove window frame
        self.setAttribute(Qt.WA_TranslucentBackground)  # Enable translucent background
        
        self.petals = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
        self.is_optimized = False
        self.optimization_progress = 0
        self.target_petal_count = 20
        
        # Create initial petals
        self.create_petals(20)

    def create_petals(self, count):
        current_count = len(self.petals)
        if count > current_count:
            # Add more petals
            for _ in range(count - current_count):
                pos = QPointF(
                    random.uniform(0, self.width()),
                    random.uniform(-50, self.height())
                )
                size = random.uniform(5, 15)
                self.petals.append(CherryBlossom(pos, size))
        else:
            # Remove excess petals
            self.petals = self.petals[:count]

    def set_optimized(self, optimized):
        self.is_optimized = optimized
        # Adjust petal count based on optimization state
        self.target_petal_count = 50 if optimized else 20
        if optimized:
            self.optimization_progress = min(100, self.optimization_progress + 5)
        else:
            self.optimization_progress = max(0, self.optimization_progress - 5)

    def update_animation(self):
        # Update petal count gradually
        current_count = len(self.petals)
        if current_count < self.target_petal_count:
            self.create_petals(current_count + 1)
        elif current_count > self.target_petal_count:
            self.petals.pop()

        # Update existing petals
        for petal in self.petals[:]:
            petal.update(self.is_optimized)
            
            # Remove petals that are out of bounds
            if petal.pos.y() > self.height() + 50:
                self.petals.remove(petal)
                # Create new petal at top
                pos = QPointF(
                    random.uniform(0, self.width()),
                    -50
                )
                size = random.uniform(5, 15)
                self.petals.append(CherryBlossom(pos, size))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for petal in self.petals:
            if not petal.is_packet:
                self.draw_petal(painter, petal)
            else:
                self.draw_packet(painter, petal)

    def draw_petal(self, painter, petal):
        painter.save()
        painter.translate(petal.pos)
        painter.rotate(petal.angle)

        path = QPainterPath()
        path.moveTo(0, -petal.size/2)
        path.cubicTo(
            petal.size/2, -petal.size/2,
            petal.size/2, petal.size/2,
            0, petal.size/2
        )
        path.cubicTo(
            -petal.size/2, petal.size/2,
            -petal.size/2, -petal.size/2,
            0, -petal.size/2
        )

        color = QColor(255, 192, 203, 150)  # Semi-transparent pink
        painter.fillPath(path, color)
        painter.restore()

    def draw_packet(self, painter, petal):
        painter.save()
        painter.translate(petal.pos)
        
        # Draw data packet
        color = QColor(0, 255, 255, 150)  # Semi-transparent cyan
        painter.fillRect(-petal.size/2, -petal.size/2, petal.size, petal.size, color)
        
        # Add some details to make it look like a data packet
        painter.setPen(QColor(0, 200, 200, 150))
        painter.drawLine(-petal.size/2, 0, petal.size/2, 0)
        painter.drawLine(0, -petal.size/2, 0, petal.size/2)
        
        painter.restore()
