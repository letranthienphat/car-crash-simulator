import streamlit as st
import numpy as np
import math
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum

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
            'braking': 0.3
        }
        
        self.ai_cars = []
        self.particles = []
        self.buildings = []
        self.trees = []
        self.obstacles = []
        self.roads = []
        self.traffic_lights = []
        
        self.score = 0
        self.total_crashes = 0
        self.game_time = 0
        self.camera_x = self.player['x']
        self.camera_y = self.player['y']
        self.camera_zoom = 1.5
        self.last_update = time.time()
        
        # Khởi tạo thế giới
        self.generate_world()
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
    
    def generate_world(self):
        # Tạo đường
        for i in range(0, self.width, 200):
            # Đường ngang
            self.roads.append({
                'x1': 0, 'y1': i,
                'x2': self.width, 'y2': i,
                'width': 80,
                'lanes': 3,
                'color': '#333333'
            })
            # Đường dọc
            self.roads.append({
                'x1': i, 'y1': 0,
                'x2': i, 'y2': self.height,
                'width': 80,
                'lanes': 3,
                'color': '#333333'
            })
        
        # Tạo nhà cửa
        building_colors = ['#C89664', '#A0522D', '#8B4513', '#D2691E', '#CD853F']
        for _ in range(50):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            
            # Kiểm tra không đặt trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road['y1']) < road['width']/2 + 30:
                    on_road = True
                    break
            
            if not on_road:
                self.buildings.append({
                    'x': x, 'y': y,
                    'width': random.randint(40, 80),
                    'height': random.randint(60, 120),
                    'color': random.choice(building_colors),
                    'window_color': '#C8E0FF'
                })
        
        # Tạo cây
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            
            # Kiểm tra không trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road['y1']) < road['width']/2 + 20:
                    on_road = True
                    break
            
            if not on_road:
                self.trees.append({
                    'x': x, 'y': y,
                    'size': random.randint(20, 40),
                    'trunk_color': '#654321',
                    'leaves_color': '#228B22'
                })
        
        # Tạo vật cản
        obstacle_types = [
            {'color': '#FFA500', 'size': 15, 'shape': 'cone'},
            {'color': '#FF0000', 'size': 20, 'shape': 'barrel'},
            {'color': '#666666', 'size': 25, 'shape': 'rock'},
            {'color': '#FFFF00', 'size': 10, 'shape': 'cone'}
        ]
        
        for _ in range(30):
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            
            # Kiểm tra trên đường
            on_road = False
            for road in self.roads:
                if abs(y - road['y1']) < road['width']/2:
                    on_road = True
                    break
            
            if on_road:
                obstacle = random.choice(obstacle_types)
                self.obstacles.append({
                    'x': x, 'y': y,
                    'color': obstacle['color'],
                    'size': obstacle['size'],
                    'shape': obstacle['shape']
                })
    
    def spawn_ai_cars(self, count: int):
        ai_colors = ['#FF0000', '#00FF00', '#FFFF00', '#FFA500', '#800080', '#00FFFF', '#FFC0CB']
        
        for _ in range(count):
            # Chọn đường ngẫu nhiên
            road = random.choice(self.roads)
            t = random.random()
            x = road['x1'] + (road['x2'] - road['x1']) * t
            y = road['y1'] + (road['y2'] - road['y1']) * t
            
            # Thêm offset
            x += random.uniform(-20, 20)
            y += random.uniform(-20, 20)
            
            self.ai_cars.append({
                'x': x, 'y': y,
                'vx': 0, 'vy': 0,
                'angle': random.uniform(0, 360),
                'target_x': random.uniform(0, self.width),
                'target_y': random.uniform(0, self.height),
                'health': 100,
                'damage': 0,
                'color': random.choice(ai_colors),
                'width': 25,
                'height': 45,
                'max_speed': random.uniform(3, 6),
                'acceleration': 0.1,
                'ai_timer': random.uniform(0, 5),
                'ai_change_time': random.uniform(2, 5)
            })
    
    def update(self, dt: float):
        # Cập nhật player
        self.update_player(dt)
        
        # Cập nhật AI cars
        self.update_ai_cars(dt)
        
        # Cập nhật particles
        self.update_particles(dt)
        
        # Cập nhật camera
        self.camera_x += (self.player['x'] - self.camera_x) * 0.1
        self.camera_y += (self.player['y'] - self.camera_y) * 0.1
        
        # Cập nhật thời gian
        self.game_time += dt
        
        # Kiểm tra va chạm
        self.check_collisions()
        
        # Hồi sinh AI cars bị phá hủy
        for i, ai in enumerate(self.ai_cars):
            if ai['health'] <= 0:
                # Tạo hiệu ứng nổ
                for _ in range(30):
                    self.create_particle(
                        ai['x'], ai['y'],
                        ai['color'],
                        random.uniform(-5, 5),
                        random.uniform(-5, 5),
                        random.randint(3, 8)
                    )
                
                # Tạo xe mới
                road = random.choice(self.roads)
                t = random.random()
                x = road['x1'] + (road['x2'] - road['x1']) * t
                y = road['y1'] + (road['y2'] - road['y1']) * t
                
                self.ai_cars[i] = {
                    'x': x, 'y': y,
                    'vx': 0, 'vy': 0,
                    'angle': random.uniform(0, 360),
                    'target_x': random.uniform(0, self.width),
                    'target_y': random.uniform(0, self.height),
                    'health': 100,
                    'damage': 0,
                    'color': random.choice(['#FF0000', '#00FF00', '#FFFF00']),
                    'width': 25,
                    'height': 45,
                    'max_speed': random.uniform(3, 6),
                    'acceleration': 0.1,
                    'ai_timer': random.uniform(0, 5),
                    'ai_change_time': random.uniform(2, 5)
                }
                self.score += 100
    
    def update_player(self, dt: float):
        # Lấy input
        keys = st.session_state.keys_pressed
        
        # Tăng tốc
        if keys.get('up', False):
            rad = math.radians(self.player['angle'])
            self.player['vx'] += math.cos(rad) * self.player['acceleration']
            self.player['vy'] += math.sin(rad) * self.player['acceleration']
        
        # Phanh
        if keys.get('down', False):
            self.player['vx'] *= 0.9
            self.player['vy'] *= 0.9
        
        # Lái trái
        if keys.get('left', False):
            self.player['angle'] -= 3
        
        # Lái phải
        if keys.get('right', False):
            self.player['angle'] += 3
        
        # Phanh tay
        if keys.get('space', False):
            self.player['vx'] *= 0.7
            self.player['vy'] *= 0.7
        
        # Giới hạn tốc độ
        speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
        if speed > self.player['max_speed']:
            scale = self.player['max_speed'] / speed
            self.player['vx'] *= scale
            self.player['vy'] *= scale
        
        # Cập nhật vị trí
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Ma sát
        self.player['vx'] *= 0.98
        self.player['vy'] *= 0.98
        
        # Tạo vết lốp
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
            
            # Tính toán hướng
            dx = ai['target_x'] - ai['x']
            dy = ai['target_y'] - ai['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 10:
                # Di chuyển về target
                ai['vx'] += (dx / dist) * ai['acceleration']
                ai['vy'] += (dy / dist) * ai['acceleration']
                
                # Cập nhật góc
                target_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = (target_angle - ai['angle']) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                ai['angle'] += angle_diff * 0.08
            
            # Giới hạn tốc độ
            speed = math.sqrt(ai['vx']**2 + ai['vy']**2)
            if speed > ai['max_speed']:
                scale = ai['max_speed'] / speed
                ai['vx'] *= scale
                ai['vy'] *= scale
            
            # Cập nhật vị trí
            ai['x'] += ai['vx']
            ai['y'] += ai['vy']
            
            # Ma sát
            ai['vx'] *= 0.98
            ai['vy'] *= 0.98
    
    def create_particle(self, x: float, y: float, color: str, vx: float, vy: float, size: int):
        self.particles.append({
            'x': x, 'y': y,
            'vx': vx, 'vy': vy,
            'color': color,
            'size': size,
            'life': 1.0,
            'gravity': 0.5,
            'friction': 0.98
        })
    
    def update_particles(self, dt: float):
        for particle in self.particles[:]:
            # Cập nhật vật lý
            particle['vy'] += particle['gravity']
            particle['vx'] *= particle['friction']
            particle['vy'] *= particle['friction']
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.02
            particle['size'] = max(1, particle['size'] * 0.95)
            
            # Xóa particle đã chết
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
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
                
                # Áp dụng damage
                self.player['health'] -= force * 2
                self.player['damage'] += force * 2
                ai['health'] -= force * 2
                ai['damage'] += force * 2
                
                # Tạo particles
                crash_x = (self.player['x'] + ai['x']) / 2
                crash_y = (self.player['y'] + ai['y']) / 2
                
                num_particles = int(force * 5)
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
                    push_x = dx / distance * force * 0.5
                    push_y = dy / distance * force * 0.5
                    
                    self.player['vx'] += push_x
                    self.player['vy'] += push_y
                    ai['vx'] -= push_x
                    ai['vy'] -= push_y
                
                # Cập nhật điểm
                self.total_crashes += 1
                self.score += int(force * 10)

# ==================== GIAO DIỆN STREAMLIT ====================

def main():
    st.title("💥 Pixel Crash Simulator")
    st.markdown("### Game Va Chạm Xe Pixel - Không Cần Pillow!")
    
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = Game()
        st.session_state.game_running = True
    
    game = st.session_state.game
    
    # Sidebar điều khiển
    with st.sidebar:
        st.header("🎮 Điều Khiển Game")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Bắt đầu" if not st.session_state.game_running else "⏸️ Dừng", 
                        use_container_width=True):
                st.session_state.game_running = not st.session_state.game_running
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset Game", use_container_width=True):
                st.session_state.game = Game()
                st.rerun()
        
        st.markdown("---")
        
        st.subheader("📷 Camera")
        game.camera_zoom = st.slider("Zoom", 0.5, 3.0, game.camera_zoom, 0.1)
        
        st.subheader("⚙️ Cài Đặt")
        ai_count = st.slider("Số lượng xe AI", 5, 30, len(game.ai_cars))
        if ai_count != len(game.ai_cars):
            game.ai_cars = game.ai_cars[:ai_count]
            if len(game.ai_cars) < ai_count:
                game.spawn_ai_cars(ai_count - len(game.ai_cars))
        
        damage_multiplier = st.slider("Lực va chạm", 0.5, 3.0, 1.0, 0.1)
        
        st.markdown("---")
        
        st.subheader("📊 Thống Kê")
        st.metric("🏆 Điểm số", f"{game.score:,}")
        st.metric("💥 Số lần va chạm", game.total_crashes)
        st.metric("⚠️ Hư hại xe", f"{game.player['damage']:.0f}%")
        st.metric("❤️ Sức khỏe", f"{game.player['health']:.0f}%")
        
        st.markdown("---")
        
        st.subheader("⌨️ Điều Khiển")
        st.markdown("""
        - **W/↑**: Tăng tốc
        - **S/↓**: Phanh
        - **A/←**: Lái trái
        - **D/→**: Lái phải
        - **Space**: Phanh tay
        - **R**: Reset xe
        """)
    
    # Main game area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Game canvas sẽ được tạo bằng HTML/JS
        st.markdown(f"""
        <div id="game-container" style="position: relative; width: 800px; height: 600px; margin: 0 auto;">
            <canvas id="game-canvas" width="800" height="600" 
                    style="border: 2px solid #333; background: #87CEEB;"></canvas>
            <div id="game-ui" style="position: absolute; top: 10px; left: 10px; color: white; font-family: Arial;">
                <div style="background: rgba(0,0,0,0.7); padding: 10px; border-radius: 5px;">
                    <div>🏆 Điểm: {game.score:,}</div>
                    <div>❤️ HP: {game.player['health']:.0f}%</div>
                    <div>⚠️ Hư hại: {game.player['damage']:.0f}%</div>
                    <div>💥 Va chạm: {game.total_crashes}</div>
                    <div>🚗 Xe AI: {len(game.ai_cars)}</div>
                </div>
            </div>
        </div>
        
        <script>
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        
        // Game state từ Python
        const gameState = {{
            player: {json.dumps(game.player)},
            ai_cars: {json.dumps(game.ai_cars)},
            particles: {json.dumps(game.particles)},
            buildings: {json.dumps(game.buildings)},
            trees: {json.dumps(game.trees)},
            obstacles: {json.dumps(game.obstacles)},
            roads: {json.dumps(game.roads)},
            camera: {{ x: {game.camera_x}, y: {game.camera_y}, zoom: {game.camera_zoom} }},
            width: {game.width},
            height: {game.height}
        }};
        
        // Hàm chuyển đổi từ world coordinates sang screen coordinates
        function worldToScreen(wx, wy) {{
            const zoom = gameState.camera.zoom;
            const screenX = (wx - gameState.camera.x + canvas.width / (2 * zoom)) * zoom;
            const screenY = (wy - gameState.camera.y + canvas.height / (2 * zoom)) * zoom;
            return {{ x: screenX, y: screenY }};
        }}
        
        // Vẽ đường
        function drawRoads() {{
            gameState.roads.forEach(road => {{
                const start = worldToScreen(road.x1, road.y1);
                const end = worldToScreen(road.x2, road.y2);
                
                ctx.beginPath();
                ctx.moveTo(start.x, start.y);
                ctx.lineTo(end.x, end.y);
                ctx.lineWidth = road.width * gameState.camera.zoom;
                ctx.strokeStyle = road.color;
                ctx.stroke();
                
                // Vẽ vạch kẻ đường
                if (road.width > 40) {{
                    ctx.setLineDash([20 * gameState.camera.zoom, 10 * gameState.camera.zoom]);
                    ctx.lineWidth = 2 * gameState.camera.zoom;
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
        
        // Vẽ nhà cửa
        function drawBuildings() {{
            gameState.buildings.forEach(building => {{
                const pos = worldToScreen(building.x, building.y);
                const width = building.width * gameState.camera.zoom;
                const height = building.height * gameState.camera.zoom;
                
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
                ctx.lineWidth = 1;
                ctx.strokeRect(pos.x - width/2, pos.y - height/2, width, height);
            }});
        }}
        
        // Vẽ cây
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
        
        // Vẽ vật cản
        function drawObstacles() {{
            gameState.obstacles.forEach(obstacle => {{
                const pos = worldToScreen(obstacle.x, obstacle.y);
                const size = obstacle.size * gameState.camera.zoom;
                
                ctx.fillStyle = obstacle.color;
                
                if (obstacle.shape === 'cone') {{
                    ctx.beginPath();
                    ctx.moveTo(pos.x, pos.y - size/2);
                    ctx.lineTo(pos.x + size/2, pos.y + size/2);
                    ctx.lineTo(pos.x - size/2, pos.y + size/2);
                    ctx.closePath();
                    ctx.fill();
                }} else if (obstacle.shape === 'barrel') {{
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, size/2, 0, Math.PI * 2);
                    ctx.fill();
                }} else {{ // rock
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, size/2, 0, Math.PI * 2);
                    ctx.fill();
                }}
                
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 1;
                ctx.stroke();
            }});
        }}
        
        // Vẽ xe AI
        function drawAICars() {{
            gameState.ai_cars.forEach(car => {{
                const pos = worldToScreen(car.x, car.y);
                const width = car.width * gameState.camera.zoom;
                const height = car.height * gameState.camera.zoom;
                
                // Lưu context
                ctx.save();
                
                // Xoay canvas theo góc xe
                ctx.translate(pos.x, pos.y);
                ctx.rotate(car.angle * Math.PI / 180);
                
                // Vẽ thân xe
                ctx.fillStyle = car.color;
                ctx.fillRect(-width/2, -height/2, width, height);
                
                // Vẽ kính chắn gió
                ctx.fillStyle = '#C8F0FF';
                ctx.fillRect(-width/3, -height/2, width * 2/3, height/4);
                
                // Viền
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 1;
                ctx.strokeRect(-width/2, -height/2, width, height);
                
                // Vết nứt nếu bị hư hại
                if (car.damage > 30) {{
                    ctx.strokeStyle = '#000000';
                    ctx.lineWidth = 2;
                    for (let i = 0; i < Math.min(5, car.damage / 20); i++) {{
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
                
                // Khôi phục context
                ctx.restore();
            }});
        }}
        
        // Vẽ player car
        function drawPlayerCar() {{
            const car = gameState.player;
            const pos = worldToScreen(car.x, car.y);
            const width = car.width * gameState.camera.zoom;
            const height = car.height * gameState.camera.zoom;
            
            // Lưu context
            ctx.save();
            
            // Xoay canvas theo góc xe
            ctx.translate(pos.x, pos.y);
            ctx.rotate(car.angle * Math.PI / 180);
            
            // Vẽ thân xe
            ctx.fillStyle = car.color;
            ctx.fillRect(-width/2, -height/2, width, height);
            
            // Viền vàng cho player
            ctx.strokeStyle = '#FFFF00';
            ctx.lineWidth = 2;
            ctx.strokeRect(-width/2, -height/2, width, height);
            
            // Vẽ kính chắn gió
            ctx.fillStyle = '#E0F7FF';
            ctx.fillRect(-width/3, -height/2, width * 2/3, height/4);
            
            // Vẽ đèn pha
            ctx.fillStyle = '#FFFFC8';
            ctx.fillRect(-width/2 - 5, -height/4, 10, height/2);
            ctx.fillRect(width/2 - 5, -height/4, 10, height/2);
            
            // Đèn phanh nếu đang phanh
            const keysPressed = {json.dumps(st.session_state.keys_pressed)};
            if (keysPressed.down || keysPressed.space) {{
                ctx.fillStyle = '#FF3333';
                ctx.fillRect(-width/3, height/2 - 8, width * 2/3, 8);
            }}
            
            // Vết nứt nếu bị hư hại
            if (car.damage > 30) {{
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                for (let i = 0; i < Math.min(5, car.damage / 20); i++) {{
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
            
            // Khôi phục context
            ctx.restore();
        }}
        
        // Vẽ particles
        function drawParticles() {{
            gameState.particles.forEach(particle => {{
                const pos = worldToScreen(particle.x, particle.y);
                const size = particle.size * gameState.camera.zoom * particle.life;
                
                if (size > 0) {{
                    ctx.fillStyle = particle.color;
                    ctx.globalAlpha = particle.life;
                    ctx.fillRect(pos.x - size/2, pos.y - size/2, size, size);
                    ctx.globalAlpha = 1.0;
                }}
            }});
        }}
        
        // Vẽ lưới (để tham khảo)
        function drawGrid() {{
            const gridSize = 100;
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 1;
            
            // Tính toán phạm vi hiển thị
            const zoom = gameState.camera.zoom;
            const startX = Math.floor((gameState.camera.x - canvas.width / (2 * zoom)) / gridSize) * gridSize;
            const endX = Math.ceil((gameState.camera.x + canvas.width / (2 * zoom)) / gridSize) * gridSize;
            const startY = Math.floor((gameState.camera.y - canvas.height / (2 * zoom)) / gridSize) * gridSize;
            const endY = Math.ceil((gameState.camera.y + canvas.height / (2 * zoom)) / gridSize) * gridSize;
            
            // Vẽ đường kẻ dọc
            for (let x = startX; x <= endX; x += gridSize) {{
                const screenPos = worldToScreen(x, 0);
                ctx.beginPath();
                ctx.moveTo(screenPos.x, 0);
                ctx.lineTo(screenPos.x, canvas.height);
                ctx.stroke();
            }}
            
            // Vẽ đường kẻ ngang
            for (let y = startY; y <= endY; y += gridSize) {{
                const screenPos = worldToScreen(0, y);
                ctx.beginPath();
                ctx.moveTo(0, screenPos.y);
                ctx.lineTo(canvas.width, screenPos.y);
                ctx.stroke();
            }}
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
            drawGrid();
            drawBuildings();
            drawTrees();
            drawObstacles();
            drawAICars();
            drawPlayerCar();
            drawParticles();
        }}
        
        // Vẽ frame đầu tiên
        draw();
        
        // Cập nhật game nếu đang chạy
        let lastTime = 0;
        function gameLoop(currentTime) {{
            const dt = Math.min(0.1, (currentTime - lastTime) / 1000);
            lastTime = currentTime;
            
            // Gửi request cập nhật nếu game đang chạy
            if ({'true' if st.session_state.game_running else 'false'}) {{
                fetch('/_stcore/api/game/update', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ dt: dt * {damage_multiplier} }})
                }})
                .then(response => response.json())
                .then(data => {{
                    // Cập nhật game state
                    Object.assign(gameState, data);
                    
                    // Cập nhật UI
                    document.getElementById('game-ui').innerHTML = `
                        <div style="background: rgba(0,0,0,0.7); padding: 10px; border-radius: 5px;">
                            <div>🏆 Điểm: ${{data.score.toLocaleString()}}</div>
                            <div>❤️ HP: ${{data.player.health.toFixed(0)}}%</div>
                            <div>⚠️ Hư hại: ${{data.player.damage.toFixed(0)}}%</div>
                            <div>💥 Va chạm: ${{data.total_crashes}}</div>
                            <div>🚗 Xe AI: ${{data.ai_cars.length}}</div>
                        </div>
                    `;
                    
                    // Vẽ lại
                    draw();
                }});
            }}
            
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
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ key: keyMap[e.key] }})
                }});
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
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ key: keyMap[e.key] }})
                }});
            }}
        }});
        </script>
        """, unsafe_allow_html=True)
        
        # Game controls
        st.markdown("### 🎮 Điều Khiển Trực Tiếp")
        control_cols = st.columns(5)
        
        with control_cols[0]:
            if st.button("↑ Tăng tốc", use_container_width=True, key="btn_up"):
                st.session_state.keys_pressed['up'] = True
                st.rerun()
        
        with control_cols[1]:
            if st.button("↓ Phanh", use_container_width=True, key="btn_down"):
                st.session_state.keys_pressed['down'] = True
                st.rerun()
        
        with control_cols[2]:
            if st.button("← Trái", use_container_width=True, key="btn_left"):
                st.session_state.keys_pressed['left'] = True
                st.rerun()
        
        with control_cols[3]:
            if st.button("→ Phải", use_container_width=True, key="btn_right"):
                st.session_state.keys_pressed['right'] = True
                st.rerun()
        
        with control_cols[4]:
            if st.button("Space Phanh tay", use_container_width=True, key="btn_space"):
                st.session_state.keys_pressed['space'] = True
                st.rerun()
    
    with col2:
        # Car info
        st.subheader("🚗 Thông Tin Xe")
        st.progress(game.player['health']/100, f"Sức khỏe: {game.player['health']:.0f}%")
        st.progress(game.player['damage']/100, f"Hư hại: {game.player['damage']:.0f}%")
        
        speed = math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20
        st.metric("📊 Tốc độ", f"{speed:.0f} km/h")
        st.metric("🎯 Hướng", f"{game.player['angle']:.0f}°")
        
        # Quick actions
        st.subheader("⚡ Hành Động Nhanh")
        if st.button("💥 Va chạm mạnh!", use_container_width=True):
            game.player['vx'] = 15
            if game.ai_cars:
                nearest = min(game.ai_cars, key=lambda c: 
                            math.sqrt((c['x']-game.player['x'])**2 + (c['y']-game.player['y'])**2))
                force = 20
                game.player['health'] -= force * 2
                game.player['damage'] += force * 2
                nearest['health'] -= force * 2
                nearest['damage'] += force * 2
                game.total_crashes += 1
                game.score += int(force * 10)
        
        if st.button("🔄 Đặt lại vị trí", use_container_width=True):
            game.player['x'] = 400
            game.player['y'] = 300
            game.player['vx'] = 0
            game.player['vy'] = 0
            game.player['health'] = 100
        
        if st.button("🔧 Sửa xe", use_container_width=True):
            game.player['health'] = min(100, game.player['health'] + 30)
            game.player['damage'] = max(0, game.player['damage'] - 20)
    
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
            - **Camera follow** với zoom linh hoạt
            
            ### 🚗 XE AI THÔNG MINH:
            - **Di chuyển tự động** trên đường
            - **Tránh vật cản** cơ bản
            - **Hồi sinh** khi bị phá hủy
            - **Màu sắc đa dạng**
            """)
    
    # API endpoints cho game loop
    if st.session_state.game_running:
        current_time = time.time()
        dt = current_time - game.last_update
        
        if dt > 0.016:  # ~60 FPS
            game.update(dt)
            game.last_update = current_time
            st.rerun()

if __name__ == "__main__":
    main()
