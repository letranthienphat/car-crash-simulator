import streamlit as st
import math
import random
import time

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="Car Crash Simulator 2D",
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
    .game-container {
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
    
    /* Canvas */
    #game-canvas {
        display: block;
        width: 100%;
        height: 100%;
        background: #0a0a1a;
    }
    
    /* UI overlay */
    .game-ui {
        position: absolute;
        top: 20px;
        left: 20px;
        z-index: 100;
        background: rgba(0, 0, 0, 0.8);
        padding: 15px;
        border-radius: 10px;
        color: white;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        width: 200px;
        border: 2px solid #00aaff;
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
    }
</style>
""", unsafe_allow_html=True)

# ==================== HỆ THỐNG GAME ĐƠN GIẢN ====================

class SimpleCarGame:
    def __init__(self):
        # Player car - đơn giản hóa
        self.player = {
            'x': 400,
            'y': 300,
            'vx': 0,
            'vy': 0,
            'angle': 0,
            'health': 100,
            'color': '#0066ff',
            'width': 20,
            'height': 40
        }
        
        # AI cars
        self.ai_cars = []
        self.particles = []
        
        # Game stats - chỉ dùng MỘT biến cho crashes
        self.score = 0
        self.crashes = 0  # CHỈ DÙNG crashes, KHÔNG DÙNG total_crashes
        self.game_time = 0
        
        # Input state
        if 'keys' not in st.session_state:
            st.session_state.keys = {
                'up': False, 'down': False, 'left': False, 'right': False,
                'w': False, 'a': False, 's': False, 'd': False
            }
        
        # Tạo AI cars
        self.create_ai_cars(5)
    
    def create_ai_cars(self, count):
        colors = ['#ff0000', '#00ff00', '#ffff00', '#ff8800', '#ff00ff']
        for i in range(count):
            self.ai_cars.append({
                'x': random.randint(100, 700),
                'y': random.randint(100, 500),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'angle': random.uniform(0, 360),
                'color': colors[i % len(colors)],
                'width': 20,
                'height': 40,
                'health': 100
            })
    
    def update(self, dt):
        # Cập nhật player
        self.update_player(dt)
        
        # Cập nhật AI
        self.update_ai(dt)
        
        # Cập nhật particles
        self.update_particles(dt)
        
        # Cập nhật thời gian
        self.game_time += dt
        
        # Kiểm tra va chạm
        self.check_collisions()
    
    def update_player(self, dt):
        keys = st.session_state.keys
        
        # Tăng tốc
        if keys.get('up') or keys.get('w'):
            rad = math.radians(self.player['angle'])
            self.player['vx'] += math.cos(rad) * 0.3
            self.player['vy'] += math.sin(rad) * 0.3
        
        # Phanh
        if keys.get('down') or keys.get('s'):
            self.player['vx'] *= 0.9
            self.player['vy'] *= 0.9
        
        # Lái
        if keys.get('left') or keys.get('a'):
            self.player['angle'] -= 4
        if keys.get('right') or keys.get('d'):
            self.player['angle'] += 4
        
        # Giới hạn tốc độ
        speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
        if speed > 6:
            scale = 6 / speed
            self.player['vx'] *= scale
            self.player['vy'] *= scale
        
        # Cập nhật vị trí
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Giữ trong màn hình
        self.player['x'] = max(50, min(750, self.player['x']))
        self.player['y'] = max(50, min(550, self.player['y']))
        
        # Ma sát
        self.player['vx'] *= 0.98
        self.player['vy'] *= 0.98
    
    def update_ai(self, dt):
        for car in self.ai_cars:
            # Di chuyển ngẫu nhiên đơn giản
            car['vx'] += random.uniform(-0.1, 0.1)
            car['vy'] += random.uniform(-0.1, 0.1)
            
            # Giới hạn tốc độ
            speed = math.sqrt(car['vx']**2 + car['vy']**2)
            if speed > 3:
                scale = 3 / speed
                car['vx'] *= scale
                car['vy'] *= scale
            
            # Cập nhật vị trí
            car['x'] += car['vx']
            car['y'] += car['vy']
            
            # Giữ trong màn hình
            car['x'] = max(50, min(750, car['x']))
            car['y'] = max(50, min(550, car['y']))
            
            # Cập nhật góc
            if abs(car['vx']) > 0.1 or abs(car['vy']) > 0.1:
                car['angle'] = math.degrees(math.atan2(car['vy'], car['vx']))
    
    def create_particle(self, x, y, color):
        self.particles.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(-3, 3),
            'color': color,
            'size': random.randint(2, 6),
            'life': 1.0
        })
    
    def update_particles(self, dt):
        # Cập nhật và xóa particles cũ
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.95
            p['vy'] *= 0.95
            p['life'] -= 0.03
            
            if p['life'] > 0:
                new_particles.append(p)
        self.particles = new_particles
    
    def check_collisions(self):
        # Kiểm tra va chạm với AI cars
        for car in self.ai_cars:
            dx = self.player['x'] - car['x']
            dy = self.player['y'] - car['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Khoảng cách va chạm
            if dist < 30:  # Khoảng cách đơn giản
                # Tính lực
                player_speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
                ai_speed = math.sqrt(car['vx']**2 + car['vy']**2)
                force = player_speed + ai_speed
                
                if force > 0.5:
                    # Giảm máu
                    damage = force * 10
                    self.player['health'] = max(0, self.player['health'] - damage)
                    
                    # Tạo particles
                    for _ in range(20):
                        self.create_particle(
                            (self.player['x'] + car['x']) / 2,
                            (self.player['y'] + car['y']) / 2,
                            random.choice([self.player['color'], car['color']])
                        )
                    
                    # Đẩy xe ra
                    if dist > 0:
                        push = force * 2
                        self.player['vx'] += (dx / dist) * push
                        self.player['vy'] += (dy / dist) * push
                        car['vx'] -= (dx / dist) * push
                        car['vy'] -= (dy / dist) * push
                    
                    # Cập nhật điểm
                    self.crashes += 1  # CHỈ DÙNG crashes
                    self.score += int(force * 50)

# ==================== GIAO DIỆN CHÍNH ====================

def main():
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = SimpleCarGame()
    
    game = st.session_state.game
    
    # Tạo HTML cho game
    st.markdown(f"""
    <div class="game-container">
        <canvas id="game-canvas"></canvas>
        
        <div class="game-ui">
            <div style="font-size: 18px; font-weight: bold; color: #00aaff; margin-bottom: 10px;">
                🚗 CAR CRASH SIMULATOR
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="color: #00aaff;">🏆 {game.score}</span>
                <span style="color: #ff5555;">💥 {game.crashes}</span>
            </div>
            
            <div class="health-bar">
                <div class="health-fill" style="width: {game.player['health']}%"></div>
            </div>
            <div style="font-size: 12px; margin-top: 5px;">
                HP: {int(game.player['health'])}%
            </div>
            
            <div style="margin-top: 10px; font-size: 11px; color: #aaa;">
                <div>🚗 AI Cars: {len(game.ai_cars)}</div>
                <div>⚡ Speed: {int(math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20)} km/h</div>
                <div>⏱️ Time: {int(game.game_time)}s</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # JavaScript đơn giản
    js_code = """
    <script>
    // Khởi tạo game
    window.onload = function() {
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        
        // Đặt kích thước canvas
        function resizeCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Vẽ một chiếc xe đơn giản
        function drawCar(x, y, angle, color, width, height) {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(angle * Math.PI / 180);
            
            // Thân xe
            ctx.fillStyle = color;
            ctx.fillRect(-width/2, -height/2, width, height);
            
            // Viền
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.strokeRect(-width/2, -height/2, width, height);
            
            // Kính
            ctx.fillStyle = 'rgba(200, 240, 255, 0.7)';
            ctx.fillRect(-width/3, -height/2 + 5, width * 2/3, 10);
            
            ctx.restore();
        }
        
        // Vẽ particle
        function drawParticle(x, y, size, color, life) {
            ctx.globalAlpha = life;
            ctx.fillStyle = color;
            ctx.fillRect(x - size/2, y - size/2, size, size);
            ctx.globalAlpha = 1.0;
        }
        
        // Game state tạm thời
        let gameState = {
            player: {x: 400, y: 300, angle: 0, color: '#0066ff', width: 20, height: 40},
            ai_cars: [],
            particles: []
        };
        
        // Vẽ game
        function drawGame() {
            // Xóa màn hình
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Vẽ nền đơn giản
            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Vẽ đường kẻ (đơn giản)
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            for (let i = 0; i < canvas.height; i += 40) {
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(canvas.width, i);
                ctx.stroke();
            }
            
            // Vẽ particles
            gameState.particles.forEach(p => {
                drawParticle(p.x, p.y, p.size, p.color, p.life);
            });
            
            // Vẽ AI cars
            gameState.ai_cars.forEach(car => {
                drawCar(car.x, car.y, car.angle, car.color, car.width, car.height);
            });
            
            // Vẽ player car
            drawCar(
                gameState.player.x, 
                gameState.player.y, 
                gameState.player.angle, 
                gameState.player.color, 
                gameState.player.width, 
                gameState.player.height
            );
        }
        
        // Game loop
        function gameLoop() {
            // Gửi request cập nhật
            fetch(window.location.href, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'update'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Cập nhật game state
                    gameState = data.game_state;
                    
                    // Cập nhật UI
                    document.querySelector('.game-ui').innerHTML = `
                        <div style="font-size: 18px; font-weight: bold; color: #00aaff; margin-bottom: 10px;">
                            🚗 CAR CRASH SIMULATOR
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #00aaff;">🏆 ${data.score}</span>
                            <span style="color: #ff5555;">💥 ${data.crashes}</span>
                        </div>
                        <div class="health-bar">
                            <div class="health-fill" style="width: ${data.health}%"></div>
                        </div>
                        <div style="font-size: 12px; margin-top: 5px;">
                            HP: ${Math.floor(data.health)}%
                        </div>
                        <div style="margin-top: 10px; font-size: 11px; color: #aaa;">
                            <div>🚗 AI Cars: ${data.ai_count}</div>
                            <div>⚡ Speed: ${Math.floor(data.speed)} km/h</div>
                            <div>⏱️ Time: ${Math.floor(data.time)}s</div>
                        </div>
                    `;
                    
                    // Vẽ lại
                    drawGame();
                }
            })
            .catch(err => console.error('Error:', err));
            
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
                'ArrowRight': 'right', 'd': 'right', 'D': 'right'
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
                'ArrowRight': 'right', 'd': 'right', 'D': 'right'
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
    };
    </script>
    """
    
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Hướng dẫn
    st.markdown("""
    <div style="position: fixed; bottom: 20px; right: 20px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; font-size: 12px; z-index: 1000;">
        <strong>ĐIỀU KHIỂN:</strong><br>
        <span style="color: #00aaff;">W/↑</span>: Tăng tốc<br>
        <span style="color: #00aaff;">S/↓</span>: Phanh<br>
        <span style="color: #00aaff;">A/←</span>: Trái<br>
        <span style="color: #00aaff;">D/→</span>: Phải
    </div>
    """, unsafe_allow_html=True)
    
    # Xử lý các request
    try:
        # Giả lập update game
        current_time = time.time()
        if 'last_update' not in st.session_state:
            st.session_state.last_update = current_time
        
        dt = current_time - st.session_state.last_update
        if dt > 0.016:  # ~60 FPS
            game.update(dt)
            st.session_state.last_update = current_time
            
            # Trả về data cho JavaScript
            st.json({
                'success': True,
                'game_state': {
                    'player': game.player,
                    'ai_cars': game.ai_cars,
                    'particles': game.particles
                },
                'score': game.score,
                'crashes': game.crashes,  # CHỈ DÙNG crashes
                'health': game.player['health'],
                'ai_count': len(game.ai_cars),
                'speed': int(math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20),
                'time': int(game.game_time)
            })
    except Exception as e:
        # Nếu có lỗi, tạo game mới
        st.session_state.game = SimpleCarGame()
        st.rerun()

if __name__ == "__main__":
    main()
