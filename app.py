import streamlit as st
import numpy as np
import math
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="Pixel Crash Simulator",
    page_icon="💥",
    layout="wide"
)

# ==================== CÁC LỚP CƠ BẢN ====================

@dataclass
class Vec2:
    x: float
    y: float
    
    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vec2(self.x * scalar, self.y * scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vec2(self.x / mag, self.y / mag)
        return Vec2(0, 0)
    
    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class PixelParticle:
    """Pixel vỡ ra khi va chạm"""
    def __init__(self, position: Vec2, color: Tuple[int, int, int], size: int = 3):
        self.position = position
        self.velocity = Vec2(random.uniform(-5, 5), random.uniform(-5, 5))
        self.color = color
        self.size = size
        self.life = 1.0
        self.gravity = Vec2(0, 0.5)
        self.friction = 0.98
        
    def update(self):
        self.velocity = self.velocity + self.gravity
        self.velocity = Vec2(self.velocity.x * self.friction, self.velocity.y * self.friction)
        self.position = self.position + self.velocity
        self.life -= 0.02
        self.size = max(1, self.size * 0.95)
        
    def is_alive(self):
        return self.life > 0

class Car:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], is_player: bool = False):
        self.position = Vec2(x, y)
        self.velocity = Vec2(0, 0)
        self.acceleration = Vec2(0, 0)
        self.angle = 0
        self.color = color
        self.width = 30 if is_player else 25
        self.height = 50 if is_player else 45
        self.max_speed = 8 if is_player else random.uniform(3, 6)
        self.acceleration_rate = 0.2 if is_player else 0.1
        self.braking_rate = 0.3
        self.steering_rate = 0.15 if is_player else 0.08
        self.is_player = is_player
        self.damage = 0
        self.health = 100
        self.crash_particles = []
        self.crash_cooldown = 0
        self.trail_particles = []
        self.last_trail_time = 0
        
        if not is_player:
            self.ai_target = Vec2(random.uniform(0, 2000), random.uniform(0, 2000))
            self.ai_change_time = random.uniform(2, 5)
            self.ai_timer = 0
        
    def update(self, dt: float, obstacles: List['Obstacle'], cars: List['Car']):
        if self.is_player:
            self.update_player(dt)
        else:
            self.update_ai(dt)
            
        # Cập nhật vị trí
        self.velocity = self.velocity + self.acceleration
        self.velocity = Vec2(
            max(-self.max_speed, min(self.max_speed, self.velocity.x)),
            max(-self.max_speed, min(self.max_speed, self.velocity.y))
        )
        self.position = self.position + self.velocity
        
        # Giảm tốc độ tự nhiên
        self.velocity = Vec2(self.velocity.x * 0.98, self.velocity.y * 0.98)
        self.acceleration = Vec2(0, 0)
        
        # Cập nhật particles va chạm
        for particle in self.crash_particles[:]:
            particle.update()
            if not particle.is_alive():
                self.crash_particles.remove(particle)
                
        # Tạo vết lốp
        current_time = time.time()
        speed = self.velocity.magnitude()
        if speed > 2 and current_time - self.last_trail_time > 0.1:
            trail_pos = Vec2(
                self.position.x - math.cos(math.radians(self.angle)) * self.height/2,
                self.position.y - math.sin(math.radians(self.angle)) * self.height/2
            )
            self.trail_particles.append(PixelParticle(
                trail_pos,
                (100, 100, 100),
                size=random.randint(2, 4)
            ))
            self.last_trail_time = current_time
            
        # Giới hạn số lượng trail particles
        if len(self.trail_particles) > 50:
            self.trail_particles = self.trail_particles[-50:]
            
        # Cập nhật trail particles
        for particle in self.trail_particles:
            particle.update()
            particle.life -= 0.01
            
        self.trail_particles = [p for p in self.trail_particles if p.is_alive()]
        
        # Giảm crash cooldown
        if self.crash_cooldown > 0:
            self.crash_cooldown -= dt
            
    def update_player(self, dt: float):
        # Điều khiển từ người chơi
        keys = st.session_state.keys_pressed
        
        # Tăng tốc
        if keys.get('up', False):
            rad = math.radians(self.angle)
            self.acceleration = Vec2(
                math.cos(rad) * self.acceleration_rate,
                math.sin(rad) * self.acceleration_rate
            )
            
        # Phanh
        if keys.get('down', False):
            self.velocity = Vec2(self.velocity.x * 0.9, self.velocity.y * 0.9)
            
        # Lái trái
        if keys.get('left', False):
            self.angle -= 3
            
        # Lái phải
        if keys.get('right', False):
            self.angle += 3
            
        # Phanh tay
        if keys.get('space', False):
            self.velocity = Vec2(self.velocity.x * 0.7, self.velocity.y * 0.7)
            
    def update_ai(self, dt: float):
        self.ai_timer += dt
        
        if self.ai_timer >= self.ai_change_time:
            self.ai_target = Vec2(
                random.uniform(0, 2000),
                random.uniform(0, 2000)
            )
            self.ai_timer = 0
            
        # Di chuyển về phía target
        direction = Vec2(
            self.ai_target.x - self.position.x,
            self.ai_target.y - self.position.y
        )
        
        if direction.magnitude() > 10:
            direction = direction.normalize()
            self.acceleration = Vec2(
                direction.x * self.acceleration_rate,
                direction.y * self.acceleration_rate
            )
            
            # Cập nhật góc
            target_angle = math.degrees(math.atan2(direction.y, direction.x))
            angle_diff = (target_angle - self.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            self.angle += angle_diff * self.steering_rate * dt * 60
            
    def apply_crash(self, force: float, other_pos: Vec2):
        if self.crash_cooldown > 0:
            return
            
        self.crash_cooldown = 10
        
        # Giảm máu
        self.health -= force * 2
        self.damage += force * 2
        
        # Tạo particles pixel vỡ ra
        num_particles = int(force * 5)
        for _ in range(num_particles):
            particle_color = (
                min(255, self.color[0] + random.randint(-50, 50)),
                min(255, self.color[1] + random.randint(-50, 50)),
                min(255, self.color[2] + random.randint(-50, 50))
            )
            
            # Vị trí va chạm
            crash_pos = Vec2(
                (self.position.x + other_pos.x) / 2,
                (self.position.y + other_pos.y) / 2
            )
            
            self.crash_particles.append(PixelParticle(
                crash_pos,
                particle_color,
                size=random.randint(2, 6)
            ))
            
        # Đẩy xe ra
        direction = Vec2(
            self.position.x - other_pos.x,
            self.position.y - other_pos.y
        ).normalize()
        self.velocity = self.velocity + direction * force
        
    def get_bounding_box(self):
        return {
            'x': self.position.x - self.width/2,
            'y': self.position.y - self.height/2,
            'width': self.width,
            'height': self.height
        }

class Building:
    def __init__(self, x: float, y: float, width: int, height: int, color: Tuple[int, int, int]):
        self.position = Vec2(x, y)
        self.width = width
        self.height = height
        self.color = color
        self.window_color = (200, 200, 255)
        
    def get_bounding_box(self):
        return {
            'x': self.position.x - self.width/2,
            'y': self.position.y - self.height/2,
            'width': self.width,
            'height': self.height
        }

class Tree:
    def __init__(self, x: float, y: float, size: int):
        self.position = Vec2(x, y)
        self.size = size
        self.trunk_color = (101, 67, 33)
        self.leaves_color = (34, 139, 34)
        
    def get_bounding_box(self):
        return {
            'x': self.position.x - self.size/2,
            'y': self.position.y - self.size/2,
            'width': self.size,
            'height': self.size
        }

class TrafficLight:
    def __init__(self, x: float, y: float):
        self.position = Vec2(x, y)
        self.state = random.choice(['red', 'yellow', 'green'])
        self.timer = random.uniform(0, 10)
        self.cycle_time = 10
        
    def update(self, dt: float):
        self.timer += dt
        if self.timer >= self.cycle_time:
            self.timer = 0
            if self.state == 'red':
                self.state = 'green'
            elif self.state == 'green':
                self.state = 'yellow'
            else:
                self.state = 'red'

class Road:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, width: int = 60, lanes: int = 2):
        self.start = Vec2(x1, y1)
        self.end = Vec2(x2, y2)
        self.width = width
        self.lanes = lanes
        self.color = (50, 50, 50)
        self.line_color = (255, 255, 255)
        self.line_dash_length = 20
        self.line_gap = 10

