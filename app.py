import streamlit as st
import math
import random
import time

# ==================== CẤU HÌNH ====================
st.set_page_config(
    page_title="Car Crash Simulator 2D",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS đơn giản
st.markdown("""
<style>
    /* Ẩn Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {max-width: 100%; padding: 0;}
    
    /* Game container */
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
        background: #1a1a2e;
    }
    
    /* UI */
    .game-ui {
        position: absolute;
        top: 20px;
        left: 20px;
        z-index: 100;
        background: rgba(0, 0, 0, 0.8);
        padding: 15px;
        border-radius: 10px;
        color: white;
        font-family: monospace;
        font-size: 14px;
        width: 200px;
        border: 2px solid #4fc3f7;
    }
    
    /* Health bar */
    .health-bar {
        width: 100%;
        height: 15px;
        background: #333;
        border-radius: 8px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .health-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff00, #ff0000);
    }
</style>
""", unsafe_allow_html=True)

# ==================== GAME CLASS ====================

class CarGame:
    def __init__(self):
        # Player
        self.player = {
            'x': 400, 'y': 300,
            'vx': 0, 'vy': 0,
            'angle': 0,
            'health': 100,
            'color': '#0066ff',
            'width': 20,
            'height': 40
        }
        
        # AI Cars
        self.ai_cars = []
        self.particles = []
        
        # Game stats - CHỈ DÙNG 1 BIẾN crashes
        self.score = 0
        self.crashes = 0  # TÊN BIẾN DUY NHẤT
        self.game_time = 0
        
        # Tạo AI cars
        self.create_ai_cars(5)
        
        # Khởi tạo input
        if 'keys' not in st.session_state:
            st.session_state.keys = {
                'up': False, 'down': False, 'left': False, 'right': False,
                'w': False, 'a': False, 's': False, 'd': False
            }
    
    def create_ai_cars(self, count):
        colors = ['#ff0000', '#00ff00', '#ffff00', '#ff8800', '#ff00ff']
        for _ in range(count):
            self.ai_cars.append({
                'x': random.randint(100, 700),
                'y': random.randint(100, 500),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'angle': random.uniform(0, 360),
                'color': random.choice(colors),
                'width': 20,
                'height': 40,
                'health': 100
            })
    
    def update(self, dt):
        # Update player
        self.update_player(dt)
        
        # Update AI
        self.update_ai(dt)
        
        # Update particles
        self.update_particles(dt)
        
        # Update time
        self.game_time += dt
        
        # Check collisions
        self.check_collisions()
    
    def update_player(self, dt):
        keys = st.session_state.keys
        
        # Acceleration
        if keys.get('up') or keys.get('w'):
            rad = math.radians(self.player['angle'])
            self.player['vx'] += math.cos(rad) * 0.3
            self.player['vy'] += math.sin(rad) * 0.3
        
        # Brake
        if keys.get('down') or keys.get('s'):
            self.player['vx'] *= 0.9
            self.player['vy'] *= 0.9
        
        # Steering
        if keys.get('left') or keys.get('a'):
            self.player['angle'] -= 4
        if keys.get('right') or keys.get('d'):
            self.player['angle'] += 4
        
        # Speed limit
        speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
        if speed > 6:
            scale = 6 / speed
            self.player['vx'] *= scale
            self.player['vy'] *= scale
        
        # Update position
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Keep in bounds
        self.player['x'] = max(50, min(750, self.player['x']))
        self.player['y'] = max(50, min(550, self.player['y']))
        
        # Friction
        self.player['vx'] *= 0.98
        self.player['vy'] *= 0.98
    
    def update_ai(self, dt):
        for car in self.ai_cars:
            # Simple AI movement
            car['vx'] += random.uniform(-0.1, 0.1)
            car['vy'] += random.uniform(-0.1, 0.1)
            
            # Speed limit
            speed = math.sqrt(car['vx']**2 + car['vy']**2)
            if speed > 3:
                scale = 3 / speed
                car['vx'] *= scale
                car['vy'] *= scale
            
            # Update position
            car['x'] += car['vx']
            car['y'] += car['vy']
            
            # Keep in bounds
            car['x'] = max(50, min(750, car['x']))
            car['y'] = max(50, min(550, car['y']))
            
            # Update angle
            if abs(car['vx']) > 0.1 or abs(car['vy']) > 0.1:
                car['angle'] = math.degrees(math.atan2(car['vy'], car['vx']))
    
    def create_particle(self, x, y, color):
        self.particles.append({
            'x': x, 'y': y,
            'vx': random.uniform(-3, 3),
            'vy': random.uniform(-3, 3),
            'color': color,
            'size': random.randint(2, 6),
            'life': 1.0
        })
    
    def update_particles(self, dt):
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
        # Check collisions with AI cars
        for car in self.ai_cars:
            dx = self.player['x'] - car['x']
            dy = self.player['y'] - car['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Collision distance
            if dist < 30:
                # Calculate force
                player_speed = math.sqrt(self.player['vx']**2 + self.player['vy']**2)
                ai_speed = math.sqrt(car['vx']**2 + car['vy']**2)
                force = player_speed + ai_speed
                
                if force > 0.5:
                    # Damage
                    damage = force * 10
                    self.player['health'] = max(0, self.player['health'] - damage)
                    
                    # Create particles
                    for _ in range(20):
                        self.create_particle(
                            (self.player['x'] + car['x']) / 2,
                            (self.player['y'] + car['y']) / 2,
                            random.choice([self.player['color'], car['color']])
                        )
                    
                    # Push cars apart
                    if dist > 0:
                        push = force * 2
                        self.player['vx'] += (dx / dist) * push
                        self.player['vy'] += (dy / dist) * push
                        car['vx'] -= (dx / dist) * push
                        car['vy'] -= (dy / dist) * push
                    
                    # Update score
                    self.crashes += 1
                    self.score += int(force * 50)

# ==================== MAIN APP ====================

def main():
    # Initialize game
    if 'game' not in st.session_state:
        st.session_state.game = CarGame()
        st.session_state.last_update = time.time()
    
    game = st.session_state.game
    
    # HTML for game
    st.markdown(f"""
    <div class="game-container">
        <canvas id="game-canvas"></canvas>
        
        <div class="game-ui">
            <div style="font-size: 16px; font-weight: bold; color: #4fc3f7; margin-bottom: 5px;">
                🚗 CAR CRASH SIMULATOR
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #4fc3f7;">🏆 {game.score}</span>
                <span style="color: #ff6b6b;">💥 {game.crashes}</span>
            </div>
            
            <div class="health-bar">
                <div class="health-fill" style="width: {game.player['health']}%"></div>
            </div>
            <div style="font-size: 12px; margin-top: 3px;">
                HP: {int(game.player['health'])}%
            </div>
            
            <div style="margin-top: 8px; font-size: 11px; color: #aaa;">
                <div>🚗 AI: {len(game.ai_cars)}</div>
                <div>⚡ {int(math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20)} km/h</div>
                <div>⏱️ {int(game.game_time)}s</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # JavaScript for game
    js_code = """
    <script>
    // Initialize game
    window.onload = function() {
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size
        function resizeCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Draw a car
        function drawCar(x, y, angle, color, width, height, isPlayer = false) {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(angle * Math.PI / 180);
            
            // Car body
            ctx.fillStyle = color;
            ctx.fillRect(-width/2, -height/2, width, height);
            
            // Border
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            ctx.strokeRect(-width/2, -height/2, width, height);
            
            // Windshield
            ctx.fillStyle = 'rgba(200, 240, 255, 0.8)';
            ctx.fillRect(-width/3, -height/2 + 3, width * 2/3, 8);
            
            // Player highlight
            if (isPlayer) {
                ctx.strokeStyle = '#ffff00';
                ctx.lineWidth = 3;
                ctx.strokeRect(-width/2, -height/2, width, height);
            }
            
            ctx.restore();
        }
        
        // Draw particle
        function drawParticle(x, y, size, color, life) {
            ctx.globalAlpha = life;
            ctx.fillStyle = color;
            ctx.fillRect(x - size/2, y - size/2, size, size);
            ctx.globalAlpha = 1.0;
        }
        
        // Game state
        let gameState = {
            player: {x: 400, y: 300, angle: 0, color: '#0066ff', width: 20, height: 40},
            ai_cars: [],
            particles: []
        };
        
        // Draw game
        function drawGame() {
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw background
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw road lines
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            for (let i = 0; i < canvas.height; i += 40) {
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(canvas.width, i);
                ctx.stroke();
            }
            
            // Draw particles
            gameState.particles.forEach(p => {
                drawParticle(p.x, p.y, p.size, p.color, p.life);
            });
            
            // Draw AI cars
            gameState.ai_cars.forEach(car => {
                drawCar(car.x, car.y, car.angle, car.color, car.width, car.height, false);
            });
            
            // Draw player car
            drawCar(
                gameState.player.x, 
                gameState.player.y, 
                gameState.player.angle, 
                gameState.player.color, 
                gameState.player.width, 
                gameState.player.height,
                true
            );
        }
        
        // Game loop
        function gameLoop() {
            // Update game via fetch
            fetch(window.location.href, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'update'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update game state
                    gameState = data.game_state;
                    
                    // Update UI
                    document.querySelector('.game-ui').innerHTML = `
                        <div style="font-size: 16px; font-weight: bold; color: #4fc3f7; margin-bottom: 5px;">
                            🚗 CAR CRASH SIMULATOR
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span style="color: #4fc3f7;">🏆 ${data.score}</span>
                            <span style="color: #ff6b6b;">💥 ${data.crashes}</span>
                        </div>
                        <div class="health-bar">
                            <div class="health-fill" style="width: ${data.health}%"></div>
                        </div>
                        <div style="font-size: 12px; margin-top: 3px;">
                            HP: ${Math.floor(data.health)}%
                        </div>
                        <div style="margin-top: 8px; font-size: 11px; color: #aaa;">
                            <div>🚗 AI: ${data.ai_count}</div>
                            <div>⚡ ${Math.floor(data.speed)} km/h</div>
                            <div>⏱️ ${Math.floor(data.time)}s</div>
                        </div>
                    `;
                    
                    // Draw game
                    drawGame();
                }
            })
            .catch(err => console.error('Error:', err));
            
            requestAnimationFrame(gameLoop);
        }
        
        // Start game loop
        gameLoop();
        
        // Handle keyboard
        document.addEventListener('keydown', (e) => {
            const keyMap = {
                'ArrowUp': 'up', 'w': 'up', 'W': 'up',
                'ArrowDown': 'down', 's': 'down', 'S': 'down',
                'ArrowLeft': 'left', 'a': 'left', 'A': 'left',
                'ArrowRight': 'right', 'd': 'right', 'D': 'right'
            };
            
            if (keyMap[e.key]) {
                e.preventDefault();
                st.session_state.keys[keyMap[e.key]] = true;
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
                st.session_state.keys[keyMap[e.key]] = false;
            }
        });
    };
    </script>
    """
    
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Controls help
    st.markdown("""
    <div style="position: fixed; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; font-size: 12px; z-index: 1000;">
        <strong>CONTROLS:</strong><br>
        <span style="color: #4fc3f7;">W/↑</span>: Accelerate<br>
        <span style="color: #4fc3f7;">S/↓</span>: Brake<br>
        <span style="color: #4fc3f7;">A/←</span>: Left<br>
        <span style="color: #4fc3f7;">D/→</span>: Right
    </div>
    """, unsafe_allow_html=True)
    
    # Update game logic
    try:
        current_time = time.time()
        dt = current_time - st.session_state.last_update
        
        if dt > 0.016:  # ~60 FPS
            game.update(dt)
            st.session_state.last_update = current_time
            
            # Return data for JavaScript
            st.json({
                'success': True,
                'game_state': {
                    'player': game.player,
                    'ai_cars': game.ai_cars,
                    'particles': game.particles
                },
                'score': game.score,
                'crashes': game.crashes,  # ĐÚNG TÊN BIẾN
                'health': game.player['health'],
                'ai_count': len(game.ai_cars),
                'speed': int(math.sqrt(game.player['vx']**2 + game.player['vy']**2) * 20),
                'time': int(game.game_time)
            })
    except Exception as e:
        # Reset on error
        st.session_state.game = CarGame()
        st.session_state.last_update = time.time()

if __name__ == "__main__":
    main()
