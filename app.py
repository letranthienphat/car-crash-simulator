import streamlit as st
import math
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import urllib.parse

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="Pixel Crash Simulator",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"  # Ẩn sidebar mặc định
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

# ==================== HỆ THỐNG GAME ====================

class Game:
    def __init__(self):
        self.width = 2000
        self.height = 2000
        self.player = {
            'x': 400,
            'y': 300,
            'vx': 0,
            'vy': 0,
            'angle': 0,
            'health': 100,
            'damage': 0,
            'color': '#0066CC',
            'width': 30,
            'height': 50,
            'max_speed': 8,
            'acceleration': 0.2,
            'braking': 0.3,
            'score_multiplier': 1.0
        }
        
        self.ai_cars = []
        self.particles = []
        self.buildings = []
        self.trees = []
        self.obstacles = []
        self.roads = []
        self.explosions = []
        
        self.score = 0
        self.total_crashes = 0
        self.game_time = 0
        self.camera_x = self.player['x']
        self.camera_y = self.player['y']
        self.camera_zoom = 1.5
        self.last_update = time.time()
        self.game_running = True
        
        # Khởi tạo thế giới
        self.generate_world()
        self.spawn_ai_cars(20)
        
        # Khởi tạo input
        if 'keys_pressed' not in st.session_state:
            st.session_state.keys_pressed = {
                'up': False, 'down': False, 'left': False, 'right': False, 'space': False
            }
        
        # Phát hiện thiết bị
        if 'is_mobile' not in st.session_state:
            st.session_state.is_mobile = False
    
    def generate_world(self):
        # Tạo đường chính
        for i in range(0, self.width, 200):
            self.roads.append({
                'x1': 0, 'y1': i, 'x2': self.width, 'y2': i,
                'width': 80, 'lanes': 3, 'color': '#333333', 'type': 'highway'
            })
            self.roads.append({
                'x1': i, 'y1': 0, 'x2': i, 'y2': self.height,
                'width': 80, 'lanes': 3, 'color': '#333333', 'type': 'highway'
            })
        
        # Tạo đường phụ
        for i in range(100, self.width - 100, 150):
            self.roads.append({
                'x1': 0, 'y1': i, 'x2': self.width, 'y2': i,
                'width': 50, 'lanes': 2, 'color': '#555555', 'type': 'street'
            })
            self.roads.append({
                'x1': i, 'y1': 0, 'x2': i, 'y2': self.height,
                'width': 50, 'lanes': 2, 'color': '#555555', 'type': 'street'
            })
        
        # Tạo nhà cửa
        building_styles = [
            {'color': '#C89664', 'height': 3, 'type': 'house'},
            {'color': '#A0522D', 'height': 5, 'type': 'apartment'},
            {'color': '#8B4513', 'height': 4, 'type': 'office'},
            {'color': '#D2691E', 'height': 2, 'type': 'shop'},
            {'color': '#CD853F', 'height': 3, 'type': 'factory'}
        ]
        
        for _ in range(80):
            style = random.choice(building_styles)
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            
            # Kiểm tra không trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road['y1']) < road['width']/2 + 40:
                    on_road = True
                    break
            
            if not on_road:
                self.buildings.append({
                    'x': x, 'y': y,
                    'width': random.randint(40, 80),
                    'height': random.randint(60, 120),
                    'color': style['color'],
                    'window_color': '#C8E0FF',
                    'floors': style['height'],
                    'type': style['type']
                })
        
        # Tạo cây
        tree_types = [
            {'color': '#228B22', 'size': 35, 'type': 'oak'},
            {'color': '#32CD32', 'size': 25, 'type': 'pine'},
            {'color': '#006400', 'size': 30, 'type': 'maple'},
            {'color': '#90EE90', 'size': 20, 'type': 'bush'}
        ]
        
        for _ in range(150):
            tree = random.choice(tree_types)
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            
            # Không trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road['y1']) < road['width']/2 + 25:
                    on_road = True
                    break
            
            if not on_road:
                self.trees.append({
                    'x': x, 'y': y,
                    'size': tree['size'],
                    'trunk_color': '#654321',
                    'leaves_color': tree['color'],
                    'type': tree['type']
                })
        
        # Tạo vật cản
        obstacle_types = [
            {'color': '#FFA500', 'size': 15, 'type': 'cone', 'damage': 10},
            {'color': '#FF0000', 'size': 20, 'type': 'barrel', 'damage': 20},
            {'color': '#666666', 'size': 25, 'type': 'rock', 'damage': 30},
            {'color': '#FFD700', 'size': 18, 'type': 'construction', 'damage': 15}
        ]
        
        for _ in range(40):
            obstacle = random.choice(obstacle_types)
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            
            # Chỉ trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road['y1']) < road['width']/2:
                    on_road = True
                    break
            
            if on_road:
                self.obstacles.append({
                    'x': x, 'y': y,
                    'color': obstacle['color'],
                    'size': obstacle['size'],
                    'type': obstacle['type'],
                    'damage': obstacle['damage']
                })
    
    def spawn_ai_cars(self, count: int):
        ai_colors = [
            '#FF0000', '#00FF00', '#FFFF00', '#FFA500',
            '#800080', '#00FFFF', '#FF1493', '#1E90FF',
            '#FF4500', '#32CD32', '#8A2BE2', '#DC143C'
        ]
        
        behaviors = ['normal', 'aggressive', 'slow', 'erratic']
        
        for i in range(count):
            road = random.choice(self.roads)
            t = random.random()
            x = road['x1'] + (road['x2'] - road['x1']) * t
            y = road['y1'] + (road['y2'] - road['y1']) * t
            
            behavior = random.choice(behaviors)
            if behavior == 'aggressive':
                max_speed = random.uniform(6, 9)
                acceleration = 0.25
            elif behavior == 'slow':
                max_speed = random.uniform(2, 4)
                acceleration = 0.08
            elif behavior == 'erratic':
                max_speed = random.uniform(4, 7)
                acceleration = 0.15
            else:
                max_speed = random.uniform(3, 6)
                acceleration = 0.1
            
            self.ai_cars.append({
                'id': i,
                'x': x, 'y': y,
                'vx': 0, 'vy': 0,
                'angle': random.uniform(0, 360),
                'target_x': random.uniform(0, self.width),
                'target_y': random.uniform(0, self.height),
                'health': 100,
                'damage': 0,
                'color': random.choice(ai_colors),
                'width': random.randint(22, 28),
                'height': random.randint(40, 50),
                'max_speed': max_speed,
                'acceleration': acceleration,
                'ai_timer': random.uniform(0, 5),
                'ai_change_time': random.uniform(2, 6),
                'behavior': behavior,
                'score_value': 50 if behavior == 'aggressive' else 30
            })
    
    def update(self, dt: float):
        if not self.game_running:
            return
            
        # Cập nhật player
        self.update_player(dt)
        
        # Cập nhật AI cars
        self.update_ai_cars(dt)
        
        # Cập nhật particles và explosions
        self.update_particles(dt)
        self.update_explosions(dt)
        
        # Cập nhật camera
        self.camera_x += (self.player['x'] - self.camera_x) * 0.1
        self.camera_y += (self.player['y'] - self.camera_y) * 0.1
        
        # Cập nhật thời gian
        self.game_time += dt
        
        # Kiểm tra va chạm
        self.check_collisions()
        
        # Hồi sinh AI cars bị phá hủy
        self.respawn_ai_cars()
        
        # Kiểm tra game over
        if self.player['health'] <= 0:
            self.game_running = False
    
    def update_player(self, dt: float):
        keys = st.session_state.keys_pressed
        
        # Tăng tốc
        if keys.get('up', False) or keys.get('w', False):
            rad = math.radians(self.player['angle'])
            self.player['vx'] += math.cos(rad) * self.player['acceleration']
            self.player['vy'] += math.sin(rad) * self.player['acceleration']
        
        # Phanh
        if keys.get('down', False) or keys.get('s', False):
            self.player['vx'] *= 0.9
            self.player['vy'] *= 0.9
        
        # Lái trái
        if keys.get('left', False) or keys.get('a', False):
            self.player['angle'] -= 3
        
        # Lái phải
        if keys.get('right', False) or keys.get('d', False):
            self.player['angle'] += 3
        
        # Phanh tay
        if keys.get('space', False):
            self.player['vx'] *= 0.7
            self.player['vy'] *= 0.7
            # Tạo vết lốp khi phanh
            if random.random() < 0.5:
                self.create_particle(
                    self.player['x'], self.player['y'],
                    '#333333',
                    random.uniform(-1, 1),
                    random.uniform(-1, 1),
                    random.randint(2, 4),
                    particle_type='smoke'
                )
        
        # Giới hạn tốc độ
        speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
        if speed > self.player['max_speed']:
            scale = self.player['max_speed'] / speed
            self.player['vx'] *= scale
            self.player['vy'] *= scale
        
        # Cập nhật vị trí
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Giữ xe trong bản đồ
        self.player['x'] = max(50, min(self.width - 50, self.player['x']))
        self.player['y'] = max(50, min(self.height - 50, self.player['y']))
        
        # Ma sát
        self.player['vx'] *= 0.98
        self.player['vy'] *= 0.98
        
        # Tạo vết lốp khi di chuyển nhanh
        if speed > 2 and random.random() < 0.3:
            self.create_particle(
                self.player['x'] - math.cos(math.radians(self.player['angle'])) * 25,
                self.player['y'] - math.sin(math.radians(self.player['angle'])) * 25,
                '#666666',
                self.player['vx'] * 0.1,
                self.player['vy'] * 0.1,
                random.randint(2, 4)
            )
    
    def update_ai_cars(self, dt: float):
        for ai in self.ai_cars:
            # Cập nhật timer
            ai['ai_timer'] += dt
            
            # Đổi target mới
            if ai['ai_timer'] >= ai['ai_change_time']:
                ai['target_x'] = random.uniform(0, self.width)
                ai['target_y'] = random.uniform(0, self.height)
                ai['ai_timer'] = 0
                
                # Hành vi erratic: thay đổi hành vi
                if ai['behavior'] == 'erratic' and random.random() < 0.3:
                    ai['acceleration'] = random.uniform(0.05, 0.2)
                    ai['max_speed'] = random.uniform(3, 8)
            
            # Tính toán hướng
            dx = ai['target_x'] - ai['x']
            dy = ai['target_y'] - ai['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 20:  # Chỉ di chuyển nếu xa target
                # Di chuyển về target
                ai['vx'] += (dx / dist) * ai['acceleration']
                ai['vy'] += (dy / dist) * ai['acceleration']
                
                # Cập nhật góc
                target_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = (target_angle - ai['angle']) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                ai['angle'] += angle_diff * 0.1
            else:
                # Giảm tốc khi đến gần target
                ai['vx'] *= 0.95
                ai['vy'] *= 0.95
            
            # Giới hạn tốc độ
            speed = math.sqrt(ai['vx']**2 + ai['vy']**2)
            if speed > ai['max_speed']:
                scale = ai['max_speed'] / speed
                ai['vx'] *= scale
                ai['vy'] *= scale
            
            # Cập nhật vị trí
            ai['x'] += ai['vx']
            ai['y'] += ai['vy']
            
            # Giữ xe trong bản đồ
            ai['x'] = max(50, min(self.width - 50, ai['x']))
            ai['y'] = max(50, min(self.height - 50, ai['y']))
            
            # Ma sát
            ai['vx'] *= 0.98
            ai['vy'] *= 0.98
            
            # Tránh va chạm với các AI khác (đơn giản)
            for other in self.ai_cars:
                if other['id'] != ai['id']:
                    dist = math.sqrt((ai['x'] - other['x'])**2 + (ai['y'] - other['y'])**2)
                    if dist < 60:
                        dx = ai['x'] - other['x']
                        dy = ai['y'] - other['y']
                        if dist > 0:
                            ai['vx'] += (dx / dist) * 0.2
                            ai['vy'] += (dy / dist) * 0.2
    
    def create_particle(self, x: float, y: float, color: str, vx: float, vy: float, size: int, particle_type: str = 'normal'):
        self.particles.append({
            'x': x, 'y': y,
            'vx': vx, 'vy': vy,
            'color': color,
            'size': size,
            'life': 1.0,
            'gravity': 0.3 if particle_type == 'normal' else -0.1,
            'friction': 0.98,
            'type': particle_type,
            'rotation': random.uniform(0, 360),
            'rotation_speed': random.uniform(-5, 5)
        })
    
    def create_explosion(self, x: float, y: float, intensity: float = 1.0, color: str = '#FF4500'):
        self.explosions.append({
            'x': x, 'y': y,
            'radius': 10,
            'max_radius': 50 * intensity,
            'life': 1.0,
            'color': color,
            'intensity': intensity
        })
        
        # Tạo particles cho vụ nổ
        num_particles = int(30 * intensity)
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8) * intensity
            self.create_particle(
                x, y,
                random.choice([color, '#FFA500', '#FFFF00']),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.randint(3, 8),
                particle_type='fire'
            )
    
    def update_particles(self, dt: float):
        for particle in self.particles[:]:
            # Cập nhật vật lý
            particle['vy'] += particle['gravity']
            particle['vx'] *= particle['friction']
            particle['vy'] *= particle['friction']
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.03 if particle['type'] == 'fire' else 0.015
            particle['size'] = max(0.5, particle['size'] * 0.95)
            particle['rotation'] += particle['rotation_speed']
            
            # Xóa particle đã chết
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def update_explosions(self, dt: float):
        for explosion in self.explosions[:]:
            explosion['radius'] += (explosion['max_radius'] - explosion['radius']) * 0.3
            explosion['life'] -= 0.05
            if explosion['life'] <= 0:
                self.explosions.remove(explosion)
    
    def check_collisions(self):
        # Kiểm tra va chạm giữa player và AI
        for ai in self.ai_cars:
            dx = self.player['x'] - ai['x']
            dy = self.player['y'] - ai['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            collision_distance = (self.player['width'] + ai['width']) / 2
            
            if distance < collision_distance:
                # Tính lực va chạm
                player_speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
                ai_speed = math.sqrt(ai['vx']**2 + ai['vy']**2)
                force = player_speed + ai_speed
                
                if force > 2:  # Chỉ tính va chạm đủ mạnh
                    # Áp dụng damage
                    damage = force * 3
                    self.player['health'] = max(0, self.player['health'] - damage)
                    self.player['damage'] = min(100, self.player['damage'] + damage)
                    ai['health'] = max(0, ai['health'] - damage)
                    ai['damage'] = min(100, ai['damage'] + damage)
                    
                    # Tạo particles
                    crash_x = (self.player['x'] + ai['x']) / 2
                    crash_y = (self.player['y'] + ai['y']) / 2
                    
                    num_particles = int(force * 8)
                    for _ in range(num_particles):
                        # Particle từ player
                        self.create_particle(
                            crash_x, crash_y,
                            self.player['color'],
                            random.uniform(-force, force),
                            random.uniform(-force, force),
                            random.randint(2, 6)
                        )
                        
                        # Particle từ AI
                        self.create_particle(
                            crash_x, crash_y,
                            ai['color'],
                            random.uniform(-force, force),
                            random.uniform(-force, force),
                            random.randint(2, 6)
                        )
                    
                    # Đẩy xe ra
                    if distance > 0:
                        push_force = force * 0.8
                        push_x = dx / distance * push_force
                        push_y = dy / distance * push_force
                        
                        self.player['vx'] += push_x
                        self.player['vy'] += push_y
                        ai['vx'] -= push_x
                        ai['vy'] -= push_y
                    
                    # Cập nhật điểm
                    self.total_crashes += 1
                    score_gain = int(force * 15 * self.player['score_multiplier'])
                    self.score += score_gain
                    
                    # Tạo text effect
                    self.create_text_effect(
                        crash_x, crash_y,
                        f"+{score_gain}",
                        '#FFFF00',
                        size=20 + int(force * 2)
                    )
        
        # Kiểm tra va chạm với vật cản
        for obstacle in self.obstacles:
            dx = self.player['x'] - obstacle['x']
            dy = self.player['y'] - obstacle['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < (self.player['width'] / 2 + obstacle['size']):
                speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
                if speed > 1:
                    # Damage từ vật cản
                    self.player['health'] = max(0, self.player['health'] - obstacle['damage'])
                    self.player['damage'] = min(100, self.player['damage'] + obstacle['damage'])
                    
                    # Tạo particles
                    for _ in range(10):
                        self.create_particle(
                            obstacle['x'], obstacle['y'],
                            obstacle['color'],
                            random.uniform(-5, 5),
                            random.uniform(-5, 5),
                            random.randint(2, 4)
                        )
                    
                    # Đẩy player ra
                    if distance > 0:
                        self.player['vx'] += (dx / distance) * 3
                        self.player['vy'] += (dy / distance) * 3
    
    def create_text_effect(self, x: float, y: float, text: str, color: str, size: int = 20):
        self.particles.append({
            'x': x, 'y': y,
            'vx': random.uniform(-1, 1),
            'vy': -2,
            'color': color,
            'size': size,
            'life': 1.5,
            'gravity': 0.1,
            'friction': 0.95,
            'type': 'text',
            'text': text,
            'rotation': 0,
            'rotation_speed': 0
        })
    
    def respawn_ai_cars(self):
        for i, ai in enumerate(self.ai_cars):
            if ai['health'] <= 0:
                # Tạo hiệu ứng nổ
                self.create_explosion(ai['x'], ai['y'], 1.2, ai['color'])
                
                # Tạo xe mới
                road = random.choice(self.roads)
                t = random.random()
                x = road['x1'] + (road['x2'] - road['x1']) * t
                y = road['y1'] + (road['y2'] - road['y1']) * t
                
                self.ai_cars[i] = {
                    'id': ai['id'],
                    'x': x, 'y': y,
                    'vx': 0, 'vy': 0,
                    'angle': random.uniform(0, 360),
                    'target_x': random.uniform(0, self.width),
                    'target_y': random.uniform(0, self.height),
                    'health': 100,
                    'damage': 0,
                    'color': random.choice(['#FF0000', '#00FF00', '#FFFF00', '#FFA500']),
                    'width': random.randint(22, 28),
                    'height': random.randint(40, 50),
                    'max_speed': random.uniform(3, 6),
                    'acceleration': 0.1,
                    'ai_timer': random.uniform(0, 5),
                    'ai_change_time': random.uniform(2, 6),
                    'behavior': random.choice(['normal', 'aggressive', 'slow']),
                    'score_value': 50
                }
                
                # Thưởng điểm cho phá hủy
                self.score += ai['score_value']
                self.create_text_effect(
                    ai['x'], ai['y'],
                    f"+{ai['score_value']}",
                    '#00FF00',
                    size=25
                )

# ==================== GIAO DIỆN STREAMLIT ====================

def main():
    # CSS toàn bộ trang
    st.markdown("""
    <style>
    /* Reset và toàn trang */
    .main > div {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    
    /* Ẩn sidebar mặc định */
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* Header game */
    .game-header {
        background: linear-gradient(90deg, #1a237e, #283593);
        color: white;
        padding: 10px 20px;
        border-radius: 0 0 10px 10px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Game container */
    .game-container {
        position: relative;
        width: 100%;
        height: 70vh;
        min-height: 500px;
        background: #1a1a2e;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    
    /* Game UI overlay */
    .game-ui {
        position: absolute;
        top: 10px;
        left: 10px;
        z-index: 100;
        background: rgba(0, 0, 0, 0.7);
        padding: 15px;
        border-radius: 10px;
        color: white;
        font-family: 'Arial', sans-serif;
        min-width: 200px;
    }
    
    /* Health bar */
    .health-bar {
        height: 20px;
        background: #333;
        border-radius: 10px;
        overflow: hidden;
        margin: 5px 0;
    }
    
    .health-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff00, #ff0000);
        transition: width 0.3s;
    }
    
    /* Mobile controls */
    .mobile-controls {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
        padding: 15px;
        background: rgba(0, 0, 0, 0.8);
        border-radius: 20px;
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
    }
    
    .control-button {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        border: 3px solid white;
        color: white;
        font-size: 24px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        user-select: none;
        transition: all 0.1s;
    }
    
    .control-button:active {
        background: rgba(255, 255, 255, 0.4);
        transform: scale(0.95);
    }
    
    .control-button.up { background: rgba(0, 150, 255, 0.7); }
    .control-button.down { background: rgba(255, 100, 100, 0.7); }
    .control-button.left { background: rgba(255, 200, 0, 0.7); }
    .control-button.right { background: rgba(0, 200, 100, 0.7); }
    .control-button.space { 
        width: 120px;
        border-radius: 40px;
        background: rgba(150, 0, 255, 0.7);
    }
    
    /* Stats grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin-top: 20px;
    }
    
    .stat-box {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #4fc3f7;
    }
    
    .stat-label {
        font-size: 12px;
        color: #b0bec5;
        margin-top: 5px;
    }
    
    /* Game over overlay */
    .game-over {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 2000;
        color: white;
    }
    
    .game-over h1 {
        font-size: 48px;
        color: #ff5252;
        margin-bottom: 20px;
    }
    
    .game-over h2 {
        font-size: 36px;
        color: #4fc3f7;
        margin-bottom: 30px;
    }
    
    .restart-button {
        background: linear-gradient(45deg, #ff5252, #ff4081);
        color: white;
        padding: 15px 40px;
        border-radius: 50px;
        font-size: 20px;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .restart-button:hover {
        transform: scale(1.05);
    }
    
    /* Canvas container */
    #canvas-container {
        width: 100%;
        height: 100%;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .game-container {
            height: 60vh;
            min-height: 400px;
        }
        
        .game-ui {
            padding: 10px;
            min-width: 160px;
            font-size: 14px;
        }
        
        .control-button {
            width: 70px;
            height: 70px;
            font-size: 20px;
        }
        
        .control-button.space {
            width: 100px;
        }
        
        .mobile-controls {
            padding: 10px;
            bottom: 10px;
        }
    }
    
    @media (max-width: 480px) {
        .game-container {
            height: 50vh;
            min-height: 300px;
        }
        
        .game-ui {
            padding: 8px;
            min-width: 140px;
            font-size: 12px;
        }
        
        .control-button {
            width: 60px;
            height: 60px;
            font-size: 18px;
        }
        
        .control-button.space {
            width: 90px;
        }
        
        .mobile-controls {
            gap: 15px;
            padding: 8px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="game-header">
        <h1 style="margin: 0; font-size: 28px;">🚗 Pixel Crash Simulator</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.8;">Va chạm, phá hủy, ghi điểm!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = Game()
    
    game = st.session_state.game
    
    # Phát hiện thiết bị bằng JavaScript
    st.markdown("""
    <script>
    // Phát hiện thiết bị
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (window.innerWidth <= 768);
    }
    
    // Lưu vào session storage để Python có thể đọc
    if (isMobileDevice()) {
        localStorage.setItem('is_mobile', 'true');
        document.body.classList.add('mobile');
    } else {
        localStorage.setItem('is_mobile', 'false');
        document.body.classList.add('desktop');
    }
    
    // Gửi thông tin về Streamlit
    window.parent.postMessage({
        type: 'device_detected',
        is_mobile: isMobileDevice()
    }, '*');
    </script>
    """, unsafe_allow_html=True)
    
    # Container game chính
    game_html = f"""
    <div class="game-container">
        <canvas id="game-canvas"></canvas>
        
        <div class="game-ui">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-size: 18px; font-weight: bold; color: #4fc3f7;">🏆 {game.score:,}</div>
                <div style="font-size: 14px; color: #b0bec5;">💥 {game.total_crashes}</div>
            </div>
            
            <div class="health-bar">
                <div class="health-fill" style="width: {game.player['health']}%"></div>
            </div>
            <div style="font-size: 12px; margin-top: 5px;">Sức khỏe: {game.player['health']:.0f}%</div>
            
            <div style="margin-top: 10px; font-size: 12px;">
                <div>Hư hại: {game.player['damage']:.0f}%</div>
                <div>Xe AI: {len(game.ai_cars)}</div>
                <div>Tốc độ: {math.sqrt(game.player['vx']**2 + game.player['vy']**2)*20:.0f} km/h</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(game_html, unsafe_allow_html=True)
    
    # JavaScript cho game
    game_js = f"""
    <script>
    // Khởi tạo canvas
    const canvas = document.getElementById('game-canvas');
    const ctx = canvas.getContext('2d');
    
    // Đặt kích thước canvas
    function resizeCanvas() {{
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
    }}
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Game state từ Python
    const gameState = {{
        player: {json.dumps(game.player)},
        ai_cars: {json.dumps(game.ai_cars)},
        particles: {json.dumps(game.particles)},
        buildings: {json.dumps(game.buildings)},
        trees: {json.dumps(game.trees)},
        obstacles: {json.dumps(game.obstacles)},
        roads: {json.dumps(game.roads)},
        explosions: {json.dumps(game.explosions)},
        camera: {{ x: {game.camera_x}, y: {game.camera_y}, zoom: {game.camera_zoom} }},
        width: {game.width},
        height: {game.height}
    }};
    
    // Hàm chuyển đổi tọa độ
    function worldToScreen(wx, wy) {{
        const zoom = gameState.camera.zoom;
        const screenX = (wx - gameState.camera.x + canvas.width / (2 * zoom)) * zoom;
        const screenY = (wy - gameState.camera.y + canvas.height / (2 * zoom)) * zoom;
        return {{ x: screenX, y: screenY }};
    }}
    
    // Hàm vẽ
    function drawRoads() {{
        gameState.roads.forEach(road => {{
            const start = worldToScreen(road.x1, road.y1);
            const end = worldToScreen(road.x2, road.y2);
            
            ctx.beginPath();
            ctx.moveTo(start.x, start.y);
            ctx.lineTo(end.x, end.y);
            ctx.lineWidth = road.width * gameState.camera.zoom;
            ctx.strokeStyle = road.color;
            ctx.lineCap = 'round';
            ctx.stroke();
            
            // Vẽ vạch kẻ đường cho highway
            if (road.type === 'highway') {{
                ctx.setLineDash([20 * gameState.camera.zoom, 10 * gameState.camera.zoom]);
                ctx.lineWidth = 3 * gameState.camera.zoom;
                ctx.strokeStyle = '#FFFFFF';
                
                for (let i = 1; i < road.lanes; i++) {{
                    const offset = (i / road.lanes - 0.5) * road.width * 0.8;
                    const dx = end.x - start.x;
                    const dy = end.y - start.y;
                    const length = Math.sqrt(dx * dx + dy * dy);
                    
                    if (length > 0) {{
                        const perpX = -dy / length * offset;
                        const perpY = dx / length * offset;
                        
                        ctx.beginPath();
                        ctx.moveTo(start.x + perpX, start.y + perpY);
                        ctx.lineTo(end.x + perpX, end.y + perpY);
                        ctx.stroke();
                    }}
                }}
                ctx.setLineDash([]);
            }}
        }});
    }}
    
    function drawBuildings() {{
        gameState.buildings.forEach(building => {{
            const pos = worldToScreen(building.x, building.y);
            const width = building.width * gameState.camera.zoom;
            const height = building.height * gameState.camera.zoom;
            
            // Vẽ tòa nhà
            ctx.fillStyle = building.color;
            ctx.fillRect(pos.x - width/2, pos.y - height/2, width, height);
            
            // Vẽ cửa sổ
            ctx.fillStyle = building.window_color;
            const windowSize = 8 * gameState.camera.zoom;
            const windowGap = 12 * gameState.camera.zoom;
            
            for (let wx = pos.x - width/2 + windowGap; wx < pos.x + width/2; wx += windowGap) {{
                for (let wy = pos.y - height/2 + windowGap; wy < pos.y + height/2; wy += windowGap) {{
                    if (wx < pos.x + width/2 - windowGap && wy < pos.y + height/2 - windowGap) {{
                        ctx.fillRect(wx, wy, windowSize, windowSize);
                    }}
                }}
            }}
            
            // Viền
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 2;
            ctx.strokeRect(pos.x - width/2, pos.y - height/2, width, height);
        }});
    }}
    
    function drawTrees() {{
        gameState.trees.forEach(tree => {{
            const pos = worldToScreen(tree.x, tree.y);
            const size = tree.size * gameState.camera.zoom;
            
            // Thân cây
            ctx.fillStyle = tree.trunk_color;
            const trunkWidth = size * 0.3;
            const trunkHeight = size * 0.5;
            ctx.fillRect(pos.x - trunkWidth/2, pos.y - trunkHeight/2, trunkWidth, trunkHeight);
            
            // Tán lá
            ctx.fillStyle = tree.leaves_color;
            ctx.beginPath();
            ctx.arc(pos.x, pos.y - trunkHeight/2, size/2, 0, Math.PI * 2);
            ctx.fill();
        }});
    }}
    
    function drawObstacles() {{
        gameState.obstacles.forEach(obstacle => {{
            const pos = worldToScreen(obstacle.x, obstacle.y);
            const size = obstacle.size * gameState.camera.zoom;
            
            ctx.fillStyle = obstacle.color;
            
            if (obstacle.type === 'cone') {{
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y - size/2);
                ctx.lineTo(pos.x + size/2, pos.y + size/2);
                ctx.lineTo(pos.x - size/2, pos.y + size/2);
                ctx.closePath();
                ctx.fill();
            }} else if (obstacle.type === 'barrel') {{
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, size/2, 0, Math.PI * 2);
                ctx.fill();
            }} else {{
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, size/2, 0, Math.PI * 2);
                ctx.fill();
            }}
            
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 2;
            ctx.stroke();
        }});
    }}
    
    function drawAICars() {{
        gameState.ai_cars.forEach(car => {{
            const pos = worldToScreen(car.x, car.y);
            const width = car.width * gameState.camera.zoom;
            const height = car.height * gameState.camera.zoom;
            
            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.rotate(car.angle * Math.PI / 180);
            
            // Thân xe
            ctx.fillStyle = car.color;
            ctx.fillRect(-width/2, -height/2, width, height);
            
            // Kính chắn gió
            ctx.fillStyle = '#C8F0FF';
            ctx.fillRect(-width/3, -height/2, width * 2/3, height/4);
            
            // Viền
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 2;
            ctx.strokeRect(-width/2, -height/2, width, height);
            
            // Đèn
            ctx.fillStyle = '#FFFF99';
            ctx.fillRect(-width/2 - 3, -height/4, 6, height/2);
            ctx.fillRect(width/2 - 3, -height/4, 6, height/2);
            
            // Vết nứt nếu bị hư hại
            if (car.damage > 20) {{
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                for (let i = 0; i < Math.min(5, car.damage / 15); i++) {{
                    const x1 = Math.random() * width - width/2;
                    const y1 = Math.random() * height - height/2;
                    const length = 5 + Math.random() * 10;
                    const angle = Math.random() * Math.PI * 2;
                    const x2 = x1 + Math.cos(angle) * length;
                    const y2 = y1 + Math.sin(angle) * length;
                    
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                }}
            }}
            
            ctx.restore();
        }});
    }}
    
    function drawPlayerCar() {{
        const car = gameState.player;
        const pos = worldToScreen(car.x, car.y);
        const width = car.width * gameState.camera.zoom;
        const height = car.height * gameState.camera.zoom;
        
        ctx.save();
        ctx.translate(pos.x, pos.y);
        ctx.rotate(car.angle * Math.PI / 180);
        
        // Thân xe
        ctx.fillStyle = car.color;
        ctx.fillRect(-width/2, -height/2, width, height);
        
        // Viền vàng cho player
        ctx.strokeStyle = '#FFFF00';
        ctx.lineWidth = 3;
        ctx.strokeRect(-width/2, -height/2, width, height);
        
        // Kính chắn gió
        ctx.fillStyle = '#E0F7FF';
        ctx.fillRect(-width/3, -height/2, width * 2/3, height/4);
        
        // Đèn pha
        ctx.fillStyle = '#FFFFC8';
        ctx.fillRect(-width/2 - 5, -height/4, 10, height/2);
        ctx.fillRect(width/2 - 5, -height/4, 10, height/2);
        
        // Đèn phanh nếu đang phanh
        if ({'true' if st.session_state.keys_pressed.get('down', False) or st.session_state.keys_pressed.get('space', False) else 'false'}) {{
            ctx.fillStyle = '#FF3333';
            ctx.fillRect(-width/3, height/2 - 8, width * 2/3, 8);
        }}
        
        // Vết nứt nếu bị hư hại
        if (car.damage > 20) {{
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 3;
            for (let i = 0; i < Math.min(5, car.damage / 15); i++) {{
                const x1 = Math.random() * width - width/2;
                const y1 = Math.random() * height - height/2;
                const length = 5 + Math.random() * 10;
                const angle = Math.random() * Math.PI * 2;
                const x2 = x1 + Math.cos(angle) * length;
                const y2 = y1 + Math.sin(angle) * length;
                
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            }}
        }}
        
        ctx.restore();
    }}
    
    function drawParticles() {{
        gameState.particles.forEach(particle => {{
            const pos = worldToScreen(particle.x, particle.y);
            const size = particle.size * gameState.camera.zoom * particle.life;
            
            if (size > 0) {{
                if (particle.type === 'text') {{
                    ctx.save();
                    ctx.globalAlpha = particle.life;
                    ctx.font = `${{size}}px Arial`;
                    ctx.fillStyle = particle.color;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(particle.text, pos.x, pos.y);
                    ctx.restore();
                }} else {{
                    ctx.save();
                    ctx.translate(pos.x, pos.y);
                    ctx.rotate(particle.rotation * Math.PI / 180);
                    ctx.globalAlpha = particle.life;
                    ctx.fillStyle = particle.color;
                    ctx.fillRect(-size/2, -size/2, size, size);
                    ctx.restore();
                }}
            }}
        }});
    }}
    
    function drawExplosions() {{
        gameState.explosions.forEach(explosion => {{
            const pos = worldToScreen(explosion.x, explosion.y);
            const radius = explosion.radius * gameState.camera.zoom;
            
            const gradient = ctx.createRadialGradient(
                pos.x, pos.y, 0,
                pos.x, pos.y, radius
            );
            gradient.addColorStop(0, explosion.color);
            gradient.addColorStop(1, 'transparent');
            
            ctx.globalAlpha = explosion.life * 0.7;
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }});
    }}
    
    // Hàm vẽ chính
    function draw() {{
        // Xóa canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Vẽ nền trời
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#87CEEB');
        gradient.addColorStop(1, '#4682B4');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Vẽ các thành phần
        drawRoads();
        drawBuildings();
        drawTrees();
        drawObstacles();
        drawAICars();
        drawPlayerCar();
        drawExplosions();
        drawParticles();
    }}
    
    // Vẽ frame đầu tiên
    draw();
    
    // Animation loop
    let lastTime = 0;
    function gameLoop(currentTime) {{
        const dt = Math.min(0.1, (currentTime - lastTime) / 1000);
        lastTime = currentTime;
        
        // Gửi request cập nhật game state
        fetch('/_stcore/api/game/update', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ dt: dt }})
        }})
        .then(response => {{
            if (response.ok) {{
                response.json().then(data => {{
                    // Cập nhật game state
                    Object.assign(gameState, data);
                    
                    // Cập nhật UI
                    if (data.game_running === false) {{
                        // Hiển thị game over
                        document.body.innerHTML += `
                            <div class="game-over">
                                <h1>💥 GAME OVER</h1>
                                <h2>Điểm: ${{data.score.toLocaleString()}}</h2>
                                <button class="restart-button" onclick="window.location.reload()">CHƠI LẠI</button>
                            </div>
                        `;
                    }}
                    
                    // Vẽ lại
                    draw();
                }});
            }}
        }})
        .catch(error => console.error('Error:', error));
        
        requestAnimationFrame(gameLoop);
    }}
    
    // Bắt đầu game loop
    requestAnimationFrame(gameLoop);
    
    // Xử lý input bàn phím
    document.addEventListener('keydown', (e) => {{
        const keyMap = {{
            'ArrowUp': 'up', 'w': 'up', 'W': 'up',
            'ArrowDown': 'down', 's': 'down', 'S': 'down',
            'ArrowLeft': 'left', 'a': 'left', 'A': 'left',
            'ArrowRight': 'right', 'd': 'right', 'D': 'right',
            ' ': 'space'
        }};
        
        if (keyMap[e.key]) {{
            fetch('/_stcore/api/game/keydown', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ key: keyMap[e.key] }})
            }});
            e.preventDefault();
        }}
    }});
    
    document.addEventListener('keyup', (e) => {{
        const keyMap = {{
            'ArrowUp': 'up', 'w': 'up', 'W': 'up',
            'ArrowDown': 'down', 's': 'down', 'S': 'down',
            'ArrowLeft': 'left', 'a': 'left', 'A': 'left',
            'ArrowRight': 'right', 'd': 'right', 'D': 'right',
            ' ': 'space'
        }};
        
        if (keyMap[e.key]) {{
            fetch('/_stcore/api/game/keyup', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ key: keyMap[e.key] }})
            }});
            e.preventDefault();
        }}
    }});
    
    // Prevent scrolling with arrow keys
    window.addEventListener('keydown', function(e) {{
        if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].indexOf(e.code) > -1) {{
            e.preventDefault();
        }}
    }}, false);
    </script>
    """
    
    st.markdown(game_js, unsafe_allow_html=True)
    
    # Kiểm tra nếu là mobile, hiển thị nút điều khiển
    is_mobile = st.session_state.get('is_mobile', False)
    
    if is_mobile:
        st.markdown("""
        <div class="mobile-controls">
            <div class="control-button up" onclick="sendKey('up', true)" ontouchstart="sendKey('up', true)" ontouchend="sendKey('up', false)">↑</div>
            <div class="control-button left" onclick="sendKey('left', true)" ontouchstart="sendKey('left', true)" ontouchend="sendKey('left', false)">←</div>
            <div class="control-button down" onclick="sendKey('down', true)" ontouchstart="sendKey('down', true)" ontouchend="sendKey('down', false)">↓</div>
            <div class="control-button right" onclick="sendKey('right', true)" ontouchstart="sendKey('right', true)" ontouchend="sendKey('right', false)">→</div>
            <div class="control-button space" onclick="sendKey('space', true)" ontouchstart="sendKey('space', true)" ontouchend="sendKey('space', false)">PHANH</div>
        </div>
        
        <script>
        function sendKey(key, isDown) {
            const endpoint = isDown ? '/_stcore/api/game/keydown' : '/_stcore/api/game/keyup';
            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: key })
            });
        }
        
        // Phát hiện thiết bị
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768) {
            localStorage.setItem('is_mobile', 'true');
        }
        </script>
        """, unsafe_allow_html=True)
    else:
        # Hướng dẫn cho PC
        st.markdown("""
        <div style="background: rgba(0,0,0,0.7); color: white; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <h4 style="margin: 0 0 10px 0; color: #4fc3f7;">🎮 ĐIỀU KHIỂN BÀN PHÍM</h4>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <div>• <strong>W / Mũi tên lên</strong>: Tăng tốc</div>
                <div>• <strong>S / Mũi tên xuống</strong>: Phanh</div>
                <div>• <strong>A / Mũi tên trái</strong>: Rẽ trái</div>
                <div>• <strong>D / Mũi tên phải</strong>: Rẽ phải</div>
                <div>• <strong>Space</strong>: Phanh tay</div>
                <div>• <strong>R</strong>: Reset xe (F5 để reload)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats grid
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 Điểm số", f"{game.score:,}")
    with col2:
        st.metric("💥 Va chạm", game.total_crashes)
    with col3:
        st.metric("🚗 Xe AI", len(game.ai_cars))
    with col4:
        st.metric("⏱️ Thời gian", f"{int(game.game_time)}s")
    
    # Game update loop
    if game.game_running:
        current_time = time.time()
        dt = current_time - game.last_update
        
        if dt > 0.016:  # ~60 FPS
            game.update(dt)
            game.last_update = current_time
            st.rerun()

# Chạy app
if __name__ == "__main__":
    main()
