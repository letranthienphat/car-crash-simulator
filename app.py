import streamlit as st
import numpy as np
import random
import time
import math

st.set_page_config(page_title="Car Crash Simulator", layout="wide")
st.title("🚗 Car Crash Simulator")

# Khởi tạo session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'menu'
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'player_pos' not in st.session_state:
    st.session_state.player_pos = 2  # Làn 1, 2, hoặc 3
if 'player_speed' not in st.session_state:
    st.session_state.player_speed = 5
if 'ai_cars' not in st.session_state:
    st.session_state.ai_cars = []
if 'obstacles' not in st.session_state:
    st.session_state.obstacles = []
if 'damage' not in st.session_state:
    st.session_state.damage = 0
if 'game_time' not in st.session_state:
    st.session_state.game_time = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

# Sidebar
with st.sidebar:
    st.header("⚙️ Cài Đặt")
    
    if st.button("🔄 Khởi động lại game", type="primary"):
        st.session_state.game_state = 'playing'
        st.session_state.score = 0
        st.session_state.player_pos = 2
        st.session_state.player_speed = 5
        st.session_state.ai_cars = []
        st.session_state.obstacles = []
        st.session_state.damage = 0
        st.session_state.game_time = 0
        st.rerun()
    
    st.markdown("---")
    st.subheader("🎮 Điều khiển")
    st.markdown("""
    - **A**: Sang trái
    - **D**: Sang phải
    - **W**: Tăng tốc
    - **S**: Giảm tốc
    """)
    
    st.markdown("---")
    st.subheader("📊 Thống kê")
    st.metric("Điểm số", st.session_state.score)
    st.metric("Hư hại", f"{st.session_state.damage}%")
    st.metric("Tốc độ", f"{st.session_state.player_speed} km/h")

# Hàm vẽ game
def draw_game():
    # Tạo canvas đơn giản bằng HTML
    lanes = 3
    road_width = 300
    lane_width = road_width // lanes
    
    # Tạo HTML cho game
    html = f"""
    <style>
        .game-container {{
            position: relative;
            width: {road_width + 100}px;
            height: 600px;
            margin: 0 auto;
            background: linear-gradient(to bottom, #87CEEB, #4682B4);
            overflow: hidden;
        }}
        .road {{
            position: absolute;
            left: 50px;
            top: 0;
            width: {road_width}px;
            height: 100%;
            background: #696969;
        }}
        .lane-line {{
            position: absolute;
            left: {lane_width}px;
            top: 0;
            width: 2px;
            height: 100%;
            background: white;
        }}
        .lane-line-2 {{
            left: {lane_width * 2}px;
        }}
        .player-car {{
            position: absolute;
            left: {50 + (st.session_state.player_pos - 0.5) * lane_width - 15}px;
            bottom: 100px;
            width: 30px;
            height: 50px;
            background: blue;
            border-radius: 5px;
            text-align: center;
            color: white;
            line-height: 50px;
            font-weight: bold;
        }}
        .ai-car {{
            position: absolute;
            width: 30px;
            height: 50px;
            background: red;
            border-radius: 5px;
            text-align: center;
            color: white;
            line-height: 50px;
            font-weight: bold;
        }}
        .obstacle {{
            position: absolute;
            width: 20px;
            height: 30px;
            background: orange;
            border-radius: 3px;
        }}
        .score {{
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            font-size: 20px;
            font-weight: bold;
            background: rgba(0,0,0,0.5);
            padding: 5px 10px;
            border-radius: 5px;
        }}
        .damage-bar {{
            position: absolute;
            top: 50px;
            left: 10px;
            width: 200px;
            height: 20px;
            background: rgba(0,0,0,0.5);
            border-radius: 5px;
            overflow: hidden;
        }}
        .damage-fill {{
            height: 100%;
            background: red;
            width: {st.session_state.damage}%;
        }}
    </style>
    
    <div class="game-container">
        <div class="road">
            <div class="lane-line"></div>
            <div class="lane-line lane-line-2"></div>
            
            <!-- Vạch kẻ đường -->
            <div style="position: absolute; left: {road_width/2 - 25}px; top: calc(var(--offset) * -100px); width: 50px; height: 30px; background: white;"></div>
            
            <!-- Xe người chơi -->
            <div class="player-car">P</div>
            
            <!-- Xe AI -->
    """
    
    # Thêm xe AI
    for i, car in enumerate(st.session_state.ai_cars):
        lane, pos = car
        html += f"""
            <div class="ai-car" style="left: {50 + (lane - 0.5) * lane_width - 15}px; top: {pos}px;">AI</div>
        """
    
    # Thêm vật cản
    for i, obs in enumerate(st.session_state.obstacles):
        lane, pos = obs
        html += f"""
            <div class="obstacle" style="left: {50 + (lane - 0.5) * lane_width - 10}px; top: {pos}px;"></div>
        """
    
    html += f"""
            <!-- Điểm số -->
            <div class="score">Điểm: {st.session_state.score}</div>
            
            <!-- Thanh hư hại -->
            <div class="damage-bar">
                <div class="damage-fill"></div>
            </div>
            <div style="position: absolute; top: 50px; left: 220px; color: white; font-weight: bold;">
                Hư hại: {st.session_state.damage}%
            </div>
        </div>
    </div>
    
    <script>
        // Thêm hiệu ứng vạch kẻ đường di chuyển
        document.addEventListener('DOMContentLoaded', function() {{
            const road = document.querySelector('.road');
            let offset = 0;
            
            function animateRoad() {{
                offset = (offset + 0.5) % 100;
                road.style.setProperty('--offset', offset);
                requestAnimationFrame(animateRoad);
            }}
            
            animateRoad();
        }});
    </script>
    """
    
    return html