class GameWorld:
    def __init__(self, width: int = 2000, height: int = 2000):
        self.width = width
        self.height = height
        self.roads = []
        self.buildings = []
        self.trees = []
        self.traffic_lights = []
        self.obstacles = []
        
        self.generate_world()
        
    def generate_world(self):
        # Tạo đường chính
        for i in range(0, self.width, 200):
            # Đường ngang
            self.roads.append(Road(0, i, self.width, i, width=80, lanes=3))
            # Đường dọc
            self.roads.append(Road(i, 0, i, self.height, width=80, lanes=3))
            
        # Tạo đường phụ
        for i in range(100, self.width, 150):
            if i % 300 == 0:
                self.roads.append(Road(0, i, self.width, i, width=60, lanes=2))
                self.roads.append(Road(i, 0, i, self.height, width=60, lanes=2))
        
        # Tạo tòa nhà
        building_colors = [
            (200, 150, 150),  # Hồng nhạt
            (150, 200, 150),  # Xanh lá nhạt
            (150, 150, 200),  # Xanh dương nhạt
            (200, 200, 150),  # Vàng nhạt
            (200, 150, 200),  # Tím nhạt
        ]
        
        for _ in range(50):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            
            # Kiểm tra không đặt nhà lên đường
            on_road = False
            for road in self.roads:
                if abs(y - road.start.y) < road.width/2 + 30 and abs(x - road.start.x) < 10:
                    on_road = True
                    break
                if abs(x - road.start.x) < road.width/2 + 30 and abs(y - road.start.y) < 10:
                    on_road = True
                    break
            
            if not on_road:
                width = random.randint(40, 80)
                height = random.randint(60, 120)
                color = random.choice(building_colors)
                self.buildings.append(Building(x, y, width, height, color))
        
        # Tạo cây
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            
            # Không đặt cây lên đường
            on_road = False
            for road in self.roads:
                if abs(y - road.start.y) < road.width/2 + 20:
                    on_road = True
                    break
            
            if not on_road:
                self.trees.append(Tree(x, y, random.randint(20, 40)))
        
        # Tạo đèn giao thông
        for i in range(0, self.width, 200):
            for j in range(0, self.height, 200):
                if random.random() < 0.3:
                    self.traffic_lights.append(TrafficLight(i, j))
        
        # Tạo vật cản
        obstacle_types = [
            {'color': (255, 165, 0), 'size': 15},  # Cọc tiêu
            {'color': (255, 0, 0), 'size': 20},    # Thùng
            {'color': (100, 100, 100), 'size': 25}, # Đá
            {'color': (255, 255, 0), 'size': 10},  # Nón
        ]
        
        for _ in range(30):
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            
            # Kiểm tra trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road.start.y) < road.width/2:
                    on_road = True
                    break
            
            if on_road:
                obstacle = random.choice(obstacle_types)
                self.obstacles.append({
                    'position': Vec2(x, y),
                    'color': obstacle['color'],
                    'size': obstacle['size']
                })

