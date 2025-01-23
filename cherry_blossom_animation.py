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
        self.speed = random.uniform(1, 2)  # Slightly faster for better movement
        self.oscillation = random.uniform(-1.5, 1.5)
        self.alpha = random.randint(150, 200)  # Randomize transparency
        self.wave_offset = random.uniform(0, 2 * math.pi)
        self.drift_direction = random.choice([-1, 1])  # Random left/right drift

    def update(self):
        # Vertical movement
        self.pos.setY(self.pos.y() + self.speed)
        
        # Horizontal movement with drift
        drift = math.sin(self.wave_offset + self.pos.y() * 0.05) * 0.8
        self.pos.setX(self.pos.x() + (drift * self.drift_direction))
        
        # Gentle rotation
        self.angle += 1

class CherryBlossomAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.lower()
        
        self.petals = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(25)  # Adjusted for better performance
        self.target_petal_count = 25  # Increased petal count
        
        # Create initial petals
        self.create_petals(self.target_petal_count)

    def create_petals(self, count):
        current_count = len(self.petals)
        if count > current_count:
            for _ in range(count - current_count):
                # Spread petals across the top of the screen
                spawn_zone = random.randint(0, 3)  # 0: left, 1: center-left, 2: center-right, 3: right
                if spawn_zone == 0:  # Left side
                    x = random.uniform(0, self.width() * 0.25)
                elif spawn_zone == 1:  # Center-left
                    x = random.uniform(self.width() * 0.25, self.width() * 0.5)
                elif spawn_zone == 2:  # Center-right
                    x = random.uniform(self.width() * 0.5, self.width() * 0.75)
                else:  # Right side
                    x = random.uniform(self.width() * 0.75, self.width())
                
                pos = QPointF(
                    x,
                    random.uniform(-50, self.height() * 0.2)  # Spawn in top fifth
                )
                size = random.uniform(8, 12)
                self.petals.append(CherryBlossom(pos, size))
        else:
            self.petals = self.petals[:count]

    def update_animation(self):
        # Update existing petals
        for petal in self.petals[:]:
            petal.update()
            
            # Remove petals that are out of bounds
            if (petal.pos.y() > self.height() + 50 or 
                petal.pos.x() < -50 or 
                petal.pos.x() > self.width() + 50):
                self.petals.remove(petal)
                # Create new petal at random position at top
                spawn_zone = random.randint(0, 3)
                if spawn_zone == 0:  # Left side
                    x = random.uniform(0, self.width() * 0.25)
                elif spawn_zone == 1:  # Center-left
                    x = random.uniform(self.width() * 0.25, self.width() * 0.5)
                elif spawn_zone == 2:  # Center-right
                    x = random.uniform(self.width() * 0.5, self.width() * 0.75)
                else:  # Right side
                    x = random.uniform(self.width() * 0.75, self.width())
                
                pos = QPointF(x, random.uniform(-50, 0))
                size = random.uniform(8, 12)
                self.petals.append(CherryBlossom(pos, size))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for petal in self.petals:
            self.draw_petal(painter, petal)

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

        # Use only pink colors with varying transparency
        color = QColor(255, 182, 193, petal.alpha)  # Light pink
        painter.fillPath(path, color)
        painter.restore()
