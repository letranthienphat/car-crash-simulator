import streamlit as st
import numpy as np
import random
import time
import plotly.graph_objects as go
import plotly.subplots as sp
from collections import deque
import math

st.set_page_config(page_title="Car Crash Simulator", layout="wide")
st.title("🚗 Car Crash Simulator - Game Đua Xe Va Chạm")
st.markdown("---")

# Sidebar điều khiển
with st.sidebar:
    st.header("⚙️ Cài Đặt Trò Chơi")
    
    game_mode = st.selectbox(
        "Chế độ chơi",
        ["Đua tự do", "Tránh vật cản", "Đua với AI"]
    )
    
    player_speed = st.slider("Tốc độ xe bạn", 3, 10, 5, key="player_speed")
    ai_car_count = st.slider("Số lượng xe AI", 1, 10, 5, key="ai_car_count")
    traffic_density = st.slider("Mật độ giao thông", 1, 5, 3, key="traffic_density")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Bắt đầu chơi", type="primary", use_container_width=True):
            st.session_state.game_running = True
            st.session_state.game_started = True
    
    with col2:
        if st.button("🔄 Khởi động lại", use_container_width=True):
            st.session_state.game_running = False
            st.rerun()
    
    st.markdown("---")
    st.subheader("🎮 Điều khiển")
    st.markdown("""
    - **Phím W**: Tăng tốc
    - **Phím S**: Giảm tốc/phanh
    - **Phím A**: Sang trái
    - **Phím D**: Sang phải
    - **Phím R**: Reset xe
    """)
    
    st.markdown("---")
    st.subheader("📊 Thống kê")
    if 'score' in st.session_state:
        st.metric("Điểm số", st.session_state.score)
    if 'damage' in st.session_state:
        st.metric("Hư hại", f"{st.session_state.damage}%")
    if 'time' in st.session_state:
        st.metric("Thời gian", f"{st.session_state.time}s")

# Khởi tạo session state
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'game_running' not in st.session_state:
    st.session_state.game_running = False

# Các tham số game
ROAD_WIDTH = 400
LANE_WIDTH = ROAD_WIDTH // 3
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 70
AI_WIDTH = 35
AI_HEIGHT = 60

class Car:
    def __init__(self, x, y, color='red', is_ai=False, lane=2):
        self.x = x
        self.y = y
        self.color = color
        self.width = AI_WIDTH if is_ai else PLAYER_WIDTH
        self.height = AI_HEIGHT if is_ai else PLAYER_HEIGHT
        self.speed = random.uniform(3, 6) if is_ai else player_speed
        self.max_speed = 8 if is_ai else 10
        self.acceleration = 0.1 if is_ai else 0.2
        self.deceleration = 0.15
        self.is_ai = is_ai
        self.target_lane = lane
        self.ai_timer = 0
        self.ai_reaction_time = random.randint(30, 120)
        self.collision_cooldown = 0
        self.damage = 0
        self.max_damage = 100
        self.lane = lane
        
    def move(self, road_width, player_car=None):
        if self.is_ai:
            self.ai_timer += 1
            
            # AI logic: đôi khi đổi làn
            if self.ai_timer > self.ai_reaction_time:
                self.ai_timer = 0
                self.ai_reaction_time = random.randint(30, 120)
                
                # 30% chance đổi làn
                if random.random() < 0.3:
                    lane_change = random.choice([-1, 0, 1])
                    new_lane = max(1, min(3, self.lane + lane_change))
                    self.target_lane = new_lane
                    self.lane = new_lane
            
            # Tự động tăng tốc
            self.speed = min(self.speed + self.acceleration * 0.5, self.max_speed)
            
            # Kiểm tra khoảng cách với player
            if player_car:
                distance = abs(self.y - player_car.y)
                if distance < 150:
                    self.speed = max(2, self.speed - self.deceleration)
        
        # Cập nhật vị trí Y
        self.y -= self.speed
        
        # Cập nhật vị trí X theo làn
        lane_center = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + self.lane * LANE_WIDTH - LANE_WIDTH // 2
        self.x = lane_center
        
        # Giảm collision cooldown
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1
            
        return self.x, self.y
    
    def check_collision(self, other_car):
        if self.collision_cooldown > 0 or other_car.collision_cooldown > 0:
            return False
            
        # Kiểm tra va chạm đơn giản
        distance = math.sqrt((self.x - other_car.x)**2 + (self.y - other_car.y)**2)
        collision_threshold = (self.width + other_car.width) / 2
        
        if distance < collision_threshold:
            # Tính toán damage
            relative_speed = abs(self.speed - other_car.speed)
            damage = min(relative_speed * 10, 50)
            
            self.damage = min(self.max_damage, self.damage + damage)
            other_car.damage = min(other_car.max_damage, other_car.damage + damage)
            
            # Giảm tốc
            self.speed = max(1, self.speed * 0.5)
            other_car.speed = max(1, other_car.speed * 0.5)
            
            # Thời gian cooldown
            self.collision_cooldown = 30
            other_car.collision_cooldown = 30
            
            return True
        return False