class Game:
    def __init__(self):
        self.world = GameWorld()
        self.player = Car(400, 300, (0, 100, 255), is_player=True)
        self.ai_cars = []
        self.camera_pos = Vec2(self.player.position.x, self.player.position.y)
        self.camera_zoom = 1.5
        self.score = 0
        self.total_crashes = 0
        self.max_damage = 0
        self.game_time = 0
        
        # Tạo AI cars
        self.spawn_ai_cars(15)
        
        # Khởi tạo input
        if 'keys_pressed' not in st.session_state:
            st.session_state.keys_pressed = {
                'up': False,
                'down': False,
                'left': False,
                'right': False,
                'space': False
            }
        
    def spawn_ai_cars(self, count: int):
        ai_colors = [
            (255, 0, 0),     # Đỏ
            (0, 255, 0),     # Xanh lá
            (255, 255, 0),   # Vàng
            (255, 165, 0),   # Cam
            (128, 0, 128),   # Tím
            (0, 255, 255),   # Cyan
            (255, 192, 203), # Hồng
        ]
        
        for _ in range(count):
            # Tìm vị trí trên đường
            road = random.choice(self.world.roads)
            t = random.random()
            x = road.start.x + (road.end.x - road.start.x) * t
            y = road.start.y + (road.end.y - road.start.y) * t
            
            # Thêm offset ngẫu nhiên
            x += random.uniform(-20, 20)
            y += random.uniform(-20, 20)
            
            color = random.choice(ai_colors)
            ai_car = Car(x, y, color, is_player=False)
            self.ai_cars.append(ai_car)
    
    def update(self, dt: float):
        # Cập nhật player
        self.player.update(dt, self.world.obstacles, self.ai_cars)
        
        # Cập nhật AI cars
        for ai_car in self.ai_cars:
            ai_car.update(dt, self.world.obstacles, self.ai_cars)
            
            # Kiểm tra va chạm với player
            if self.check_collision(self.player, ai_car):
                force = self.player.velocity.magnitude() + ai_car.velocity.magnitude()
                self.player.apply_crash(force, ai_car.position)
                ai_car.apply_crash(force, self.player.position)
                self.total_crashes += 1
                self.score += int(force * 10)
                
            # Kiểm tra va chạm giữa các AI
            for other_ai in self.ai_cars:
                if ai_car != other_ai and self.check_collision(ai_car, other_ai):
                    force = ai_car.velocity.magnitude() + other_ai.velocity.magnitude()
                    ai_car.apply_crash(force, other_ai.position)
                    other_ai.apply_crash(force, ai_car.position)
                    self.score += int(force * 5)
        
        # Cập nhật đèn giao thông
        for light in self.world.traffic_lights:
            light.update(dt)
        
        # Cập nhật camera
        self.camera_pos.x += (self.player.position.x - self.camera_pos.x) * 0.1
        self.camera_pos.y += (self.player.position.y - self.camera_pos.y) * 0.1
        
        # Cập nhật thời gian
        self.game_time += dt
        
        # Cập nhật max damage
        self.max_damage = max(self.max_damage, self.player.damage)
        
        # Hồi sinh AI cars bị phá hủy
        for i, ai_car in enumerate(self.ai_cars):
            if ai_car.health <= 0:
                # Tạo hiệu ứng nổ lớn
                for _ in range(30):
                    self.player.crash_particles.append(PixelParticle(
                        ai_car.position,
                        ai_car.color,
                        size=random.randint(3, 8)
                    ))
                
                # Tạo xe mới
                road = random.choice(self.world.roads)
                t = random.random()
                x = road.start.x + (road.end.x - road.start.x) * t
                y = road.start.y + (road.end.y - road.start.y) * t
                
                ai_colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0)]
                self.ai_cars[i] = Car(x, y, random.choice(ai_colors), is_player=False)
                self.score += 100
    
    def check_collision(self, car1: Car, car2: Car) -> bool:
        box1 = car1.get_bounding_box()
        box2 = car2.get_bounding_box()
        
        return (abs(box1['x'] - box2['x']) * 2 < (box1['width'] + box2['width']) and
                abs(box1['y'] - box2['y']) * 2 < (box1['height'] + box2['height']))
    
    def check_collision_with_obstacle(self, car: Car) -> bool:
        for obstacle in self.world.obstacles:
            car_box = car.get_bounding_box()
            obs_x, obs_y = obstacle['position'].x, obstacle['position'].y
            obs_size = obstacle['size']
            
            distance = car.position.distance(obstacle['position'])
            if distance < (max(car.width, car.height) / 2 + obs_size):
                return True
        return False
    
    def draw(self, width: int = 800, height: int = 600):
        # Tạo ảnh mới
        img = Image.new('RGB', (width, height), (135, 206, 235))  # Màu trời
        draw = ImageDraw.Draw(img)
        
        # Tính toán viewport dựa trên camera
        view_left = self.camera_pos.x - width / (2 * self.camera_zoom)
        view_top = self.camera_pos.y - height / (2 * self.camera_zoom)
        view_right = self.camera_pos.x + width / (2 * self.camera_zoom)
        view_bottom = self.camera_pos.y + height / (2 * self.camera_zoom)
        
        def world_to_screen(pos: Vec2):
            return (
                (pos.x - view_left) * self.camera_zoom,
                (pos.y - view_top) * self.camera_zoom
            )
        
        # Vẽ đường
        for road in self.world.roads:
            start_screen = world_to_screen(road.start)
            end_screen = world_to_screen(road.end)
            
            # Vẽ mặt đường
            draw.line([start_screen, end_screen], 
                     fill=road.color, 
                     width=int(road.width * self.camera_zoom))
            
            # Vẽ vạch kẻ đường
            if road.width > 40:
                line_count = road.lanes - 1
                for i in range(1, line_count + 1):
                    offset = (i / (line_count + 1) - 0.5) * road.width * 0.8
                    
                    # Tính vị trí song song
                    dx = road.end.x - road.start.x
                    dy = road.end.y - road.start.y
                    length = math.sqrt(dx*dx + dy*dy)
                    
                    if length > 0:
                        perp = Vec2(-dy, dx).normalize()
                        start_offset = road.start + perp * offset
                        end_offset = road.end + perp * offset
                        
                        start_screen = world_to_screen(start_offset)
                        end_screen = world_to_screen(end_offset)
                        
                        # Vẽ đường đứt đoạn
                        dash_length = road.line_dash_length * self.camera_zoom
                        gap_length = road.line_gap * self.camera_zoom
                        total_length = math.sqrt(
                            (end_screen[0] - start_screen[0])**2 + 
                            (end_screen[1] - start_screen[1])**2
                        )
                        
                        if total_length > 0:
                            dx_screen = (end_screen[0] - start_screen[0]) / total_length
                            dy_screen = (end_screen[1] - start_screen[1]) / total_length
                            
                            current = 0
                            while current < total_length:
                                next_point = current + dash_length
                                if next_point > total_length:
                                    next_point = total_length
                                
                                x1 = start_screen[0] + dx_screen * current
                                y1 = start_screen[1] + dy_screen * current
                                x2 = start_screen[0] + dx_screen * next_point
                                y2 = start_screen[1] + dy_screen * next_point
                                
                                draw.line([(x1, y1), (x2, y2)], 
                                         fill=road.line_color,
                                         width=max(1, int(2 * self.camera_zoom)))
                                
                                current += dash_length + gap_length
        
        # Vẽ nhà cửa
        for building in self.world.buildings:
            screen_pos = world_to_screen(building.position)
            bbox = building.get_bounding_box()
            
            left = (bbox['x'] - view_left) * self.camera_zoom
            top = (bbox['y'] - view_top) * self.camera_zoom
            right = left + building.width * self.camera_zoom
            bottom = top + building.height * self.camera_zoom
            
            # Chỉ vẽ nếu trong màn hình
            if (right > 0 and left < width and bottom > 0 and top < height):
                # Vẽ tòa nhà
                draw.rectangle([left, top, right, bottom], 
                              fill=building.color, 
                              outline=(0, 0, 0))
                
                # Vẽ cửa sổ
                window_size = 8 * self.camera_zoom
                window_gap = 12 * self.camera_zoom
                
                for wx in range(int(left + window_gap), int(right), int(window_gap)):
                    for wy in range(int(top + window_gap), int(bottom), int(window_gap)):
                        if wx < right - window_gap and wy < bottom - window_gap:
                            draw.rectangle([
                                wx, wy, 
                                wx + window_size, 
                                wy + window_size
                            ], fill=building.window_color)
        
        # Vẽ cây
        for tree in self.world.trees:
            screen_pos = world_to_screen(tree.position)
            size = tree.size * self.camera_zoom
            
            if (screen_pos[0] > -size and screen_pos[0] < width + size and
                screen_pos[1] > -size and screen_pos[1] < height + size):
                
                # Vẽ thân cây
                trunk_width = size * 0.3
                trunk_height = size * 0.5
                draw.rectangle([
                    screen_pos[0] - trunk_width/2,
                    screen_pos[1] - trunk_height/2,
                    screen_pos[0] + trunk_width/2,
                    screen_pos[1] + trunk_height/2
                ], fill=tree.trunk_color)
                
                # Vẽ tán lá
                draw.ellipse([
                    screen_pos[0] - size/2,
                    screen_pos[1] - size/2 - trunk_height/2,
                    screen_pos[0] + size/2,
                    screen_pos[1] + size/2 - trunk_height/2
                ], fill=tree.leaves_color)
        
        # Vẽ vật cản
        for obstacle in self.world.obstacles:
            screen_pos = world_to_screen(obstacle['position'])
            size = obstacle['size'] * self.camera_zoom
            
            if (screen_pos[0] > -size and screen_pos[0] < width + size and
                screen_pos[1] > -size and screen_pos[1] < height + size):
                
                shape = random.choice(['circle', 'square', 'triangle'])
                
                if shape == 'circle':
                    draw.ellipse([
                        screen_pos[0] - size/2,
                        screen_pos[1] - size/2,
                        screen_pos[0] + size/2,
                        screen_pos[1] + size/2
                    ], fill=obstacle['color'], outline=(0, 0, 0))
                elif shape == 'square':
                    draw.rectangle([
                        screen_pos[0] - size/2,
                        screen_pos[1] - size/2,
                        screen_pos[0] + size/2,
                        screen_pos[1] + size/2
                    ], fill=obstacle['color'], outline=(0, 0, 0))
                else:  # triangle
                    points = [
                        (screen_pos[0], screen_pos[1] - size/2),
                        (screen_pos[0] + size/2, screen_pos[1] + size/2),
                        (screen_pos[0] - size/2, screen_pos[1] + size/2)
                    ]
                    draw.polygon(points, fill=obstacle['color'], outline=(0, 0, 0))
        
        # Vẽ đèn giao thông
        for light in self.world.traffic_lights:
            screen_pos = world_to_screen(light.position)
            size = 15 * self.camera_zoom
            
            if (screen_pos[0] > -size and screen_pos[0] < width + size and
                screen_pos[1] > -size and screen_pos[1] < height + size):
                
                # Vẽ cột đèn
                draw.rectangle([
                    screen_pos[0] - size/4,
                    screen_pos[1] - size,
                    screen_pos[0] + size/4,
                    screen_pos[1] + size
                ], fill=(50, 50, 50))
                
                # Vẽ đèn
                light_color = {
                    'red': (255, 0, 0),
                    'yellow': (255, 255, 0),
                    'green': (0, 255, 0)
                }[light.state]
                
                draw.ellipse([
                    screen_pos[0] - size/3,
                    screen_pos[1] - size/2,
                    screen_pos[0] + size/3,
                    screen_pos[1] + size/2
                ], fill=light_color)
        
        # Vẽ trail particles của player
        for particle in self.player.trail_particles:
            screen_pos = world_to_screen(particle.position)
            if (screen_pos[0] > 0 and screen_pos[0] < width and
                screen_pos[1] > 0 and screen_pos[1] < height):
                draw.rectangle([
                    screen_pos[0] - particle.size/2,
                    screen_pos[1] - particle.size/2,
                    screen_pos[0] + particle.size/2,
                    screen_pos[1] + particle.size/2
                ], fill=particle.color)
        
        # Vẽ AI cars
        for ai_car in self.ai_cars:
            screen_pos = world_to_screen(ai_car.position)
            car_width = ai_car.width * self.camera_zoom
            car_height = ai_car.height * self.camera_zoom
            
            if (screen_pos[0] > -car_width and screen_pos[0] < width + car_width and
                screen_pos[1] > -car_height and screen_pos[1] < height + car_height):
                
                # Vẽ thân xe
                draw.rectangle([
                    screen_pos[0] - car_width/2,
                    screen_pos[1] - car_height/2,
                    screen_pos[0] + car_width/2,
                    screen_pos[1] + car_height/2
                ], fill=ai_car.color, outline=(0, 0, 0))
                
                # Vẽ kính chắn gió
                windshield_color = (200, 230, 255)
                draw.rectangle([
                    screen_pos[0] - car_width/3,
                    screen_pos[1] - car_height/2,
                    screen_pos[0] + car_width/3,
                    screen_pos[1] - car_height/4
                ], fill=windshield_color)
                
                # Hiển thị damage nếu có
                if ai_car.damage > 30:
                    damage_alpha = min(200, ai_car.damage * 2)
                    damage_color = (255, 0, 0, damage_alpha)
                    
                    # Vẽ vết nứt
                    for _ in range(int(ai_car.damage / 20)):
                        crack_x = screen_pos[0] + random.uniform(-car_width/3, car_width/3)
                        crack_y = screen_pos[1] + random.uniform(-car_height/3, car_height/3)
                        length = random.uniform(3, 8) * self.camera_zoom
                        angle = random.uniform(0, 360)
                        
                        end_x = crack_x + math.cos(math.radians(angle)) * length
                        end_y = crack_y + math.sin(math.radians(angle)) * length
                        
                        draw.line([(crack_x, crack_y), (end_x, end_y)], 
                                 fill=(0, 0, 0), 
                                 width=int(self.camera_zoom))
        
        # Vẽ player car
        screen_pos = world_to_screen(self.player.position)
        car_width = self.player.width * self.camera_zoom
        car_height = self.player.height * self.camera_zoom
        
        # Vẽ thân xe
        draw.rectangle([
            screen_pos[0] - car_width/2,
            screen_pos[1] - car_height/2,
            screen_pos[0] + car_width/2,
            screen_pos[1] + car_height/2
        ], fill=self.player.color, outline=(255, 255, 0), width=2)
        
        # Vẽ kính chắn gió
        windshield_color = (220, 240, 255)
        draw.rectangle([
            screen_pos[0] - car_width/3,
            screen_pos[1] - car_height/2,
            screen_pos[0] + car_width/3,
            screen_pos[1] - car_height/4
        ], fill=windshield_color)
        
        # Vẽ đèn pha
        headlight_color = (255, 255, 200)
        draw.ellipse([
            screen_pos[0] - car_width/2 - 5,
            screen_pos[1] - car_height/4,
            screen_pos[0] - car_width/2 + 5,
            screen_pos[1] + car_height/4
        ], fill=headlight_color)
        draw.ellipse([
            screen_pos[0] + car_width/2 - 5,
            screen_pos[1] - car_height/4,
            screen_pos[0] + car_width/2 + 5,
            screen_pos[1] + car_height/4
        ], fill=headlight_color)
        
        # Vẽ đèn phanh nếu đang phanh
        if st.session_state.keys_pressed.get('down', False) or st.session_state.keys_pressed.get('space', False):
            brake_color = (255, 50, 50)
            draw.rectangle([
                screen_pos[0] - car_width/3,
                screen_pos[1] + car_height/2 - 8,
                screen_pos[0] + car_width/3,
                screen_pos[1] + car_height/2
            ], fill=brake_color)
        
        # Vẽ crash particles
        all_particles = self.player.crash_particles.copy()
        for ai_car in self.ai_cars:
            all_particles.extend(ai_car.crash_particles)
        
        for particle in all_particles:
            screen_pos_p = world_to_screen(particle.position)
            if (screen_pos_p[0] > 0 and screen_pos_p[0] < width and
                screen_pos_p[1] > 0 and screen_pos_p[1] < height):
                
                alpha = int(255 * particle.life)
                color_with_alpha = particle.color + (alpha,)
                
                # Vẽ pixel particle
                draw.rectangle([
                    screen_pos_p[0] - particle.size/2,
                    screen_pos_p[1] - particle.size/2,
                    screen_pos_p[0] + particle.size/2,
                    screen_pos_p[1] + particle.size/2
                ], fill=particle.color)
        
        # Vẽ UI
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Thông tin player
        draw.rectangle([10, 10, 250, 130], fill=(0, 0, 0, 150), outline=(255, 255, 255))
        
        # Health bar
        health_width = 200 * (self.player.health / 100)
        draw.rectangle([20, 20, 20 + health_width, 35], fill=(0, 255, 0))
        draw.rectangle([20, 20, 220, 35], outline=(255, 255, 255))
        draw.text((20, 40), f"HP: {self.player.health:.0f}/100", fill=(255, 255, 255), font=font)
        
        # Damage
        draw.text((20, 60), f"Hư hại: {self.player.damage:.0f}%", fill=(255, 255, 255), font=font)
        
        # Score
        draw.text((20, 80), f"Điểm: {self.score:,}", fill=(255, 255, 255), font=font)
        
        # Game time
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        draw.text((20, 100), f"Thời gian: {minutes:02d}:{seconds:02d}", fill=(255, 255, 255), font=font)
        
        # Tốc độ
        speed = self.player.velocity.magnitude() * 20
        draw.text((20, 120), f"Tốc độ: {speed:.0f} km/h", fill=(255, 255, 255), font=font)
        
        # Thông tin va chạm
        draw.rectangle([width - 260, 10, width - 10, 110], fill=(0, 0, 0, 150), outline=(255, 255, 255))
        draw.text((width - 250, 20), f"Số lần va chạm: {self.total_crashes}", fill=(255, 255, 255), font=font)
        draw.text((width - 250, 40), f"Xe AI: {len(self.ai_cars)}", fill=(255, 255, 255), font=font)
        draw.text((width - 250, 60), f"Lực mạnh nhất: {self.max_damage:.0f}", fill=(255, 255, 255), font=font)
        draw.text((width - 250, 80), f"Camera zoom: {self.camera_zoom:.1f}x", fill=(255, 255, 255), font=font)
        
        # Hướng dẫn
        draw.text((width - 250, height - 80), "ĐIỀU KHIỂN:", fill=(255, 255, 255), font=font)
        draw.text((width - 250, height - 60), "↑↓: Tốc độ | ←→: Lái", fill=(255, 255, 255), font=font)
        draw.text((width - 250, height - 40), "Space: Phanh tay | R: Reset", fill=(255, 255, 255), font=font)
        
        return img

