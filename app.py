import streamlit as st
import pygame
import sys
import numpy as np
import random
from pygame import gfxdraw
import math

# Khởi tạo Pygame
pygame.init()

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
    
    player_speed = st.slider("Tốc độ xe bạn", 3, 10, 5)
    ai_car_count = st.slider("Số lượng xe AI", 1, 10, 5)
    traffic_density = st.slider("Mật độ giao thông", 1, 5, 3)
    
    if st.button("🔄 Khởi động lại trò chơi"):
        st.rerun()
    
    st.markdown("---")
    st.subheader("🎮 Điều khiển")
    st.markdown("""
    - **Mũi tên lên/xuống**: Tăng/giảm tốc độ
    - **Mũi tên trái/phải**: Chuyển hướng
    - **Spacebar**: Phanh
    - **R**: Reset xe
    """)

# Khởi tạo màn hình
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
ROAD_WIDTH = 400
LANE_WIDTH = ROAD_WIDTH // 3

class TrafficSign:
    def __init__(self, x, y, sign_type):
        self.x = x
        self.y = y
        self.type = sign_type
        self.width = 30
        self.height = 30
        
    def draw(self, screen, camera_y):
        # Vẽ biển báo
        sign_y = self.y - camera_y
        
        if self.type == "stop":
            pygame.draw.rect(screen, (255, 0, 0), 
                           (self.x, sign_y, self.width, self.height))
            # Chữ STOP
            font = pygame.font.SysFont(None, 20)
            text = font.render("STOP", True, (255, 255, 255))
            screen.blit(text, (self.x + 5, sign_y + 8))
            
        elif self.type == "speed_limit":
            pygame.draw.rect(screen, (255, 255, 0), 
                           (self.x, sign_y, self.width, self.height))
            # Số 60
            font = pygame.font.SysFont(None, 25)
            text = font.render("60", True, (0, 0, 0))
            screen.blit(text, (self.x + 8, sign_y + 5))
            
        elif self.type == "warning":
            pygame.draw.polygon(screen, (255, 165, 0), 
                              [(self.x + 15, sign_y),
                               (self.x + 30, sign_y + 30),
                               (self.x, sign_y + 30)])
            # Dấu chấm than
            pygame.draw.rect(screen, (255, 255, 255), 
                           (self.x + 13, sign_y + 8, 4, 15))
            pygame.draw.circle(screen, (255, 255, 255), 
                             (self.x + 15, sign_y + 25), 3)