class TrafficSystem:
    def __init__(self):
        self.signs = []
        self.obstacles = []
        self.generate_elements()
        
    def generate_elements(self):
        # Tạo biển báo
        sign_types = ["stop", "speed", "warning"]
        for i in range(0, 5000, 200):
            sign_type = random.choice(sign_types)
            side = random.choice(["left", "right"])
            x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 - 50 if side == "left" else SCREEN_WIDTH // 2 + ROAD_WIDTH // 2 + 20
            self.signs.append({
                'x': x,
                'y': i,
                'type': sign_type,
                'side': side
            })
        
        # Tạo vật cản
        for i in range(100, 5000, 150):
            if random.random() > 0.6:
                lane = random.randint(1, 3)
                x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + lane * LANE_WIDTH - LANE_WIDTH // 2
                self.obstacles.append({
                    'x': x,
                    'y': i,
                    'type': random.choice(["cone", "barrel", "rock"]),
                    'lane': lane
                })

def create_game_figure(player_car, ai_cars, traffic_system, camera_y, score, damage, game_time):
    fig = go.Figure()
    
    # Vẽ đường
    fig.add_shape(
        type="rect",
        x0=SCREEN_WIDTH // 2 - ROAD_WIDTH // 2,
        y0=0,
        x1=SCREEN_WIDTH // 2 + ROAD_WIDTH // 2,
        y1=SCREEN_HEIGHT,
        fillcolor="gray",
        opacity=0.7,
        line=dict(width=0)
    )
    
    # Vẽ vạch chia làn
    for i in range(1, 3):
        lane_x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + i * LANE_WIDTH
        fig.add_shape(
            type="line",
            x0=lane_x, y0=0,
            x1=lane_x, y1=SCREEN_HEIGHT,
            line=dict(color="white", width=2, dash="dash")
        )
    
    # Vẽ vạch kẻ đường giữa
    for i in range(-50, SCREEN_HEIGHT + 50, 60):
        fig.add_shape(
            type="rect",
            x0=SCREEN_WIDTH // 2 - 5,
            y0=i - camera_y % 60,
            x1=SCREEN_WIDTH // 2 + 5,
            y1=i + 30 - camera_y % 60,
            fillcolor="white",
            line=dict(width=0)
        )
    
    # Vẽ biển báo trong tầm nhìn
    for sign in traffic_system.signs:
        sign_y = sign['y'] - camera_y
        if 0 <= sign_y <= SCREEN_HEIGHT:
            if sign['type'] == 'stop':
                color = 'red'
                text = 'STOP'
            elif sign['type'] == 'speed':
                color = 'yellow'
                text = '60'
            else:
                color = 'orange'
                text = '!'
            
            fig.add_trace(go.Scatter(
                x=[sign['x']],
                y=[sign_y],
                mode='markers+text',
                marker=dict(size=20, color=color, symbol='square'),
                text=text,
                textposition="middle center",
                textfont=dict(size=10, color='black'),
                name='Biển báo'
            ))
    
    # Vẽ vật cản trong tầm nhìn
    for obstacle in traffic_system.obstacles:
        obstacle_y = obstacle['y'] - camera_y
        if 0 <= obstacle_y <= SCREEN_HEIGHT:
            if obstacle['type'] == 'cone':
                symbol = 'triangle-up'
                color = 'orange'
            elif obstacle['type'] == 'barrel':
                symbol = 'circle'
                color = 'red'
            else:
                symbol = 'diamond'
                color = 'gray'
            
            fig.add_trace(go.Scatter(
                x=[obstacle['x']],
                y=[obstacle_y],
                mode='markers',
                marker=dict(size=15, color=color, symbol=symbol),
                name='Vật cản'
            ))
    
    # Vẽ xe AI
    for i, ai_car in enumerate(ai_cars):
        ai_y = ai_car.y - camera_y
        if -AI_HEIGHT <= ai_y <= SCREEN_HEIGHT:
            fig.add_trace(go.Scatter(
                x=[ai_car.x],
                y=[ai_y],
                mode='markers+text',
                marker=dict(
                    size=30,
                    color=ai_car.color,
                    symbol='square',
                    line=dict(width=2, color='black')
                ),
                text=f"AI{i}",
                textposition="middle center",
                textfont=dict(size=8, color='white'),
                name=f'Xe AI {i+1}'
            ))
    
    # Vẽ xe player
    player_y = player_car.y - camera_y
    if -PLAYER_HEIGHT <= player_y <= SCREEN_HEIGHT:
        fig.add_trace(go.Scatter(
            x=[player_car.x],
            y=[player_y],
            mode='markers+text',
            marker=dict(
                size=35,
                color=player_car.color,
                symbol='square',
                line=dict(width=3, color='blue')
            ),
            text="BẠN",
            textposition="middle center",
            textfont=dict(size=10, color='white', weight='bold'),
            name='Xe của bạn'
        ))
    
    # Cập nhật layout
    fig.update_layout(
        title=f"Car Crash Simulator | Điểm: {score} | Hư hại: {damage}% | Thời gian: {game_time}s",
        xaxis=dict(
            range=[0, SCREEN_WIDTH],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title=''
        ),
        yaxis=dict(
            range=[0, SCREEN_HEIGHT],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            title='',
            scaleanchor="x",
            scaleratio=1
        ),
        showlegend=False,
        height=SCREEN_HEIGHT,
        margin=dict(l=0, r=0, t=50, b=0),
        plot_bgcolor='lightblue'
    )
    
    return fig

