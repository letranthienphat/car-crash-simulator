import streamlit as st
import random
import time
import math

st.set_page_config(page_title="Car Crash Game", layout="wide")

# Khởi tạo session state
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'player_lane' not in st.session_state:
    st.session_state.player_lane = 2  # 1, 2, hoặc 3
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'damage' not in st.session_state:
    st.session_state.damage = 0
if 'ai_cars' not in st.session_state:
    st.session_state.ai_cars = []
if 'obstacles' not in st.session_state:
    st.session_state.obstacles = []
if 'game_time' not in st.session_state:
    st.session_state.game_time = 0

# CSS custom
st.markdown("""
<style>
    .game-container {
        background-color: #87CEEB;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .road {
        background-color: #696969;
        height: 500px;
        position: relative;
        margin: 0 auto;
        width: 300px;
        border: 5px solid #333;
    }
    .lane {
        border-right: 2px dashed white;
        height: 100%;
        position: absolute;
    }
    .player-car {
        background-color: #0066cc;
        color: white;
        width: 50px;
        height: 80px;
        position: absolute;
        bottom: 50px;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        transition: left 0.3s;
    }
    .ai-car {
        background-color: #cc0000;
        color: white;
        width: 50px;
        height: 80px;
        position: absolute;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    .obstacle {
        background-color: #ff9900;
        width: 30px;
        height: 40px;
        position: absolute;
        border-radius: 3px;
    }
    .road-line {
        background-color: white;
        height: 20px;
        width: 5px;
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
    }
    .stats {
        background-color: rgba(0,0,0,0.7);
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🚗 Car Crash Game")
    st.markdown("---")
    
    if st.button("🎮 Bắt đầu chơi", type="primary", use_container_width=True):
        st.session_state.game_started = True
        st.session_state.player_lane = 2
        st.session_state.score = 0
        st.session_state.damage = 0
        st.session_state.ai_cars = []
        st.session_state.obstacles = []
        st.session_state.game_time = time.time()
        st.rerun()
    
    if st.button("🔄 Chơi lại", use_container_width=True):
        st.session_state.game_started = False
        st.rerun()
    
    st.markdown("---")
    st.subheader("Điều khiển")
    st.markdown("""
    - **A**: Sang trái
    - **D**: Sang phải
    - **Rút lui**: Tự động tránh
    """)
    
    st.markdown("---")
    st.subheader("Luật chơi")
    st.markdown("""
    1. Tránh xe AI màu đỏ
    2. Tránh vật cản màu cam
    3. Giữ hư hại dưới 100%
    4. Tăng điểm bằng cách sống lâu
    """)

# Main game area
if not st.session_state.game_started:
    st.title("🚗 Car Crash Simulator")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center;'>
            <h2>Chào mừng đến với trò chơi!</h2>
            <p>Điều khiển xe màu xanh dương, tránh xe AI và vật cản.</p>
            <p>Nhấn <strong>Bắt đầu chơi</strong> để bắt đầu!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎮 BẮT ĐẦU CHƠI", type="primary", size="large", use_container_width=True):
            st.session_state.game_started = True
            st.session_state.game_time = time.time()
            st.rerun()

else:
    # Game đang chạy
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        # Game stats
        current_time = time.time()
        elapsed_time = int(current_time - st.session_state.game_time)
        
        st.markdown(f"""
        <div class="stats">
            <h3>📊 Thống kê</h3>
            <p>⏱️ Thời gian: {elapsed_time}s</p>
            <p>🏆 Điểm số: {st.session_state.score}</p>
            <p>⚠️ Hư hại: {st.session_state.damage}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Điều khiển
        st.markdown("<h3>🎮 Điều khiển</h3>", unsafe_allow_html=True)
        control_col1, control_col2, control_col3 = st.columns(3)
        with control_col1:
            if st.button("⬅️ Trái (A)", use_container_width=True):
                st.session_state.player_lane = max(1, st.session_state.player_lane - 1)
                st.rerun()
        with control_col2:
            if st.button("⏹️ Dừng", use_container_width=True):
                st.session_state.game_started = False
                st.rerun()
        with control_col3:
            if st.button("➡️ Phải (D)", use_container_width=True):
                st.session_state.player_lane = min(3, st.session_state.player_lane + 1)
                st.rerun()
    
    with col2:
        # Game area
        st.markdown("""
        <div class="game-container">
            <div class="road" id="road">
                <!-- Lanes -->
                <div class="lane" style="left: 100px;"></div>
                <div class="lane" style="left: 200px;"></div>
                
                <!-- Road lines (animated with JS) -->
                <div id="road-lines"></div>
                
                <!-- Player car -->
                <div class="player-car" id="player-car">
                    BẠN
                </div>
            </div>
        </div>
        
        <script>
        // Position player car
        const playerLane = """ + str(st.session_state.player_lane) + """;
        const car = document.getElementById('player-car');
        if (car) {
            const positions = [25, 125, 225];
            car.style.left = positions[playerLane - 1] + 'px';
        }
        
        // Create road lines
        const roadLines = document.getElementById('road-lines');
        if (roadLines) {
            roadLines.innerHTML = '';
            for (let i = -50; i < 550; i += 60) {
                const line = document.createElement('div');
                line.className = 'road-line';
                line.style.top = i + 'px';
                roadLines.appendChild(line);
            }
        }
        
        // Animate road lines
        let lineOffset = 0;
        function animateRoad() {
            lineOffset = (lineOffset + 5) % 60;
            const lines = document.querySelectorAll('.road-line');
            lines.forEach((line, index) => {
                const top = (index * 60 + lineOffset) % 600;
                line.style.top = top + 'px';
            });
            requestAnimationFrame(animateRoad);
        }
        
        // Add AI cars and obstacles from Python
        const road = document.getElementById('road');
        
        // AI cars
        """ + f"""
        const aiCars = {st.session_state.ai_cars};
        aiCars.forEach(car => {{
            const aiCar = document.createElement('div');
            aiCar.className = 'ai-car';
            aiCar.textContent = 'AI';
            const positions = [25, 125, 225];
            aiCar.style.left = positions[car.lane - 1] + 'px';
            aiCar.style.top = car.position + 'px';
            road.appendChild(aiCar);
        }});
        
        // Obstacles
        const obstacles = {st.session_state.obstacles};
        obstacles.forEach(obs => {{
            const obstacle = document.createElement('div');
            obstacle.className = 'obstacle';
            const positions = [35, 135, 235];
            obstacle.style.left = positions[obs.lane - 1] + 'px';
            obstacle.style.top = obs.position + 'px';
            road.appendChild(obstacle);
        }});
        """ + """
        
        animateRoad();
        </script>
        """, unsafe_allow_html=True)
    
    with col3:
        # Game log
        st.markdown("<h3>📝 Nhật ký trò chơi</h3>", unsafe_allow_html=True)
        
        # Tạo sự kiện ngẫu nhiên
        if random.random() < 0.3:
            event_type = random.choice(["ai_spawn", "obstacle_spawn", "near_miss"])
            
            if event_type == "ai_spawn" and len(st.session_state.ai_cars) < 5:
                lane = random.randint(1, 3)
                st.session_state.ai_cars.append({
                    "lane": lane,
                    "position": random.randint(-100, 50)
                })
                st.info(f"🚗 Xe AI xuất hiện ở làn {lane}")
            
            elif event_type == "obstacle_spawn" and len(st.session_state.obstacles) < 3:
                lane = random.randint(1, 3)
                st.session_state.obstacles.append({
                    "lane": lane,
                    "position": random.randint(-50, 100)
                })
                st.warning(f"⚠️ Vật cản xuất hiện ở làn {lane}")
        
        # Kiểm tra va chạm
        player_lane = st.session_state.player_lane
        
        for ai_car in st.session_state.ai_cars[:]:
            ai_car["position"] += 10  # Di chuyển AI xuống
            
            # Nếu AI đã vượt qua player
            if ai_car["position"] > 500:
                st.session_state.ai_cars.remove(ai_car)
                st.session_state.score += 10
                st.success("✅ Vượt qua xe AI! +10 điểm")
            
            # Kiểm tra va chạm
            elif (ai_car["lane"] == player_lane and 
                  400 < ai_car["position"] < 500):
                st.session_state.damage = min(100, st.session_state.damage + 20)
                st.session_state.ai_cars.remove(ai_car)
                st.error("💥 Va chạm với xe AI! +20% hư hại")
        
        for obstacle in st.session_state.obstacles[:]:
            obstacle["position"] += 8  # Di chuyển vật cản xuống
            
            # Nếu vật cản đã vượt qua player
            if obstacle["position"] > 500:
                st.session_state.obstacles.remove(obstacle)
                st.session_state.score += 5
                st.success("✅ Vượt qua vật cản! +5 điểm")
            
            # Kiểm tra va chạm
            elif (obstacle["lane"] == player_lane and 
                  420 < obstacle["position"] < 500):
                st.session_state.damage = min(100, st.session_state.damage + 15)
                st.session_state.obstacles.remove(obstacle)
                st.error("💥 Va chạm với vật cản! +15% hư hại")
        
        # Tăng điểm theo thời gian
        if random.random() < 0.5:
            st.session_state.score += 1
        
        # Kiểm tra game over
        if st.session_state.damage >= 100:
            st.session_state.game_started = False
            st.error("💥 GAME OVER! Xe của bạn đã bị hỏng hoàn toàn!")
            st.balloons()
            st.stop()
        
        # Auto-refresh game
        time.sleep(0.5)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Car Crash Game - Built with Streamlit</p>
    <p>Chơi an toàn, lái xe có trách nhiệm!</p>
</div>
""", unsafe_allow_html=True)