# Hàm cập nhật game
def update_game():
    current_time = time.time()
    
    # Tạo xe AI mới
    if random.random() < 0.1:
        lane = random.randint(1, 3)
        st.session_state.ai_cars.append([lane, -50])
    
    # Tạo vật cản mới
    if random.random() < 0.05:
        lane = random.randint(1, 3)
        st.session_state.obstacles.append([lane, -30])
    
    # Di chuyển xe AI
    new_ai_cars = []
    for car in st.session_state.ai_cars:
        lane, pos = car
        new_pos = pos + 3 + random.random() * 2
        
        # Kiểm tra va chạm với xe player
        if (lane == st.session_state.player_pos and 
            abs(new_pos - 500) < 70):  # 500 là vị trí Y của xe player
            st.session_state.damage = min(100, st.session_state.damage + 20)
            st.session_state.score = max(0, st.session_state.score - 10)
        elif new_pos < 600:
            new_ai_cars.append([lane, new_pos])
        else:
            st.session_state.score += 10
    
    st.session_state.ai_cars = new_ai_cars
    
    # Di chuyển vật cản
    new_obstacles = []
    for obs in st.session_state.obstacles:
        lane, pos = obs
        new_pos = pos + st.session_state.player_speed
        
        # Kiểm tra va chạm
        if (lane == st.session_state.player_pos and 
            abs(new_pos - 500) < 50):
            st.session_state.damage = min(100, st.session_state.damage + 30)
            st.session_state.score = max(0, st.session_state.score - 15)
        elif new_pos < 600:
            new_obstacles.append([lane, new_pos])
        else:
            st.session_state.score += 5
    
    st.session_state.obstacles = new_obstacles
    
    # Cập nhật thời gian
    st.session_state.game_time += 1
    st.session_state.last_update = current_time
    
    # Kiểm tra game over
    if st.session_state.damage >= 100:
        st.session_state.game_state = 'game_over'

# Main app
if st.session_state.game_state == 'menu':
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>🚗 Car Crash Simulator</h1>
        <h3>Trò chơi đua xe với vật lý va chạm</h3>
        <br><br>
        <p>Tránh xe AI và vật cản để sống sót lâu nhất!</p>
        <p>Điều khiển xe của bạn bằng các phím A/D hoặc nút bên dưới.</p>
        <br><br>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎮 Bắt đầu chơi", type="primary", use_container_width=True, size="large"):
            st.session_state.game_state = 'playing'
            st.rerun()

elif st.session_state.game_state == 'playing':
    # Điều khiển
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("⬅️ A - Trái", use_container_width=True):
            st.session_state.player_pos = max(1, st.session_state.player_pos - 1)
    with col2:
        if st.button("➡️ D - Phải", use_container_width=True):
            st.session_state.player_pos = min(3, st.session_state.player_pos + 1)
    with col3:
        if st.button("⬆️ W - Nhanh", use_container_width=True):
            st.session_state.player_speed = min(10, st.session_state.player_speed + 1)
    with col4:
        if st.button("⬇️ S - Chậm", use_container_width=True):
            st.session_state.player_speed = max(1, st.session_state.player_speed - 1)
    with col5:
        if st.button("⏹️ Dừng", use_container_width=True):
            st.session_state.game_state = 'paused'
    
    # Hiển thị game
    st.components.v1.html(draw_game(), height=650)
    
    # Auto-update
    if time.time() - st.session_state.last_update > 0.1:
        update_game()
        st.rerun()

elif st.session_state.game_state == 'paused':
    st.warning("⏸️ Game đã tạm dừng")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Tiếp tục", use_container_width=True):
            st.session_state.game_state = 'playing'
            st.session_state.last_update = time.time()
            st.rerun()
    with col2:
        if st.button("🔄 Chơi lại", use_container_width=True):
            st.session_state.game_state = 'menu'
            st.rerun()
    
    st.components.v1.html(draw_game(), height=650)

elif st.session_state.game_state == 'game_over':
    st.error("💥 GAME OVER! Xe của bạn đã bị hỏng hoàn toàn!")
    st.success(f"🏆 Điểm số cuối cùng: {st.session_state.score}")
    
    # Hiển thị thống kê
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Thời gian sống", f"{st.session_state.game_time // 10} giây")
    with col2:
        st.metric("Số xe AI tránh được", f"{st.session_state.score // 10}")
    with col3:
        st.metric("Mức độ hư hại", "100%")
    
    if st.button("🔄 Chơi lại", type="primary"):
        st.session_state.game_state = 'menu'
        st.rerun()

# Thông tin thêm
st.markdown("---")
st.markdown("""
### 🎮 Cách chơi:
1. Sử dụng nút **A/D** hoặc **Trái/Phải** để chuyển làn
2. Sử dụng **W/S** hoặc **Nhanh/Chậm** để điều chỉnh tốc độ
3. Tránh xe **AI** (màu đỏ) và vật cản (màu cam)
4. Giữ mức hư hại dưới 100%

### ⚠️ Vật lý va chạm:
- Va chạm với xe AI: +20% hư hại
- Va chạm với vật cản: +30% hư hại
- Tốc độ càng cao, va chạm càng mạnh
""")