# ==================== GIAO DIỆN STREAMLIT ====================

def main():
    st.title("💥 Pixel Crash Simulator")
    st.markdown("### Game Va Chạm Xe Pixel - Phá Hủy Mọi Thứ!")
    
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = Game()
        st.session_state.last_update = time.time()
        st.session_state.game_running = True
    
    game = st.session_state.game
    
    # Sidebar điều khiển
    with st.sidebar:
        st.header("🎮 Điều Khiển Game")
        
        # Nút bắt đầu/dừng
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Bắt đầu" if not st.session_state.game_running else "⏸️ Dừng", 
                        use_container_width=True):
                st.session_state.game_running = not st.session_state.game_running
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset Game", use_container_width=True):
                st.session_state.game = Game()
                st.session_state.last_update = time.time()
                st.rerun()
        
        st.markdown("---")
        
        # Camera controls
        st.subheader("📷 Camera")
        game.camera_zoom = st.slider("Zoom", 0.5, 3.0, game.camera_zoom, 0.1)
        
        # Game settings
        st.subheader("⚙️ Cài Đặt")
        ai_count = st.slider("Số lượng xe AI", 5, 30, len(game.ai_cars))
        if ai_count != len(game.ai_cars):
            game.ai_cars = game.ai_cars[:ai_count]
            if len(game.ai_cars) < ai_count:
                game.spawn_ai_cars(ai_count - len(game.ai_cars))
        
        damage_multiplier = st.slider("Lực va chạm", 0.5, 3.0, 1.0, 0.1)
        
        st.markdown("---")
        
        # Thống kê
        st.subheader("📊 Thống Kê")
        st.metric("🏆 Điểm số", f"{game.score:,}")
        st.metric("💥 Số lần va chạm", game.total_crashes)
        st.metric("⚠️ Hư hại xe", f"{game.player.damage:.0f}%")
        st.metric("❤️ Sức khỏe", f"{game.player.health:.0f}%")
        
        st.markdown("---")
        
        # Keyboard controls
        st.subheader("⌨️ Điều Khiển Bàn Phím")
        st.markdown("""
        - **↑ Mũi tên lên**: Tăng tốc
        - **↓ Mũi tên xuống**: Phanh
        - **← Mũi tên trái**: Lái trái
        - **→ Mũi tên phải**: Lái phải
        - **Space**: Phanh tay
        - **R**: Reset xe
        - **Z**: Zoom in
        - **X**: Zoom out
        """)
    
    # Main game area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Game canvas
        game_container = st.empty()
        
        # Game controls
        st.markdown("### 🎮 Điều Khiển Trực Tiếp")
        control_col1, control_col2, control_col3, control_col4, control_col5 = st.columns(5)
        
        with control_col1:
            accelerate = st.button("↑ Tăng tốc", use_container_width=True)
            if accelerate:
                st.session_state.keys_pressed['up'] = True
            else:
                st.session_state.keys_pressed['up'] = False
        
        with control_col2:
            brake = st.button("↓ Phanh", use_container_width=True)
            if brake:
                st.session_state.keys_pressed['down'] = True
            else:
                st.session_state.keys_pressed['down'] = False
        
        with control_col3:
            left = st.button("← Trái", use_container_width=True)
            if left:
                st.session_state.keys_pressed['left'] = True
            else:
                st.session_state.keys_pressed['left'] = False
        
        with control_col4:
            right = st.button("→ Phải", use_container_width=True)
            if right:
                st.session_state.keys_pressed['right'] = True
            else:
                st.session_state.keys_pressed['right'] = False
        
        with control_col5:
            handbrake = st.button("Space Phanh tay", use_container_width=True)
            if handbrake:
                st.session_state.keys_pressed['space'] = True
            else:
                st.session_state.keys_pressed['space'] = False
    
    with col2:
        # Car info
        st.subheader("🚗 Thông Tin Xe")
        st.progress(game.player.health/100, f"Sức khỏe: {game.player.health:.0f}%")
        st.progress(game.player.damage/100, f"Hư hại: {game.player.damage:.0f}%")
        
        speed = game.player.velocity.magnitude() * 20
        st.metric("📊 Tốc độ", f"{speed:.0f} km/h")
        st.metric("🎯 Hướng", f"{game.player.angle:.0f}°")
        
        # Crash force
        if game.total_crashes > 0:
            st.metric("💥 Lực va chạm TB", f"{game.max_damage/game.total_crashes:.1f}")
        
        # Quick actions
        st.subheader("⚡ Hành Động Nhanh")
        if st.button("💥 Va chạm mạnh!", use_container_width=True):
            game.player.velocity = Vec2(15, 0)
            nearest_ai = min(game.ai_cars, key=lambda c: c.position.distance(game.player.position))
            game.player.apply_crash(20, nearest_ai.position)
            nearest_ai.apply_crash(20, game.player.position)
        
        if st.button("🔄 Đặt lại vị trí", use_container_width=True):
            game.player.position = Vec2(400, 300)
            game.player.velocity = Vec2(0, 0)
            game.player.health = 100
    
    # Game loop
    if st.session_state.game_running:
        current_time = time.time()
        dt = (current_time - st.session_state.last_update)
        
        if dt > 0.016:  # ~60 FPS
            game.update(dt * damage_multiplier)
            
            # Vẽ game
            game_img = game.draw(800, 600)
            
            # Hiển thị
            game_container.image(game_img, use_column_width=True)
            
            st.session_state.last_update = current_time
            st.rerun()
    else:
        # Chỉ vẽ một frame tĩnh
        game_img = game.draw(800, 600)
        game_container.image(game_img, use_column_width=True)
    
    # Game description
    st.markdown("---")
    with st.expander("🎯 Mục Tiêu & Cách Chơi", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎮 CÁCH CHƠI:
            1. **Điều khiển xe** bằng nút hoặc bàn phím
            2. **Va chạm với xe AI** để gây sát thương
            3. **Nhận điểm** mỗi khi va chạm
            4. **Tránh hư hại quá nhiều** - xe sẽ nổ!
            5. **Phá hủy càng nhiều xe AI càng tốt**
            
            ### 💥 HIỆU ỨNG VA CHẠM:
            - **Pixel vỡ ra** khi va chạm
            - **Màu sắc thay đổi** theo lực va chạm
            - **Vết nứt** trên xe bị hư hại
            - **Vết lốp** khi xe di chuyển nhanh
            """)
        
        with col2:
            st.markdown("""
            ### 🏙️ THẾ GIỚI GAME:
            - **Bản đồ rộng 2000x2000 pixel**
            - **Hệ thống đường** với vạch kẻ
            - **Tòa nhà** và cơ sở hạ tầng
            - **Cây cối** và vật cản
            - **Đèn giao thông** hoạt động
            - **Camera follow** với zoom linh hoạt
            
            ### 🚗 XE AI THÔNG MINH:
            - **Di chuyển tự động** trên đường
            - **Tránh vật cản** cơ bản
            - **Hồi sinh** khi bị phá hủy
            - **Màu sắc đa dạng**
            """)
    
    # Keyboard event handling
    st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowUp') {
            window.parent.postMessage({type: 'keydown', key: 'up'}, '*');
        } else if (e.key === 'ArrowDown') {
            window.parent.postMessage({type: 'keydown', key: 'down'}, '*');
        } else if (e.key === 'ArrowLeft') {
            window.parent.postMessage({type: 'keydown', key: 'left'}, '*');
        } else if (e.key === 'ArrowRight') {
            window.parent.postMessage({type: 'keydown', key: 'right'}, '*');
        } else if (e.key === ' ') {
            window.parent.postMessage({type: 'keydown', key: 'space'}, '*');
        } else if (e.key === 'r' || e.key === 'R') {
            window.parent.postMessage({type: 'keydown', key: 'reset'}, '*');
        } else if (e.key === 'z' || e.key === 'Z') {
            window.parent.postMessage({type: 'keydown', key: 'zoomin'}, '*');
        } else if (e.key === 'x' || e.key === 'X') {
            window.parent.postMessage({type: 'keydown', key: 'zoomout'}, '*');
        }
    });
    
    document.addEventListener('keyup', function(e) {
        if (e.key === 'ArrowUp') {
            window.parent.postMessage({type: 'keyup', key: 'up'}, '*');
        } else if (e.key === 'ArrowDown') {
            window.parent.postMessage({type: 'keyup', key: 'down'}, '*');
        } else if (e.key === 'ArrowLeft') {
            window.parent.postMessage({type: 'keyup', key: 'left'}, '*');
        } else if (e.key === 'ArrowRight') {
            window.parent.postMessage({type: 'keyup', key: 'right'}, '*');
        } else if (e.key === ' ') {
            window.parent.postMessage({type: 'keyup', key: 'space'}, '*');
        }
    });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
