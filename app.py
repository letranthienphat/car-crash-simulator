import streamlit as st
import math
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="Pixel Crash Simulator",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ẩn tất cả các phần tử không cần thiết của Streamlit
st.markdown("""
<style>
    /* Ẩn các phần tử mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* CSS chính cho toàn bộ trang */
    .main > div {padding: 0;}
    
    /* Container chính của game */
    .game-main-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: #000;
        margin: 0;
        padding: 0;
        overflow: hidden;
        z-index: 1;
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
    
    /* UI overlay - ĐẶT Ở GÓC TRÊN TRÁI NHỎ LẠI */
    .game-ui {
        position: absolute;
        top: 10px;
        left: 10px;
        z-index: 100;
        background: rgba(0, 0, 0, 0.7);
        padding: 15px;
        border-radius: 10px;
        color: white;
        font-family: Arial, sans-serif;
        width: 200px;  /* ĐỊNH RÕ KÍCH THƯỚC */
        max-height: 200px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        pointer-events: none; /* Không chặn các sự kiện chuột */
    }
    
    /* Mobile controls - CHỈ HIỆN KHI LÀ MOBILE */
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
        display: none; /* Mặc định ẩn */
    }
    
    .mobile-control-button {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        border: 3px solid white;
        color: white;
        font-size: 24px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        user-select: none;
        touch-action: manipulation;
    }
    
    .mobile-control-button:active {
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0.95);
    }
    
    /* Game over screen */
    .game-over {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        display: none;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        color: white;
    }
    
    /* Reset streamlit styles */
    .stApp {
        max-width: 100% !important;
        padding: 0 !important;
    }
    
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    
    /* Health bar */
    .health-bar {
        width: 100%;
        height: 20px;
        background: #333;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .health-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff00, #ff0000);
        transition: width 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HỆ THỐNG GAME ====================

class Game:
    def __init__(self):
        self.width = 1600
        self.height = 1200
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
        }
        
        self.ai_cars = []
        self.particles = []
        self.buildings = []
        self.trees = []
        self.obstacles = []
        self.roads = []
        
        self.score = 0
        self.total_crashes = 0
        self.game_time = 0
        self.camera_x = self.player['x']
        self.camera_y = self.player['y']
        self.camera_zoom = 1.5
        self.game_running = True
        self.last_update = time.time()
        
        # Khởi tạo thế giới
        self.generate_world()
        self.spawn_ai_cars(15)
        
        # Khởi tạo input
        if 'keys_pressed' not in st.session_state:
            st.session_state.keys_pressed = {
                'up': False, 'down': False, 'left': False, 'right': False, 'space': False,
                'w': False, 'a': False, 's': False, 'd': False
            }
        
        # Khởi tạo trạng thái thiết bị
        if 'is_mobile' not in st.session_state:
            st.session_state.is_mobile = False
    
    def generate_world(self):
        # Tạo đường
        for i in range(0, self.width, 150):
            self.roads.append({
                'x1': 0, 'y1': i,
                'x2': self.width, 'y2': i,
                'width': 60,
                'color': '#333333',
                'type': 'highway'
            })
            
        for i in range(0, self.height, 150):
            self.roads.append({
                'x1': i, 'y1': 0,
                'x2': i, 'y2': self.height,
                'width': 60,
                'color': '#333333',
                'type': 'highway'
            })
        
        # Tạo nhà cửa
        for _ in range(30):
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            
            # Kiểm tra không trên đường
            on_road = False
            for road in self.roads:
                if abs(x - road['x1']) < road['width']/2 + 50 or abs(y - road['y1']) < road['width']/2 + 50:
                    on_road = True
                    break
            
            if not on_road:
                self.buildings.append({
                    'x': x, 'y': y,
                    'width': random.randint(40, 80),
                    'height': random.randint(60, 120),
                    'color': random.choice(['#8B4513', '#A0522D', '#D2691E']),
                    'windows': random.randint(4, 12)
                })
        
        # Tạo vật cản
        for _ in range(20):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            
            # Chỉ đặt trên đường
            on_road = False
            for road in self.roads:
                if abs(x - road['x1']) < road['width']/2 or abs(y - road['y1']) < road['width']/2:
                    on_road = True
                    break
            
            if on_road:
                self.obstacles.append({
                    'x': x, 'y': y,
                    'size': random.randint(15, 25),
                    'color': random.choice(['#FF0000', '#FFA500', '#FFFF00']),
                    'type': random.choice(['cone', 'barrel', 'rock'])
                })
    
    def spawn_ai_cars(self, count: int):
        ai_colors = ['#FF0000', '#00FF00', '#FFFF00', '#FFA500', '#800080']
        
        for i in range(count):
            road = random.choice(self.roads)
            t = random.random()
            
            if road['type'] == 'highway':
                if random.random() > 0.5:
                    x = road['x1'] + (road['x2'] - road['x1']) * t
                    y = road['y1']
                else:
                    x = road['x1']
                    y = road['y1'] + (road['y2'] - road['y1']) * t
            else:
                x = road['x1'] + (road['x2'] - road['x1']) * t
                y = road['y1'] + (road['y2'] - road['y1']) * t
            
            self.ai_cars.append({
                'id': i,
                'x': x, 'y': y,
                'vx': 0, 'vy': 0,
                'angle': random.uniform(0, 360),
                'health': 100,
                'damage': 0,
                'color': random.choice(ai_colors),
                'width': 25,
                'height': 45,
                'max_speed': random.uniform(3, 6),
                'acceleration': 0.1,
                'target_x': random.uniform(0, self.width),
                'target_y': random.uniform(0, self.height),
                'ai_timer': 0
            })
    
    def update(self, dt: float):
        if not self.game_running:
            return
        
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
        self.player['x'] = max(50, min(self.width - 50, self.player['x']))
        self.player['y'] = max(50, min(self.height - 50, self.player['y']))
        
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
                3
            )
    
    def update_ai_cars(self, dt: float):
        for ai in self.ai_cars:
            ai['ai_timer'] += dt
            
            # Đổi hướng mỗi 2-5 giây
            if ai['ai_timer'] > random.uniform(2, 5):
                ai['target_x'] = random.uniform(0, self.width)
                ai['target_y'] = random.uniform(0, self.height)
                ai['ai_timer'] = 0
            
            # Di chuyển về target
            dx = ai['target_x'] - ai['x']
            dy = ai['target_y'] - ai['y']
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 20:
                ai['vx'] += (dx / dist) * ai['acceleration']
                ai['vy'] += (dy / dist) * ai['acceleration']
                
                # Cập nhật góc
                target_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = (target_angle - ai['angle']) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                ai['angle'] += angle_diff * 0.1
            
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
            ai['x'] = max(50, min(self.width - 50, ai['x']))
            ai['y'] = max(50, min(self.height - 50, ai['y']))
            
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
            'gravity': 0.3,
            'friction': 0.98
        })
    
    def update_particles(self, dt: float):
        for particle in self.particles[:]:
            particle['vy'] += particle['gravity']
            particle['vx'] *= particle['friction']
            particle['vy'] *= particle['friction']
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.02
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def check_collisions(self):
        # Va chạm với AI cars
        for ai in self.ai_cars:
            dx = self.player['x'] - ai['x']
            dy = self.player['y'] - ai['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < (self.player['width'] + ai['width']) / 2:
                # Tính lực va chạm
                player_speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
                ai_speed = math.sqrt(ai['vx']**2 + ai['vy']**2)
                force = player_speed + ai_speed
                
                if force > 1:
                    # Damage
                    damage = force * 3
                    self.player['health'] = max(0, self.player['health'] - damage)
                    self.player['damage'] = min(100, self.player['damage'] + damage)
                    ai['health'] = max(0, ai['health'] - damage)
                    ai['damage'] = min(100, ai['damage'] + damage)
                    
                    # Tạo particles
                    for _ in range(int(force * 5)):
                        self.create_particle(
                            (self.player['x'] + ai['x']) / 2,
                            (self.player['y'] + ai['y']) / 2,
                            random.choice([self.player['color'], ai['color']]),
                            random.uniform(-force, force),
                            random.uniform(-force, force),
                            random.randint(2, 5)
                        )
                    
                    # Đẩy xe ra
                    if distance > 0:
                        push = force * 0.5
                        self.player['vx'] += (dx / distance) * push
                        self.player['vy'] += (dy / distance) * push
                        ai['vx'] -= (dx / distance) * push
                        ai['vy'] -= (dy / distance) * push
                    
                    # Điểm
                    self.total_crashes += 1
                    self.score += int(force * 10)
                    
                    # Respawn AI nếu bị phá hủy
                    if ai['health'] <= 0:
                        self.spawn_ai_cars(1)
                        self.ai_cars.remove(ai)
                        self.score += 100

# ==================== GIAO DIỆN CHÍNH ====================

def main():
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = Game()
    
    game = st.session_state.game
    
    # Phát hiện thiết bị
    st.markdown("""
    <script>
    // Phát hiện mobile
    function detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (window.innerWidth <= 768);
    }
    
    // Hiển thị mobile controls nếu là mobile
    if (detectMobile()) {
        document.documentElement.style.setProperty('--show-mobile-controls', 'block');
        localStorage.setItem('is_mobile', 'true');
    } else {
        document.documentElement.style.setProperty('--show-mobile-controls', 'none');
        localStorage.setItem('is_mobile', 'false');
    }
    
    // Gửi event cho Streamlit biết
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: { is_mobile: detectMobile() }
    }, '*');
    </script>
    """, unsafe_allow_html=True)
    
    # Container chính của game - CHỈ CÓ GAME
    game_html = f"""
    <div class="game-main-container">
        <!-- Canvas cho game -->
        <div class="canvas-container">
            <canvas id="game-canvas"></canvas>
        </div>
        
        <!-- UI overlay - NHỎ Ở GÓC TRÊN TRÁI -->
        <div class="game-ui">
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">🚗 PIXEL CRASH</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #4fc3f7;">🏆 {game.score:,}</span>
                <span style="color: #ff6b6b;">💥 {game.total_crashes}</span>
            </div>
            
            <div class="health-bar">
                <div class="health-fill" style="width: {game.player['health']}%"></div>
            </div>
            <div style="font-size: 12px; margin-top: 3px;">
                HP: {int(game.player['health'])}% | Dmg: {int(game.player['damage'])}%
            </div>
            
            <div style="margin-top: 8px; font-size: 11px; color: #aaa;">
                <div>🚗 AI: {len(game.ai_cars)}</div>
                <div>⚡ {int(math.sqrt(game.player['vx']**2 + game.player['vy']**2)*20)} km/h</div>
                <div>⏱️ {int(game.game_time)}s</div>
            </div>
        </div>
        
        <!-- Mobile controls - CHỈ HIỆN KHI LÀ MOBILE -->
        <div class="mobile-controls" id="mobile-controls">
            <div class="mobile-control-button" data-key="up">↑</div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div class="mobile-control-button" data-key="left">←</div>
                <div class="mobile-control-button" data-key="right">→</div>
            </div>
            <div class="mobile-control-button" data-key="down">↓</div>
            <div class="mobile-control-button" data-key="space" style="width: 90px;">SPACE</div>
        </div>
        
        <!-- Game over screen -->
        <div class="game-over" id="game-over">
            <h1>💥 GAME OVER</h1>
            <h2>Điểm: {game.score:,}</h2>
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
            ">CHƠI LẠI</button>
        </div>
    </div>
    """
    
    st.markdown(game_html, unsafe_allow_html=True)
    
    # JavaScript cho game
    game_js = f"""
    <script>
    // Khởi tạo game khi trang load xong
    window.addEventListener('load', function() {{
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        
        // Đặt kích thước canvas bằng với container
        function resizeCanvas() {{
            const container = canvas.parentElement;
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
        }}
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Game state
        const gameState = {{
            player: {json.dumps(game.player)},
            ai_cars: {json.dumps(game.ai_cars)},
            particles: {json.dumps(game.particles)},
            buildings: {json.dumps(game.buildings)},
            obstacles: {json.dumps(game.obstacles)},
            roads: {json.dumps(game.roads)},
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
                if (road.type === 'highway') {{
                    ctx.setLineDash([20 * gameState.camera.zoom, 10 * gameState.camera.zoom]);
                    ctx.lineWidth = 2 * gameState.camera.zoom;
                    ctx.strokeStyle = '#FFFFFF';
                    
                    const dx = end.x - start.x;
                    const dy = end.y - start.y;
                    const length = Math.sqrt(dx * dx + dy * dy);
                    
                    if (length > 0) {{
                        // Vẽ đường giữa
                        ctx.beginPath();
                        ctx.moveTo(start.x + dx/2, start.y + dy/2);
                        ctx.lineTo(end.x - dx/2, end.y - dy/2);
                        ctx.stroke();
                    }}
                    ctx.setLineDash([]);
                }}
            }});
        }}
        
        // Vẽ nhà
        function drawBuildings() {{
            gameState.buildings.forEach(building => {{
                const pos = worldToScreen(building.x, building.y);
                const width = building.width * gameState.camera.zoom;
                const height = building.height * gameState.camera.zoom;
                
                // Vẽ tòa nhà
                ctx.fillStyle = building.color;
                ctx.fillRect(pos.x - width/2, pos.y - height/2, width, height);
                
                // Vẽ cửa sổ
                ctx.fillStyle = '#C8E0FF';
                const windowSize = 5 * gameState.camera.zoom;
                for (let i = 0; i < building.windows; i++) {{
                    const wx = pos.x - width/3 + Math.random() * (width * 2/3);
                    const wy = pos.y - height/3 + Math.random() * (height * 2/3);
                    ctx.fillRect(wx, wy, windowSize, windowSize);
                }}
                
                // Viền
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                ctx.strokeRect(pos.x - width/2, pos.y - height/2, width, height);
            }});
        }}
        
        // Vẽ vật cản
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
                    ctx.fillRect(pos.x - size/2, pos.y - size/2, size, size);
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
                
                ctx.restore();
            }});
        }}
        
        // Vẽ xe player
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
            
            // Đèn
            ctx.fillStyle = '#FFFFC8';
            ctx.fillRect(-width/2 - 3, -height/4, 6, height/2);
            ctx.fillRect(width/2 - 3, -height/4, 6, height/2);
            
            ctx.restore();
        }}
        
        // Vẽ particles
        function drawParticles() {{
            gameState.particles.forEach(particle => {{
                const pos = worldToScreen(particle.x, particle.y);
                const size = particle.size * gameState.camera.zoom * particle.life;
                
                if (size > 0) {{
                    ctx.globalAlpha = particle.life;
                    ctx.fillStyle = particle.color;
                    ctx.fillRect(pos.x - size/2, pos.y - size/2, size, size);
                    ctx.globalAlpha = 1.0;
                }}
            }});
        }}
        
        // Vẽ nền
        function drawBackground() {{
            // Nền trời
            const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
            gradient.addColorStop(0, '#87CEEB');
            gradient.addColorStop(1, '#4682B4');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }}
        
        // Hàm vẽ chính
        function draw() {{
            // Xóa canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Vẽ các thành phần
            drawBackground();
            drawRoads();
            drawBuildings();
            drawObstacles();
            drawAICars();
            drawPlayerCar();
            drawParticles();
        }}
        
        // Vẽ frame đầu tiên
        draw();
        
        // Game loop
        let lastTime = 0;
        function gameLoop(currentTime) {{
            const dt = Math.min(0.1, (currentTime - lastTime) / 1000);
            lastTime = currentTime;
            
            // Gửi request cập nhật game state
            fetch(window.location.href, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{ dt: dt }})
            }})
            .then(response => response.json())
            .then(data => {{
                // Cập nhật UI
                document.querySelector('.game-ui').innerHTML = `
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">🚗 PIXEL CRASH</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #4fc3f7;">🏆 ${{data.score.toLocaleString()}}</span>
                        <span style="color: #ff6b6b;">💥 ${{data.total_crashes}}</span>
                    </div>
                    <div class="health-bar">
                        <div class="health-fill" style="width: ${{data.player.health}}%"></div>
                    </div>
                    <div style="font-size: 12px; margin-top: 3px;">
                        HP: ${{Math.floor(data.player.health)}}% | Dmg: ${{Math.floor(data.player.damage)}}%
                    </div>
                    <div style="margin-top: 8px; font-size: 11px; color: #aaa;">
                        <div>🚗 AI: ${{data.ai_cars.length}}</div>
                        <div>⚡ ${{Math.floor(Math.sqrt(data.player.vx**2 + data.player.vy**2)*20)}} km/h</div>
                        <div>⏱️ ${{Math.floor(data.game_time)}}s</div>
                    </div>
                `;
                
                // Cập nhật game state
                Object.assign(gameState, data);
                
                // Hiển thị game over nếu cần
                if (!data.game_running) {{
                    document.getElementById('game-over').style.display = 'flex';
                }}
                
                // Vẽ lại
                draw();
            }})
            .catch(error => console.error('Error:', error));
            
            requestAnimationFrame(gameLoop);
        }}
        
        // Bắt đầu game loop
        requestAnimationFrame(gameLoop);
        
        // Xử lý bàn phím
        document.addEventListener('keydown', (e) => {{
            const keyMap = {{
                'ArrowUp': 'up', 'w': 'up', 'W': 'up',
                'ArrowDown': 'down', 's': 'down', 'S': 'down',
                'ArrowLeft': 'left', 'a': 'left', 'A': 'left',
                'ArrowRight': 'right', 'd': 'right', 'D': 'right',
                ' ': 'space'
            }};
            
            if (keyMap[e.key]) {{
                e.preventDefault();
                // Gửi key press tới Streamlit
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: keyMap[e.key], action: 'down' }})
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
                e.preventDefault();
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: keyMap[e.key], action: 'up' }})
                }});
            }}
        }});
        
        // Xử lý mobile controls
        const mobileControls = document.getElementById('mobile-controls');
        const buttons = mobileControls.querySelectorAll('.mobile-control-button');
        
        buttons.forEach(button => {{
            const key = button.getAttribute('data-key');
            
            // Touch events
            button.addEventListener('touchstart', (e) => {{
                e.preventDefault();
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key, action: 'down' }})
                }});
                button.style.transform = 'scale(0.95)';
                button.style.opacity = '0.8';
            }});
            
            button.addEventListener('touchend', (e) => {{
                e.preventDefault();
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key, action: 'up' }})
                }});
                button.style.transform = '';
                button.style.opacity = '';
            }});
            
            // Mouse events (cho cảm ứng trên desktop)
            button.addEventListener('mousedown', (e) => {{
                e.preventDefault();
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key, action: 'down' }})
                }});
            }});
            
            button.addEventListener('mouseup', (e) => {{
                e.preventDefault();
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key, action: 'up' }})
                }});
            }});
            
            button.addEventListener('mouseleave', (e) => {{
                e.preventDefault();
                fetch(window.location.href, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key, action: 'up' }})
                }});
            }});
        }});
        
        // Hiển thị mobile controls nếu là mobile
        if (localStorage.getItem('is_mobile') === 'true') {{
            mobileControls.style.display = 'flex';
        }} else {{
            mobileControls.style.display = 'none';
        }}
    }});
    </script>
    """
    
    st.markdown(game_js, unsafe_allow_html=True)
    
    # Hướng dẫn điều khiển (chỉ hiện ở dưới cùng)
    st.markdown("""
    <div style="position: fixed; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; font-size: 12px; z-index: 1000;">
        <strong>ĐIỀU KHIỂN:</strong><br>
        <span style="color: #4fc3f7;">W/↑</span>: Tăng tốc | 
        <span style="color: #4fc3f7;">S/↓</span>: Phanh<br>
        <span style="color: #4fc3f7;">A/←</span>: Trái | 
        <span style="color: #4fc3f7;">D/→</span>: Phải<br>
        <span style="color: #4fc3f7;">Space</span>: Phanh tay
    </div>
    """, unsafe_allow_html=True)
    
    # Game update loop
    if game.game_running:
        current_time = time.time()
        dt = current_time - game.last_update
        
        if dt > 0.016:  # ~60 FPS
            game.update(dt)
            game.last_update = current_time
            
            # Force rerun để cập nhật UI
            st.rerun()

# Chạy app
if __name__ == "__main__":
    main()