def main_game():
    # Khởi tạo game state
    if 'player_car' not in st.session_state:
        st.session_state.player_car = Car(
            SCREEN_WIDTH // 2, 
            SCREEN_HEIGHT - 100, 
            color='blue', 
            is_ai=False,
            lane=2
        )
    
    if 'ai_cars' not in st.session_state:
        st.session_state.ai_cars = []
        for i in range(ai_car_count):
            lane = random.randint(1, 3)
            y = random.randint(-500, -100)
            color = random.choice(['red', 'green', 'yellow', 'orange', 'purple'])
            ai_car = Car(
                SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + lane * LANE_WIDTH - LANE_WIDTH // 2,
                y,
                color=color,
                is_ai=True,
                lane=lane
            )
            ai_car.speed = random.uniform(3, 6)
            st.session_state.ai_cars.append(ai_car)
    
    if 'traffic_system' not in st.session_state:
        st.session_state.traffic_system = TrafficSystem()
    
    if 'camera_y' not in st.session_state:
        st.session_state.camera_y = 0
    
    if 'score' not in st.session_state:
        st.session_state.score = 0
    
    if 'damage' not in st.session_state:
        st.session_state.damage = 0
    
    if 'game_time' not in st.session_state:
        st.session_state.game_time = 0
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()
    
    # Container cho game
    game_container = st.empty()
    controls_container = st.empty()
    
    # Điều khiển bằng phím
    with controls_container.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            accelerate = st.button("W - Tăng tốc", use_container_width=True)
        with col2:
            brake = st.button("S - Phanh", use_container_width=True)
        with col3:
            left = st.button("A - Sang trái", use_container_width=True)
        with col4:
            right = st.button("D - Sang phải", use_container_width=True)
        with col5:
            reset = st.button("R - Reset", use_container_width=True)
    
    # Xử lý điều khiển
    if accelerate:
        st.session_state.player_car.speed = min(
            st.session_state.player_car.speed + st.session_state.player_car.acceleration,
            st.session_state.player_car.max_speed
        )
    
    if brake:
        st.session_state.player_car.speed = max(
            0,
            st.session_state.player_car.speed - st.session_state.player_car.deceleration * 2
        )
    
    if left:
        st.session_state.player_car.lane = max(1, st.session_state.player_car.lane - 1)
    
    if right:
        st.session_state.player_car.lane = min(3, st.session_state.player_car.lane + 1)
    
    if reset:
        st.session_state.player_car.x = SCREEN_WIDTH // 2
        st.session_state.player_car.damage = 0
        st.session_state.damage = 0
    
    # Game loop simulation
    if st.session_state.game_running:
        current_time = time.time()
        time_diff = current_time - st.session_state.last_update
        
        if time_diff > 0.05:  # 20 FPS
            # Di chuyển player car
            st.session_state.player_car.move(ROAD_WIDTH)
            
            # Cập nhật camera
            st.session_state.camera_y = st.session_state.player_car.y - SCREEN_HEIGHT * 0.7
            
            # Di chuyển và cập nhật AI cars
            for ai_car in st.session_state.ai_cars[:]:
                ai_car.move(ROAD_WIDTH, st.session_state.player_car)
                
                # Kiểm tra va chạm với player
                if st.session_state.player_car.check_collision(ai_car):
                    st.session_state.damage = st.session_state.player_car.damage
                    
                    # Hiệu ứng va chạm
                    st.warning("💥 Va chạm!")
            
            # Xóa AI cars đã vượt quá
            st.session_state.ai_cars = [
                ai_car for ai_car in st.session_state.ai_cars 
                if ai_car.y > st.session_state.camera_y - 200
            ]
            
            # Thêm AI cars mới
            while len(st.session_state.ai_cars) < ai_car_count:
                lane = random.randint(1, 3)
                y = st.session_state.camera_y + SCREEN_HEIGHT + random.randint(200, 500)
                color = random.choice(['red', 'green', 'yellow'])
                new_ai = Car(
                    SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + lane * LANE_WIDTH - LANE_WIDTH // 2,
                    y,
                    color=color,
                    is_ai=True,
                    lane=lane
                )
                new_ai.speed = random.uniform(3, 6)
                st.session_state.ai_cars.append(new_ai)
                st.session_state.score += 10
            
            # Cập nhật thời gian và điểm
            st.session_state.game_time += 1
            if st.session_state.game_time % 20 == 0:
                st.session_state.score += 5
            
            st.session_state.last_update = current_time
            
            # Kiểm tra game over
            if st.session_state.player_car.damage >= 100:
                st.session_state.game_running = False
                st.error("💥 Game Over! Xe của bạn đã bị hỏng hoàn toàn!")
                st.balloons()
    
    # Tạo hình ảnh game
    fig = create_game_figure(
        st.session_state.player_car,
        st.session_state.ai_cars,
        st.session_state.traffic_system,
        st.session_state.camera_y,
        st.session_state.score,
        st.session_state.damage,
        st.session_state.game_time
    )
    
    # Hiển thị game
    game_container.plotly_chart(fig, use_container_width=True)
    
    # Auto-refresh khi game đang chạy
    if st.session_state.game_running:
        time.sleep(0.05)
        st.rerun()