class RoadInfrastructure:
    def __init__(self):
        self.lines = []
        self.signs = []
        self.obstacles = []
        
        # Tạo vạch kẻ đường
        for i in range(-100, 5000, 50):
            self.lines.append({
                'x': SCREEN_WIDTH // 2,
                'y': i,
                'width': 10,
                'height': 30
            })
        
        # Tạo biển báo
        sign_types = ["stop", "speed_limit", "warning"]
        for i in range(0, 5000, 200):
            sign_type = random.choice(sign_types)
            side = random.choice(["left", "right"])
            x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 - 50 if side == "left" else SCREEN_WIDTH // 2 + ROAD_WIDTH // 2 + 20
            self.signs.append(TrafficSign(x, i, sign_type))
        
        # Tạo vật cản
        obstacle_types = ["cone", "barrel", "rock"]
        for i in range(100, 5000, 150):
            if random.random() > 0.7:
                lane = random.randint(1, 3)
                x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + lane * LANE_WIDTH - LANE_WIDTH // 2
                self.obstacles.append({
                    'x': x,
                    'y': i,
                    'type': random.choice(obstacle_types),
                    'width': 20,
                    'height': 30
                })
    
    def draw(self, screen, camera_y):
        # Vẽ đường
        pygame.draw.rect(screen, (50, 50, 50),  # Màu đường
                       (SCREEN_WIDTH // 2 - ROAD_WIDTH // 2, 0, 
                        ROAD_WIDTH, SCREEN_HEIGHT))
        
        # Vẽ vạch chia làn
        for i in range(-3, 4):
            pygame.draw.rect(screen, (100, 100, 100),  # Màu vạch chia làn
                           (SCREEN_WIDTH // 2 - 5 + i * (ROAD_WIDTH // 3), 0, 
                            3, SCREEN_HEIGHT))
        
        # Vẽ vạch kẻ đường giữa
        for line in self.lines:
            line_y = line['y'] - camera_y
            if 0 <= line_y <= SCREEN_HEIGHT:
                pygame.draw.rect(screen, (255, 255, 255),
                               (line['x'] - line['width']//2, line_y,
                                line['width'], line['height']))
        
        # Vẽ biển báo
        for sign in self.signs:
            sign.draw(screen, camera_y)
        
        # Vẽ vật cản
        for obstacle in self.obstacles:
            obstacle_y = obstacle['y'] - camera_y
            if 0 <= obstacle_y <= SCREEN_HEIGHT:
                if obstacle['type'] == "cone":
                    pygame.draw.polygon(screen, (255, 165, 0), [
                        (obstacle['x'], obstacle_y + obstacle['height']),
                        (obstacle['x'] - obstacle['width']//2, obstacle_y),
                        (obstacle['x'] + obstacle['width']//2, obstacle_y)
                    ])
                elif obstacle['type'] == "barrel":
                    pygame.draw.rect(screen, (255, 0, 0),
                                   (obstacle['x'] - obstacle['width']//2, obstacle_y,
                                    obstacle['width'], obstacle['height']))
                else:  # rock
                    pygame.draw.circle(screen, (100, 100, 100),
                                     (obstacle['x'], obstacle_y + obstacle['height']//2),
                                     obstacle['width']//2)

class Car:
    def __init__(self, x, y, color=(255, 0, 0), is_ai=False):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 70
        self.color = color
        self.speed = 3 if is_ai else 5
        self.max_speed = 8 if is_ai else 10
        self.acceleration = 0.1 if is_ai else 0.2
        self.deceleration = 0.15
        self.angle = 0
        self.target_lane = None
        self.is_ai = is_ai
        self.ai_timer = 0
        self.ai_reaction_time = random.randint(30, 120)
        self.collision_cooldown = 0
        self.damage = 0
        self.max_damage = 100
        
    def move(self, road_width, player_car=None):
        if self.is_ai:
            self.ai_timer += 1
            
            # AI logic: đôi khi đổi làn
            if self.ai_timer > self.ai_reaction_time:
                self.ai_timer = 0
                self.ai_reaction_time = random.randint(30, 120)
                
                # 30% chance đổi làn
                if random.random() < 0.3:
                    lane_change = random.choice([-1, 1])
                    new_lane = max(1, min(3, (self.x - (SCREEN_WIDTH // 2 - ROAD_WIDTH // 2)) // LANE_WIDTH + 1 + lane_change))
                    self.target_lane = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + new_lane * LANE_WIDTH - LANE_WIDTH // 2
            
            # Di chuyển đến làn mục tiêu
            if self.target_lane:
                if abs(self.x - self.target_lane) > 2:
                    self.x += (self.target_lane - self.x) * 0.05
                else:
                    self.target_lane = None
            
            # Tự động tăng tốc
            self.speed = min(self.speed + self.acceleration * 0.5, self.max_speed)
            
            # Kiểm tra va chạm với xe player
            if player_car:
                distance = abs(self.y - player_car.y)
                if distance < 100:
                    self.speed = max(2, self.speed - self.deceleration)
        
        # Cập nhật vị trí
        self.y -= self.speed
        
        # Giới hạn trong đường
        left_boundary = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + 20
        right_boundary = SCREEN_WIDTH // 2 + ROAD_WIDTH // 2 - 20
        self.x = max(left_boundary, min(right_boundary, self.x))
        
        # Giảm thời gian hồi chiêu va chạm
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1
    
    def draw(self, screen, camera_y):
        car_y = self.y - camera_y
        
        # Chỉ vẽ nếu xe trong màn hình
        if -self.height < car_y < SCREEN_HEIGHT:
            # Vẽ thân xe
            car_rect = pygame.Rect(self.x - self.width//2, car_y - self.height//2, 
                                 self.width, self.height)
            
            # Tạo hiệu ứng hư hại
            damage_color = (
                min(255, self.color[0] + self.damage * 2),
                max(0, self.color[1] - self.damage),
                max(0, self.color[2] - self.damage)
            )
            
            pygame.draw.rect(screen, damage_color, car_rect, border_radius=8)
            
            # Vẽ kính chắn gió
            pygame.draw.rect(screen, (135, 206, 235),
                           (self.x - self.width//2 + 5, car_y - self.height//2 + 5,
                            self.width - 10, 15), border_radius=3)
            
            # Vẽ đèn
            pygame.draw.rect(screen, (255, 255, 200),
                           (self.x - self.width//2 + 5, car_y + self.height//2 - 10,
                            10, 5))
            pygame.draw.rect(screen, (255, 255, 200),
                           (self.x + self.width//2 - 15, car_y + self.height//2 - 10,
                            10, 5))
            
            # Hiển thị thanh damage nếu có
            if self.damage > 0:
                damage_width = (self.damage / self.max_damage) * self.width
                pygame.draw.rect(screen, (255, 0, 0),
                               (self.x - self.width//2, car_y - self.height//2 - 10,
                                damage_width, 5))
    
    def check_collision(self, other_car):
        if self.collision_cooldown > 0 or other_car.collision_cooldown > 0:
            return False
            
        rect1 = pygame.Rect(self.x - self.width//2, self.y - self.height//2,
                          self.width, self.height)
        rect2 = pygame.Rect(other_car.x - other_car.width//2, 
                          other_car.y - other_car.height//2,
                          other_car.width, other_car.height)
        
        if rect1.colliderect(rect2):
            # Tính toán va chạm vật lý
            relative_speed = abs(self.speed - other_car.speed)
            damage = min(relative_speed * 10, 50)
            
            self.damage = min(self.max_damage, self.damage + damage)
            other_car.damage = min(other_car.max_damage, other_car.damage + damage)
            
            # Đẩy xe ra
            if self.x < other_car.x:
                self.x -= 20
                other_car.x += 20
            else:
                self.x += 20
                other_car.x -= 20
            
            # Giảm tốc độ
            self.speed = max(1, self.speed * 0.5)
            other_car.speed = max(1, other_car.speed * 0.5)
            
            # Thời gian hồi chiêu
            self.collision_cooldown = 30
            other_car.collision_cooldown = 30
            
            return True
        return False

class Game:
    def __init__(self):
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.road = RoadInfrastructure()
        self.player = Car(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, (0, 100, 255))
        self.ai_cars = []
        self.camera_y = 0
        self.score = 0
        self.game_time = 0
        self.generate_ai_cars()
    
    def generate_ai_cars(self):
        self.ai_cars = []
        ai_colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), 
                    (255, 165, 0), (128, 0, 128)]
        
        for i in range(ai_car_count):
            lane = random.randint(1, 3)
            x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + lane * LANE_WIDTH - LANE_WIDTH // 2
            y = random.randint(-500, -100)
            color = random.choice(ai_colors)
            ai_car = Car(x, y, color, is_ai=True)
            ai_car.speed = random.uniform(3, 6)
            self.ai_cars.append(ai_car)
    
    def handle_events(self):
        keys = pygame.key.get_pressed()
        
        # Điều khiển xe player
        if keys[pygame.K_UP]:
            self.player.speed = min(self.player.speed + self.player.acceleration, 
                                  self.player.max_speed)
        if keys[pygame.K_DOWN]:
            self.player.speed = max(0, self.player.speed - self.player.deceleration)
        if keys[pygame.K_LEFT]:
            self.player.x -= 5
        if keys[pygame.K_RIGHT]:
            self.player.x += 5
        if keys[pygame.K_SPACE]:  # Phanh
            self.player.speed = max(0, self.player.speed - self.player.deceleration * 2)
        if keys[pygame.K_r]:  # Reset
            self.player.x = SCREEN_WIDTH // 2
            self.player.damage = 0
    
    def update(self):
        self.handle_events()
        
        # Di chuyển camera theo xe player
        self.camera_y = self.player.y - SCREEN_HEIGHT * 0.7
        
        # Di chuyển xe player
        self.player.move(ROAD_WIDTH)
        
        # Di chuyển và kiểm tra va chạm cho xe AI
        for ai_car in self.ai_cars[:]:
            ai_car.move(ROAD_WIDTH, self.player)
            
            # Kiểm tra va chạm với player
            self.player.check_collision(ai_car)
            
            # Kiểm tra va chạm giữa các xe AI với nhau
            for other_ai in self.ai_cars:
                if ai_car != other_ai:
                    ai_car.check_collision(other_ai)
            
            # Xóa xe AI đã ra khỏi màn hình
            if ai_car.y < self.camera_y - 200:
                self.ai_cars.remove(ai_car)
                self.score += 10
        
        # Tạo thêm xe AI mới
        while len(self.ai_cars) < ai_car_count:
            lane = random.randint(1, 3)
            x = SCREEN_WIDTH // 2 - ROAD_WIDTH // 2 + lane * LANE_WIDTH - LANE_WIDTH // 2
            y = self.camera_y + SCREEN_HEIGHT + random.randint(200, 500)
            color = random.choice([(255, 0, 0), (0, 255, 0), (255, 255, 0)])
            ai_car = Car(x, y, color, is_ai=True)
            ai_car.speed = random.uniform(3, 6)
            self.ai_cars.append(ai_car)
        
        # Cập nhật thời gian và điểm
        self.game_time += 1
        if self.game_time % 60 == 0:
            self.score += 1
        
        # Game over nếu hư hại quá nhiều
        if self.player.damage >= self.player.max_damage:
            self.running = False
    
    def draw(self):
        # Màu nền (bầu trời)
        self.screen.fill((135, 206, 235))
        
        # Vẽ đồng cỏ hai bên đường
        pygame.draw.rect(self.screen, (34, 139, 34),  # Xanh lá cây
                       (0, 0, SCREEN_WIDTH // 2 - ROAD_WIDTH // 2, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, (34, 139, 34),
                       (SCREEN_WIDTH // 2 + ROAD_WIDTH // 2, 0,
                        SCREEN_WIDTH // 2 - ROAD_WIDTH // 2, SCREEN_HEIGHT))
        
        # Vẽ cơ sở hạ tầng đường
        self.road.draw(self.screen, self.camera_y)
        
        # Vẽ các xe AI
        for ai_car in self.ai_cars:
            ai_car.draw(self.screen, self.camera_y)
        
        # Vẽ xe player
        self.player.draw(self.screen, self.camera_y)
        
        # Vẽ HUD
        self.draw_hud()
    
    def draw_hud(self):
        # Tạo font
        font = pygame.font.SysFont(None, 36)
        
        # Hiển thị điểm
        score_text = font.render(f"Điểm: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        # Hiển thị tốc độ
        speed_text = font.render(f"Tốc độ: {int(self.player.speed * 10)} km/h", True, (255, 255, 255))
        self.screen.blit(speed_text, (20, 60))
        
        # Hiển thị hư hại
        damage_text = font.render(f"Hư hại: {self.player.damage}%", True, 
                                (255, 0, 0) if self.player.damage > 50 else (255, 255, 255))
        self.screen.blit(damage_text, (20, 100))
        
        # Hiển thị số xe AI còn lại
        ai_text = font.render(f"Xe AI: {len(self.ai_cars)}", True, (255, 255, 255))
        self.screen.blit(ai_text, (20, 140))
        
        # Hiển thị hướng dẫn
        help_font = pygame.font.SysFont(None, 24)
        help_text = help_font.render("Mũi tên: Di chuyển | Space: Phanh | R: Reset", True, (200, 200, 200))
        self.screen.blit(help_text, (SCREEN_WIDTH - 400, 20))

def main():
    st.markdown("### 🎮 Khu vực chơi game")
    
    # Tạo container cho game
    game_container = st.empty()
    
    # Khởi tạo game
    game = Game()
    
    # Vòng lặp game
    running = True
    while running and game.running:
        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Cập nhật game
        game.update()
        game.draw()
        
        # Chuyển đổi Pygame surface thành hình ảnh để hiển thị trong Streamlit
        game_surface = game.screen
        game_array = pygame.surfarray.array3d(game_surface)
        game_array = np.transpose(game_array, (1, 0, 2))
        
        # Hiển thị game
        game_container.image(game_array, channels="RGB", 
                           use_column_width=True,
                           caption="Car Crash Simulator")
        
        # Điều khiển tốc độ khung hình
        game.clock.tick(60)
    
    # Hiển thị kết quả khi game over
    if not game.running:
        st.error(f"### 💥 Game Over! Xe bạn đã bị hỏng hoàn toàn!")
        st.success(f"### 🏆 Điểm cuối cùng: {game.score}")
        
        if st.button("🔄 Chơi lại"):
            st.rerun()

if __name__ == "__main__":
    # Khởi tạo Pygame cho Streamlit
    pygame.display.set_mode((1, 1))  # Ẩn cửa sổ Pygame
    main()
