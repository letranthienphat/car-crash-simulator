import streamlit as st
import math
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="Pixel Crash Simulator 2D",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS để ẩn các phần tử Streamlit và thiết lập game
st.markdown("""
<style>
    /* Ẩn các phần tử mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {max-width: 100%; padding: 0;}
    
    /* Container chính cho toàn bộ game */
    .game-main {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        margin: 0;
        padding: 0;
        background: #000;
        overflow: hidden;
    }
    
    /* Canvas container */
    .canvas-container {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
    }
    
    /* Canvas - ĐẢM BẢO HIỂN THỊ ĐẦY ĐỦ */
    #game-canvas {
        display: block;
        width: 100%;
        height: 100%;
        background: #1a1a2e;
        image-rendering: pixelated;
        image-rendering: crisp-edges;
    }
    
    /* UI overlay - nhỏ ở góc trái trên */
    .game-ui {
        position: absolute;
        top: 10px;
        left: 10px;
        z-index: 100;
        background: rgba(0, 0, 0, 0.8);
        padding: 12px;
        border-radius: 8px;
        color: white;
        font-family: monospace;
        font-size: 14px;
        width: 180px;
        border: 2px solid #4fc3f7;
        pointer-events: none;
    }
    
    /* Health bar */
    .health-bar {
        width: 100%;
        height: 15px;
        background: #333;
        border-radius: 7px;
        overflow: hidden;
        margin: 8px 0;
    }
    
    .health-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff00, #ff0000);
        transition: width 0.3s;
    }
    
    /* Mobile controls */
    .mobile-controls {
        position: fixed;
        bottom: 20px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        gap: 15px;
        padding: 15px;
        z-index: 200;
        background: rgba(0, 0, 0, 0.5);
        display: none;
    }
    
    .mobile-btn {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        border: 2px solid white;
        color: white;
        font-size: 20px;
        font-weight: bold;
        cursor: pointer;
        user-select: none;
    }
    
    /* Game over screen */
    .game-over {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.95);
        display: none;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        color: white;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HỆ THỐNG GAME PIXEL 2D ====================

class PixelCarGame:
    def __init__(self):
        # Kích thước thế giới game
        self.world_width = 2000
        self.world_height = 2000
        
        # Player car
        self.player = {
            'x': 500,
            'y': 500,
            'vx': 0,
            'vy': 0,
            'angle': 0,
            'health': 100,
            'damage': 0,
            'color': (0, 102, 204),  # Blue
            'width': 16,  # pixels
            'height': 32,  # pixels
            'max_speed': 5,
            'acceleration': 0.15,
            'braking': 0.2,
        }
        
        # AI cars
        self.ai_cars = []
        self.particles = []
        self.roads = []
        self.buildings = []
        self.obstacles = []
        
        # Game stats
        self.score = 0
        self.crashes = 0
        self.game_time = 0
        self.camera_x = self.player['x']
        self.camera_y = self.player['y']
        self.camera_zoom = 2.0
        self.game_running = True
        self.last_update = time.time()
        
        # Generate world
        self.generate_world()
        self.spawn_ai_cars(10)
        
        # Input state
        if 'keys_pressed' not in st.session_state:
            st.session_state.keys_pressed = {
                'up': False, 'down': False, 'left': False, 'right': False, 
                'w': False, 'a': False, 's': False, 'd': False, 'space': False
            }
    
    def generate_world(self):
        """Tạo thế giới pixel 2D"""
        # Tạo đường
        road_width = 100
        for i in range(-5, 5):
            self.roads.append({
                'x': 0,
                'y': i * 300,
                'width': self.world_width,
                'height': road_width,
                'color': (60, 60, 60)
            })
            self.roads.append({
                'x': i * 300,
                'y': 0,
                'width': road_width,
                'height': self.world_height,
                'color': (60, 60, 60)
            })
        
        # Tạo các tòa nhà pixel
        building_colors = [
            (139, 69, 19),   # Brown
            (160, 82, 45),   # Sienna
            (210, 105, 30),  # Chocolate
        ]
        
        for _ in range(50):
            x = random.randint(100, self.world_width - 100)
            y = random.randint(100, self.world_height - 100)
            
            # Kiểm tra không trên đường
            on_road = False
            for road in self.roads:
                if (abs(x - road['x']) < road['width']/2 + 80 and 
                    abs(y - road['y']) < road['height']/2 + 80):
                    on_road = True
                    break
            
            if not on_road:
                width = random.choice([40, 60, 80])
                height = random.choice([60, 80, 100])
                
                self.buildings.append({
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'color': random.choice(building_colors),
                    'window_color': (200, 200, 255)
                })
        
        # Tạo vật cản
        for _ in range(30):
            x = random.randint(50, self.world_width - 50)
            y = random.randint(50, self.world_height - 50)
            
            # Chỉ đặt trên đường
            on_road = False
            for road in self.roads:
                if (abs(x - road['x']) < road['width']/2 - 30 and 
                    abs(y - road['y']) < road['height']/2 - 30):
                    on_road = True
                    break
            
            if on_road:
                self.obstacles.append({
                    'x': x,
                    'y': y,
                    'size': random.randint(8, 16),
                    'color': random.choice([(255, 0, 0), (255, 165, 0), (255, 255, 0)]),
                    'type': random.choice(['cone', 'barrel', 'block'])
                })
    
    def spawn_ai_cars(self, count):
        """Sinh xe AI"""
        ai_colors = [
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (255, 255, 0),   # Yellow
            (255, 165, 0),   # Orange
            (128, 0, 128),   # Purple
        ]
        
        for i in range(count):
            # Chọn một con đường ngẫu nhiên
            road = random.choice(self.roads)
            
            if road['width'] > road['height']:  # Đường ngang
                x = random.randint(road['x'], road['x'] + road['width'])
                y = road['y']
                angle = 0 if random.random() > 0.5 else 180
            else:  # Đường dọc
                x = road['x']
                y = random.randint(road['y'], road['y'] + road['height'])
                angle = 90 if random.random() > 0.5 else 270
            
            self.ai_cars.append({
                'id': i,
                'x': x,
                'y': y,
                'vx': 0,
                'vy': 0,
                'angle': angle,
                'health': 100,
                'damage': 0,
                'color': random.choice(ai_colors),
                'width': 14,
                'height': 28,
                'max_speed': random.uniform(2, 4),
                'acceleration': 0.08,
                'target_x': random.randint(0, self.world_width),
                'target_y': random.randint(0, self.world_height),
                'ai_timer': random.uniform(0, 3)
            })
    
    def update(self, dt):
        """Cập nhật trạng thái game"""
        if not self.game_running:
            return
        
        # Cập nhật player
        self.update_player(dt)
        
        # Cập nhật AI cars
        self.update_ai_cars(dt)
        
        # Cập nhật particles
        self.update_particles(dt)
        
        # Cập nhật camera
        self.camera_x = self.player['x']
        self.camera_y = self.player['y']
        
        # Cập nhật thời gian
        self.game_time += dt
        
        # Kiểm tra va chạm
        self.check_collisions()
        
        # Kiểm tra game over
        if self.player['health'] <= 0:
            self.game_running = False
    
    def update_player(self, dt):
        """Cập nhật xe player"""
        keys = st.session_state.keys_pressed
        
        # Tăng tốc
        if keys.get('up', False) or keys.get('w', False):
            rad = math.radians(self.player['angle'])
            self.player['vx'] += math.cos(rad) * self.player['acceleration']
            self.player['vy'] += math.sin(rad) * self.player['acceleration']
        
        # Phanh
        if keys.get('down', False) or keys.get('s', False):
            self.player['vx'] *= 0.85
            self.player['vy'] *= 0.85
        
        # Lái trái
        if keys.get('left', False) or keys.get('a', False):
            self.player['angle'] -= 4
        
        # Lái phải
        if keys.get('right', False) or keys.get('d', False):
            self.player['angle'] += 4
        
        # Phanh tay
        if keys.get('space', False):
            self.player['vx'] *= 0.6
            self.player['vy'] *= 0.6
        
        # Giới hạn tốc độ
        speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
        if speed > self.player['max_speed']:
            scale = self.player['max_speed'] / speed
            self.player['vx'] *= scale
            self.player['vy'] *= scale
        
        # Cập nhật vị trí
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Giữ trong bản đồ
        self.player['x'] = max(50, min(self.world_width - 50, self.player['x']))
        self.player['y'] = max(50, min(self.world_height - 50, self.player['y']))
        
        # Ma sát
        self.player['vx'] *= 0.96
        self.player['vy'] *= 0.96
        
        # Tạo particles từ lốp xe
        if speed > 1.5 and random.random() < 0.2:
            self.create_particle(
                self.player['x'] - math.cos(math.radians(self.player['angle'])) * 20,
                self.player['y'] - math.sin(math.radians(self.player['angle'])) * 20,
                (100, 100, 100),
                self.player['vx'] * 0.3,
                self.player['vy'] * 0.3,
                2
            )
    
    def update_ai_cars(self, dt):
        """Cập nhật xe AI"""
        for ai in self.ai_cars:
            ai['ai_timer'] += dt
            
            # Đổi hướng định kỳ
            if ai['ai_timer'] > random.uniform(1, 4):
                ai['target_x'] = random.randint(0, self.world_width)
                ai['target_y'] = random.randint(0, self.world_height)
                ai['ai_timer'] = 0
            
            # Di chuyển về target
            dx = ai['target_x'] - ai['x']
            dy = ai['target_y'] - ai['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 50:
                ai['vx'] += (dx / dist) * ai['acceleration']
                ai['vy'] += (dy / dist) * ai['acceleration']
                
                # Cập nhật góc
                if abs(dx) > 1 or abs(dy) > 1:
                    target_angle = math.degrees(math.atan2(dy, dx))
                    angle_diff = (target_angle - ai['angle']) % 360
                    if angle_diff > 180:
                        angle_diff -= 360
                    ai['angle'] += angle_diff * 0.05
            
            # Giới hạn tốc độ
            speed = math.sqrt(ai['vx']**2 + ai['vy']**2)
            if speed > ai['max_speed']:
                scale = ai['max_speed'] / speed
                ai['vx'] *= scale
                ai['vy'] *= scale
            
            # Cập nhật vị trí
            ai['x'] += ai['vx']
            ai['y'] += ai['vy']
            
            # Giữ trong bản đồ
            ai['x'] = max(50, min(self.world_width - 50, ai['x']))
            ai['y'] = max(50, min(self.world_height - 50, ai['y']))
            
            # Ma sát
            ai['vx'] *= 0.97
            ai['vy'] *= 0.97
    
    def create_particle(self, x, y, color, vx, vy, size):
        """Tạo particle (pixel vỡ ra khi va chạm)"""
        self.particles.append({
            'x': x,
            'y': y,
            'vx': vx,
            'vy': vy,
            'color': color,
            'size': size,
            'life': 1.0,
            'gravity': 0.1,
            'friction': 0.95
        })
    
    def update_particles(self, dt):
        """Cập nhật particles"""
        new_particles = []
        for p in self.particles:
            p['vy'] += p['gravity']
            p['vx'] *= p['friction']
            p['vy'] *= p['friction']
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.03
            
            if p['life'] > 0:
                new_particles.append(p)
        self.particles = new_particles
    
    def check_collisions(self):
        """Kiểm tra va chạm giữa các xe"""
        # Va chạm player với AI
        for ai in self.ai_cars[:]:
            dx = self.player['x'] - ai['x']
            dy = self.player['y'] - ai['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            # Khoảng cách va chạm
            collision_dist = (self.player['width'] + ai['width']) / 2
            
            if dist < collision_dist:
                # Tính lực va chạm
                player_speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
                ai_speed = math.sqrt(ai['vx']**2 + ai['vy']**2)
                force = player_speed + ai_speed
                
                if force > 0.5:
                    # Damage
                    damage = force * 20
                    self.player['health'] = max(0, self.player['health'] - damage)
                    self.player['damage'] = min(100, self.player['damage'] + damage)
                    ai['health'] = max(0, ai['health'] - damage)
                    ai['damage'] = min(100, ai['damage'] + damage)
                    
                    # Tạo particles vỡ (pixel)
                    for _ in range(int(force * 10)):
                        particle_color = random.choice([self.player['color'], ai['color'], (255, 255, 255)])
                        self.create_particle(
                            (self.player['x'] + ai['x']) / 2,
                            (self.player['y'] + ai['y']) / 2,
                            particle_color,
                            random.uniform(-force*3, force*3),
                            random.uniform(-force*3, force*3),
                            random.randint(2, 5)
                        )
                    
                    # Đẩy xe ra
                    if dist > 0:
                        push = force * 2
                        self.player['vx'] += (dx / dist) * push
                        self.player['vy'] += (dy / dist) * push
                        ai['vx'] -= (dx / dist) * push
                        ai['vy'] -= (dy / dist) * push
                    
                    # Cập nhật điểm
                    self.crashes += 1
                    self.score += int(force * 50)
                    
                    # Nếu AI bị phá hủy
                    if ai['health'] <= 0:
                        # Tạo thêm particles khi xe nổ
                        for _ in range(30):
                            self.create_particle(
                                ai['x'],
                                ai['y'],
                                ai['color'],
                                random.uniform(-8, 8),
                                random.uniform(-8, 8),
                                random.randint(3, 6)
                            )
                        self.ai_cars.remove(ai)
                        self.score += 200
                        # Spawn xe AI mới
                        self.spawn_ai_cars(1)

# ==================== GIAO DIỆN STREAMLIT ====================

def main():
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = PixelCarGame()
    
    game = st.session_state.game
    
    # HTML cho game interface
    game_html = f"""
    <div class="game-main">
        <!-- Canvas container -->
        <div class="canvas-container">
            <canvas id="game-canvas"></canvas>
        </div>
        
        <!-- Game UI -->
        <div class="game-ui">
            <div style="font-size: 16px; font-weight: bold; color: #4fc3f7; margin-bottom: 5px;">
                🚗 PIXEL CRASH 2D
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #4fc3f7;">🏆 {game.score:,}</span>
                <span style="color: #ff6b6b;">💥 {game.crashes}</span>
            </div>
            
            <div class="health-bar">
                <div class="health-fill" style="width: {game.player['health']}%"></div>
            </div>
            <div style="font-size: 12px; margin-top: 3px;">
                HP: {int(game.player['health'])}% | Dmg: {int(game.player['damage'])}%
            </div>
            
            <div style="margin-top: 8px; font-size: 11px; color: #aaa;">
                <div>🚗 AI Cars: {len(game.ai_cars)}</div>
                <div>⚡ Speed: {int(math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20)} km/h</div>
                <div>⏱️ Time: {int(game.game_time)}s</div>
            </div>
        </div>
        
        <!-- Mobile Controls (hidden by default) -->
        <div class="mobile-controls" id="mobile-controls">
            <div class="mobile-btn" data-key="up">↑</div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div class="mobile-btn" data-key="left">←</div>
                <div class="mobile-btn" data-key="right">→</div>
            </div>
            <div class="mobile-btn" data-key="down">↓</div>
            <div class="mobile-btn" data-key="space" style="width: 80px;">SPACE</div>
        </div>
        
        <!-- Game Over Screen -->
        <div class="game-over" id="game-over">
            <h1 style="font-size: 48px; color: #ff6b6b;">💥 GAME OVER</h1>
            <h2 style="font-size: 32px;">Score: {game.score:,}</h2>
            <h3 style="font-size: 24px;">Crashes: {game.crashes}</h3>
            <h3 style="font-size: 24px;">Time: {int(game.game_time)}s</h3>
            <button onclick="location.reload()" style="
                background: linear-gradient(45deg, #ff6b6b, #ffa500);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 25px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 20px;
                font-family: monospace;
            ">PLAY AGAIN</button>
        </div>
    </div>
    """
    
    st.markdown(game_html, unsafe_allow_html=True)
    
    # JavaScript cho game - VẼ ĐỒ HỌA PIXEL 2D
    game_js = """
    <script>
    // Khởi tạo game khi trang load
    window.addEventListener('load', function() {
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        
        // Đặt kích thước canvas
        function resizeCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        }
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Game state sẽ được cập nhật từ server
        let gameState = {
            player: {x: 500, y: 500, angle: 0, color: [0, 102, 204], width: 16, height: 32},
            ai_cars: [],
            particles: [],
            roads: [],
            buildings: [],
            obstacles: [],
            camera: {x: 500, y: 500, zoom: 2.0}
        };
        
        // Hàm vẽ pixel art car
        function drawPixelCar(x, y, angle, color, width, height, isPlayer = false) {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(angle * Math.PI / 180);
            
            // Thân xe chính (pixel style)
            ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            ctx.fillRect(-width/2, -height/2, width, height);
            
            // Viền đen cho pixel car
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.strokeRect(-width/2, -height/2, width, height);
            
            // Kính chắn gió (pixel style)
            ctx.fillStyle = 'rgba(200, 240, 255, 0.8)';
            ctx.fillRect(-width/3, -height/2 + 2, width * 2/3, height/4);
            
            // Đèn xe
            ctx.fillStyle = '#FFFF99';
            ctx.fillRect(-width/2 - 1, -height/4, 3, height/2);
            ctx.fillRect(width/2 - 2, -height/4, 3, height/2);
            
            // Nếu là player, thêm hiệu ứng đặc biệt
            if (isPlayer) {
                ctx.strokeStyle = '#FFFF00';
                ctx.lineWidth = 3;
                ctx.strokeRect(-width/2, -height/2, width, height);
            }
            
            ctx.restore();
        }
        
        // Hàm vẽ pixel building
        function drawPixelBuilding(x, y, width, height, color, windowColor) {
            ctx.save();
            
            // Tòa nhà chính
            ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            ctx.fillRect(x - width/2, y - height/2, width, height);
            
            // Viền đen
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.strokeRect(x - width/2, y - height/2, width, height);
            
            // Cửa sổ pixel
            ctx.fillStyle = `rgb(${windowColor[0]}, ${windowColor[1]}, ${windowColor[2]})`;
            const windowSize = 4;
            const windowSpacing = 8;
            
            for (let wx = x - width/2 + windowSpacing; wx < x + width/2 - windowSpacing; wx += windowSpacing) {
                for (let wy = y - height/2 + windowSpacing; wy < y + height/2 - windowSpacing; wy += windowSpacing) {
                    if (Math.random() > 0.3) { // Không vẽ cửa sổ ở tất cả các vị trí
                        ctx.fillRect(wx, wy, windowSize, windowSize);
                    }
                }
            }
            
            ctx.restore();
        }
        
        // Hàm vẽ pixel obstacle
        function drawPixelObstacle(x, y, size, color, type) {
            ctx.save();
            
            ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            
            if (type === 'cone') {
                // Hình nón pixel
                ctx.beginPath();
                ctx.moveTo(x, y - size/2);
                ctx.lineTo(x + size/2, y + size/2);
                ctx.lineTo(x - size/2, y + size/2);
                ctx.closePath();
                ctx.fill();
            } else if (type === 'barrel') {
                // Thùng pixel
                ctx.beginPath();
                ctx.arc(x, y, size/2, 0, Math.PI * 2);
                ctx.fill();
                // Vạch ngang
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(x - size/2, y);
                ctx.lineTo(x + size/2, y);
                ctx.stroke();
            } else {
                // Khối vuông pixel
                ctx.fillRect(x - size/2, y - size/2, size, size);
            }
            
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 1;
            ctx.stroke();
            
            ctx.restore();
        }
        
        // Hàm vẽ pixel particle
        function drawPixelParticle(x, y, size, color, life) {
            ctx.save();
            
            ctx.globalAlpha = life;
            ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            ctx.fillRect(x - size/2, y - size/2, size, size);
            
            // Hiệu ứng pixel sáng
            if (life > 0.7) {
                ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
                ctx.fillRect(x - size/4, y - size/4, size/2, size/2);
            }
            
            ctx.restore();
        }
        
        // Hàm vẽ đường pixel
        function drawPixelRoad(x, y, width, height, color) {
            ctx.save();
            
            // Mặt đường
            ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
            ctx.fillRect(x - width/2, y - height/2, width, height);
            
            // Vạch kẻ đường (pixel style)
            ctx.fillStyle = '#FFF';
            const lineWidth = 4;
            const lineSpacing = 20;
            
            if (width > height) { // Đường ngang
                for (let lx = x - width/2 + 20; lx < x + width/2 - 20; lx += lineSpacing) {
                    ctx.fillRect(lx, y - lineWidth/2, 10, lineWidth);
                }
            } else { // Đường dọc
                for (let ly = y - height/2 + 20; ly < y + height/2 - 20; ly += lineSpacing) {
                    ctx.fillRect(x - lineWidth/2, ly, lineWidth, 10);
                }
            }
            
            ctx.restore();
        }
        
        // Hàm chuyển tọa độ thế giới sang tọa độ màn hình
        function worldToScreen(wx, wy, cameraX, cameraY, zoom, canvasWidth, canvasHeight) {
            const screenX = (wx - cameraX) * zoom + canvasWidth / 2;
            const screenY = (wy - cameraY) * zoom + canvasHeight / 2;
            return {x: screenX, y: screenY};
        }
        
        // Hàm vẽ chính
        function drawGame() {
            // Xóa canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Vẽ nền trời pixel
            const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
            gradient.addColorStop(0, '#1a1a2e');
            gradient.addColorStop(1, '#16213e');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Vẽ các phần tử game
            const camera = gameState.camera;
            const zoom = camera.zoom || 2.0;
            
            // Vẽ đường
            if (gameState.roads) {
                gameState.roads.forEach(road => {
                    const pos = worldToScreen(road.x, road.y, camera.x, camera.y, zoom, canvas.width, canvas.height);
                    drawPixelRoad(pos.x, pos.y, road.width * zoom, road.height * zoom, road.color);
                });
            }
            
            // Vẽ tòa nhà
            if (gameState.buildings) {
                gameState.buildings.forEach(building => {
                    const pos = worldToScreen(building.x, building.y, camera.x, camera.y, zoom, canvas.width, canvas.height);
                    if (pos.x > -100 && pos.x < canvas.width + 100 && pos.y > -100 && pos.y < canvas.height + 100) {
                        drawPixelBuilding(
                            pos.x, pos.y, 
                            building.width * zoom, 
                            building.height * zoom, 
                            building.color, 
                            building.window_color || [200, 200, 255]
                        );
                    }
                });
            }
            
            // Vẽ vật cản
            if (gameState.obstacles) {
                gameState.obstacles.forEach(obstacle => {
                    const pos = worldToScreen(obstacle.x, obstacle.y, camera.x, camera.y, zoom, canvas.width, canvas.height);
                    if (pos.x > -50 && pos.x < canvas.width + 50 && pos.y > -50 && pos.y < canvas.height + 50) {
                        drawPixelObstacle(
                            pos.x, pos.y,
                            obstacle.size * zoom,
                            obstacle.color,
                            obstacle.type
                        );
                    }
                });
            }
            
            // Vẽ xe AI
            if (gameState.ai_cars) {
                gameState.ai_cars.forEach(car => {
                    const pos = worldToScreen(car.x, car.y, camera.x, camera.y, zoom, canvas.width, canvas.height);
                    if (pos.x > -100 && pos.x < canvas.width + 100 && pos.y > -100 && pos.y < canvas.height + 100) {
                        drawPixelCar(
                            pos.x, pos.y,
                            car.angle,
                            car.color,
                            car.width * zoom,
                            car.height * zoom,
                            false
                        );
                    }
                });
            }
            
            // Vẽ particles
            if (gameState.particles) {
                gameState.particles.forEach(particle => {
                    const pos = worldToScreen(particle.x, particle.y, camera.x, camera.y, zoom, canvas.width, canvas.height);
                    if (pos.x > -20 && pos.x < canvas.width + 20 && pos.y > -20 && pos.y < canvas.height + 20) {
                        drawPixelParticle(
                            pos.x, pos.y,
                            particle.size * zoom * particle.life,
                            particle.color,
                            particle.life
                        );
                    }
                });
            }
            
            // Vẽ player car (luôn vẽ)
            const player = gameState.player;
            const playerPos = worldToScreen(player.x, player.y, camera.x, camera.y, zoom, canvas.width, canvas.height);
            drawPixelCar(
                playerPos.x, playerPos.y,
                player.angle,
                player.color,
                player.width * zoom,
                player.height * zoom,
                true
            );
        }
        
        // Game loop để cập nhật và vẽ
        let lastUpdate = Date.now();
        
        function gameLoop() {
            const now = Date.now();
            const dt = Math.min(0.1, (now - lastUpdate) / 1000);
            lastUpdate = now;
            
            // Gửi yêu cầu cập nhật game state
            fetch(window.location.href, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'update', dt: dt})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Cập nhật game state
                    gameState = data.game_state;
                    
                    // Cập nhật UI
                    if (data.ui_update) {
                        const ui = document.querySelector('.game-ui');
                        if (ui) {
                            ui.innerHTML = `
                                <div style="font-size: 16px; font-weight: bold; color: #4fc3f7; margin-bottom: 5px;">
                                    🚗 PIXEL CRASH 2D
                                </div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                    <span style="color: #4fc3f7;">🏆 ${data.ui_update.score.toLocaleString()}</span>
                                    <span style="color: #ff6b6b;">💥 ${data.ui_update.crashes}</span>
                                </div>
                                <div class="health-bar">
                                    <div class="health-fill" style="width: ${data.ui_update.health}%"></div>
                                </div>
                                <div style="font-size: 12px; margin-top: 3px;">
                                    HP: ${Math.floor(data.ui_update.health)}% | Dmg: ${Math.floor(data.ui_update.damage)}%
                                </div>
                                <div style="margin-top: 8px; font-size: 11px; color: #aaa;">
                                    <div>🚗 AI Cars: ${data.ui_update.ai_count}</div>
                                    <div>⚡ Speed: ${Math.floor(data.ui_update.speed)} km/h</div>
                                    <div>⏱️ Time: ${Math.floor(data.ui_update.time)}s</div>
                                </div>
                            `;
                        }
                        
                        // Hiển thị game over nếu cần
                        if (!data.ui_update.game_running) {
                            document.getElementById('game-over').style.display = 'flex';
                        }
                    }
                    
                    // Vẽ game
                    drawGame();
                }
            })
            .catch(error => console.error('Error:', error));
            
            requestAnimationFrame(gameLoop);
        }
        
        // Bắt đầu game loop
        gameLoop();
        
        // Xử lý bàn phím
        document.addEventListener('keydown', (e) => {
            const keyMap = {
                'ArrowUp': 'up', 'w': 'up', 'W': 'up',
                'ArrowDown': 'down', 's': 'down', 'S': 'down',
                'ArrowLeft': 'left', 'a': 'left', 'A': 'left',
                'ArrowRight': 'right', 'd': 'right', 'D': 'right',
                ' ': 'space'
            };
            
            if (keyMap[e.key]) {
                e.preventDefault();
                fetch(window.location.href, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'key', key: keyMap[e.key], state: 'down'})
                });
            }
        });
        
        document.addEventListener('keyup', (e) => {
            const keyMap = {
                'ArrowUp': 'up', 'w': 'up', 'W': 'up',
                'ArrowDown': 'down', 's': 'down', 'S': 'down',
                'ArrowLeft': 'left', 'a': 'left', 'A': 'left',
                'ArrowRight': 'right', 'd': 'right', 'D': 'right',
                ' ': 'space'
            };
            
            if (keyMap[e.key]) {
                e.preventDefault();
                fetch(window.location.href, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'key', key: keyMap[e.key], state: 'up'})
                });
            }
        });
        
        // Xử lý mobile controls
        const mobileControls = document.getElementById('mobile-controls');
        const buttons = mobileControls.querySelectorAll('.mobile-btn');
        
        buttons.forEach(btn => {
            const key = btn.getAttribute('data-key');
            
            btn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                fetch(window.location.href, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'key', key: key, state: 'down'})
                });
                btn.style.transform = 'scale(0.9)';
                btn.style.opacity = '0.8';
            });
            
            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                fetch(window.location.href, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'key', key: key, state: 'up'})
                });
                btn.style.transform = '';
                btn.style.opacity = '';
            });
        });
        
        // Phát hiện thiết bị di động
        function detectMobile() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                   (window.innerWidth <= 768);
        }
        
        if (detectMobile()) {
            mobileControls.style.display = 'flex';
        }
    });
    </script>
    """
    
    st.markdown(game_js, unsafe_allow_html=True)
    
    # Xử lý các request từ JavaScript
    if st.rerun:
        try:
            # Lấy data từ request (giả lập)
            current_time = time.time()
            dt = current_time - game.last_update
            
            if dt > 0.016:  # ~60 FPS
                game.update(dt)
                game.last_update = current_time
                
                # Prepare response
                response = {
                    'success': True,
                    'game_state': {
                        'player': game.player,
                        'ai_cars': game.ai_cars,
                        'particles': game.particles,
                        'roads': game.roads,
                        'buildings': game.buildings,
                        'obstacles': game.obstacles,
                        'camera': {
                            'x': game.camera_x,
                            'y': game.camera_y,
                            'zoom': game.camera_zoom
                        }
                    },
                    'ui_update': {
                        'score': game.score,
                        'crashes': game.crashes,
                        'health': game.player['health'],
                        'damage': game.player['damage'],
                        'ai_count': len(game.ai_cars),
                        'speed': math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20,
                        'time': game.game_time,
                        'game_running': game.game_running
                    }
                }
                
                # Force rerun để cập nhật
                st.rerun()
        except:
            pass

if __name__ == "__main__":
    main()