# Hiển thị màn hình bắt đầu
if not st.session_state.game_started:
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>🚗 Car Crash Simulator</h1>
        <h3>Trò chơi đua xe với vật lý va chạm thực tế</h3>
        <br><br>
        <p>Điều khiển xe của bạn trên đường cao tốc, tránh các xe AI và vật cản!</p>
        <p>Chọn cài đặt trong sidebar và nhấn <strong>Bắt đầu chơi</strong>!</p>
        <br><br>
    </div>
    """, unsafe_allow_html=True)
    
    # Hiển thị hướng dẫn
    with st.expander("📖 Hướng dẫn chơi", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 🎮 Điều khiển
            - **W**: Tăng tốc độ
            - **S**: Giảm tốc/phanh
            - **A**: Chuyển sang làn trái
            - **D**: Chuyển sang làn phải
            - **R**: Reset vị trí xe
            
            ### 🎯 Mục tiêu
            - Tránh va chạm với xe AI
            - Đạt điểm cao nhất
            - Giữ mức hư hại dưới 100%
            """)
        
        with col2:
            st.markdown("""
            ### 🚗 Các loại xe
            - **Xe xanh dương**: Xe của bạn
            - **Xe đỏ/xanh lá**: Xe AI
            - **Vật thể màu cam**: Vật cản
            
            ### ⚠️ Biển báo
            - 🔴 **Đỏ**: Biển STOP
            - 🟡 **Vàng**: Giới hạn tốc độ 60km/h
            - 🟠 **Cam**: Cảnh báo nguy hiểm
            """)
    
    # Hiển thị preview
    st.markdown("### 🎮 Preview")
    sample_fig = create_game_figure(
        Car(SCREEN_WIDTH // 2, 300, color='blue', is_ai=False, lane=2),
        [
            Car(SCREEN_WIDTH // 2 - 100, 200, color='red', is_ai=True, lane=1),
            Car(SCREEN_WIDTH // 2, 150, color='green', is_ai=True, lane=2),
            Car(SCREEN_WIDTH // 2 + 100, 100, color='yellow', is_ai=True, lane=3)
        ],
        TrafficSystem(),
        0,
        0,
        0,
        0
    )
    st.plotly_chart(sample_fig, use_container_width=True)

else:
    main_game()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Car Crash Simulator - Built with Streamlit & Plotly</p>
    <p>⚠️ Chú ý an toàn giao thông trong đời thực!</p>
</div>
""", unsafe_allow_html=True)
