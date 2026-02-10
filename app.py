import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
import math
import time
import json
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="🚗 Car Crash Simulator Ultimate",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CÁC LỚP DỮ LIỆU ====================

class WeatherType(Enum):
    SUNNY = "sunny"
    RAINY = "rainy"
    FOGGY = "foggy"
    NIGHT = "night"
    STORMY = "stormy"

class CarType(Enum):
    SEDAN = "sedan"
    SUV = "suv"
    TRUCK = "truck"
    SPORTS = "sports"
    BUS = "bus"
    POLICE = "police"
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"

class RoadType(Enum):
    HIGHWAY = "highway"
    CITY_STREET = "city_street"
    COUNTRY_ROAD = "country_road"
    DIRT_ROAD = "dirt_road"
    BRIDGE = "bridge"
    TUNNEL = "tunnel"
    INTERSECTION = "intersection"
    ROUNDABOUT = "roundabout"

class TrafficSignType(Enum):
    STOP = "stop"
    SPEED_LIMIT = "speed_limit"
    TRAFFIC_LIGHT = "traffic_light"
    YIELD = "yield"
    PEDESTRIAN = "pedestrian"
    SCHOOL = "school"
    CONSTRUCTION = "construction"
    NO_ENTRY = "no_entry"

@dataclass
class Vector2:
    x: float
    y: float
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector2(self.x / mag, self.y / mag)
        return Vector2(0, 0)
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def rotate(self, angle):
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

@dataclass
class Color:
    r: int
    g: int
    b: int
    a: int = 255
    
    def to_hex(self):
        return f'#{self.r:02x}{self.g:02x}{self.b:02x}'
    
    def to_rgba(self):
        return f'rgba({self.r}, {self.g}, {self.b}, {self.a/255})'

# ==================== HỆ THỐNG VẬT LÝ ====================

class PhysicsEngine:
    def __init__(self):
        self.gravity = 9.81
        self.friction_coefficient = 0.85
        self.restitution = 0.3
        self.drag_coefficient = 0.3
        self.air_density = 1.225
        self.collisions = []
    
    def check_collision(self, obj1, obj2):
        """Kiểm tra va chạm giữa hai vật thể"""
        dx = obj1.position.x - obj2.position.x
        dy = obj1.position.y - obj2.position.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < (obj1.radius + obj2.radius):
            normal = Vector2(dx, dy).normalize()
            return {
                'collision': True,
                'normal': normal,
                'depth': (obj1.radius + obj2.radius) - distance,
                'point': Vector2(
                    (obj1.position.x + obj2.position.x) / 2,
                    (obj1.position.y + obj2.position.y) / 2
                )
            }
        return {'collision': False}
    
    def resolve_collision(self, obj1, obj2, collision_data):
        """Giải quyết va chạm"""
        normal = collision_data['normal']
        depth = collision_data['depth']
        
        # Đẩy vật thể ra
        correction = normal * depth * 0.5
        obj1.position = obj1.position + correction
        obj2.position = obj2.position - correction
        
        # Tính toán động lượng
        relative_velocity = Vector2(
            obj2.velocity.x - obj1.velocity.x,
            obj2.velocity.y - obj1.velocity.y
        )
        
        vel_along_normal = relative_velocity.x * normal.x + relative_velocity.y * normal.y
        
        if vel_along_normal > 0:
            return
        
        e = min(obj1.restitution, obj2.restitution)
        j = -(1 + e) * vel_along_normal
        j /= (1/obj1.mass + 1/obj2.mass)
        
        impulse = normal * j
        
        # Áp dụng xung lực
        if not obj1.static:
            obj1.velocity = obj1.velocity - impulse * (1/obj1.mass)
        if not obj2.static:
            obj2.velocity = obj2.velocity + impulse * (1/obj2.mass)
        
        # Ma sát
        friction = 0.1
        if not obj1.static:
            obj1.velocity = obj1.velocity * (1 - friction)
        if not obj2.static:
            obj2.velocity = obj2.velocity * (1 - friction)
    
    def update(self, objects, dt):
        """Cập nhật vật lý cho tất cả vật thể"""
        # Áp dụng trọng lực
        for obj in objects:
            if not obj.static and obj.apply_gravity:
                obj.velocity.y += self.gravity * dt
        
        # Kiểm tra va chạm
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                obj1 = objects[i]
                obj2 = objects[j]
                
                if obj1.static and obj2.static:
                    continue
                
                collision = self.check_collision(obj1, obj2)
                if collision['collision']:
                    self.resolve_collision(obj1, obj2, collision)
                    self.collisions.append({
                        'obj1': obj1,
                        'obj2': obj2,
                        'point': collision['point'],
                        'force': collision['depth'] * 100
                    })
        
        # Cập nhật vị trí
        for obj in objects:
            if not obj.static:
                obj.position = obj.position + obj.velocity * dt
                obj.velocity = obj.velocity * obj.damping

# ==================== ĐỐI TƯỢNG TRONG GAME ====================

class GameObject:
    def __init__(self, position: Vector2, radius: float = 10):
        self.position = position
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.mass = 1.0
        self.radius = radius
        self.restitution = 0.5
        self.damping = 0.99
        self.static = False
        self.apply_gravity = True
        self.color = Color(255, 255, 255)
        self.rotation = 0
        self.id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    
    def apply_force(self, force: Vector2):
        if not self.static:
            self.acceleration = self.acceleration + force * (1/self.mass)
    
    def update(self, dt):
        if not self.static:
            self.velocity = self.velocity + self.acceleration * dt
            self.position = self.position + self.velocity * dt
            self.acceleration = Vector2(0, 0)
            self.velocity = self.velocity * self.damping

class Car(GameObject):
    def __init__(self, position: Vector2, car_type: CarType = CarType.SEDAN):
        super().__init__(position)
        self.car_type = car_type
        self.width = 40
        self.height = 80
        self.radius = max(self.width, self.height) / 2
        
        # Cấu hình theo loại xe
        self.configs = {
            CarType.SEDAN: {'max_speed': 8, 'acceleration': 0.2, 'mass': 1.5, 'color': Color(0, 100, 255)},
            CarType.SUV: {'max_speed': 7, 'acceleration': 0.15, 'mass': 2.0, 'color': Color(0, 150, 0)},
            CarType.TRUCK: {'max_speed': 5, 'acceleration': 0.1, 'mass': 5.0, 'color': Color(100, 100, 100)},
            CarType.SPORTS: {'max_speed': 12, 'acceleration': 0.3, 'mass': 1.0, 'color': Color(255, 0, 0)},
            CarType.BUS: {'max_speed': 6, 'acceleration': 0.12, 'mass': 4.0, 'color': Color(255, 200, 0)},
            CarType.POLICE: {'max_speed': 9, 'acceleration': 0.25, 'mass': 1.3, 'color': Color(0, 0, 255)},
            CarType.AMBULANCE: {'max_speed': 10, 'acceleration': 0.22, 'mass': 1.4, 'color': Color(255, 255, 255)},
            CarType.FIRE_TRUCK: {'max_speed': 7, 'acceleration': 0.18, 'mass': 3.0, 'color': Color(255, 0, 0)}
        }
        
        config = self.configs[car_type]
        self.max_speed = config['max_speed']
        self.acceleration_rate = config['acceleration']
        self.mass = config['mass']
        self.color = config['color']
        
        self.speed = 0
        self.target_speed = 0
        self.steering = 0
        self.target_steering = 0
        self.steering_speed = 0.1
        self.braking = False
        self.damage = 0
        self.max_damage = 100
        self.fuel = 100
        self.is_player = False
        self.ai_controller = None
        self.path = []
        self.current_waypoint = 0
        self.brake_lights = False
        self.headlights = False
        
        # Hệ thống lái
        self.wheel_base = 70
        self.turning_radius = 5
        self.wheel_angle = 0
        self.max_wheel_angle = 30
    
    def update(self, dt):
        super().update(dt)
        
        if self.ai_controller:
            self.ai_controller.update(self, dt)
        
        # Cập nhật tốc độ
        if self.speed < self.target_speed:
            self.speed = min(self.speed + self.acceleration_rate, self.target_speed)
        elif self.speed > self.target_speed:
            self.speed = max(self.speed - self.acceleration_rate * 2, self.target_speed)
        
        # Cập nhật lái
        if self.steering < self.target_steering:
            self.steering = min(self.steering + self.steering_speed, self.target_steering)
        elif self.steering > self.target_steering:
            self.steering = max(self.steering - self.steering_speed, self.target_steering)
        
        # Áp dụng vận tốc
        rad = math.radians(self.rotation)
        self.velocity.x = math.cos(rad) * self.speed
        self.velocity.y = math.sin(rad) * self.speed
        
        # Cập nhật góc quay
        if abs(self.speed) > 0.1:
            turn_radius = self.wheel_base / math.tan(math.radians(self.steering * self.max_wheel_angle))
            if abs(turn_radius) > 0.01:
                angular_velocity = self.speed / turn_radius
                self.rotation += math.degrees(angular_velocity) * dt
        
        # Giảm nhiên liệu
        self.fuel = max(0, self.fuel - abs(self.speed) * 0.01)
        
        # Đèn phanh
        self.brake_lights = self.braking or self.speed < self.target_speed
    
    def accelerate(self, amount=1.0):
        self.target_speed = min(self.max_speed, self.target_speed + amount)
        self.braking = False
    
    def brake(self, amount=1.0):
        self.target_speed = max(-self.max_speed * 0.5, self.target_speed - amount * 2)
        self.braking = True
    
    def steer(self, amount):
        self.target_steering = max(-1, min(1, amount))
    
    def apply_damage(self, damage):
        self.damage = min(self.max_damage, self.damage + damage)
        if self.damage > 70:
            self.max_speed *= 0.7
        elif self.damage > 40:
            self.max_speed *= 0.85

class AIController:
    def __init__(self, aggression=0.5, skill=0.5):
        self.aggression = aggression  # 0-1
        self.skill = skill  # 0-1
        self.reaction_time = 0.5 + (1 - skill) * 1.0
        self.path = []
        self.target = None
        self.state = "FOLLOWING"
        self.avoidance_timer = 0
        self.lane_change_timer = 0
        self.decision_timer = 0
        
    def update(self, car, dt):
        self.decision_timer += dt
        
        if self.decision_timer > self.reaction_time:
            self.decision_timer = 0
            self.make_decision(car)
        
        self.execute_decision(car, dt)
    
    def make_decision(self, car):
        # AI logic quyết định
        if random.random() < 0.1 * self.aggression:
            self.state = "AGGRESSIVE"
        elif random.random() < 0.05:
            self.state = "LANE_CHANGE"
        else:
            self.state = "FOLLOWING"
    
    def execute_decision(self, car, dt):
        if self.state == "AGGRESSIVE":
            car.accelerate(0.2 * self.aggression)
            if random.random() < 0.3:
                car.steer(random.uniform(-0.5, 0.5))
        elif self.state == "LANE_CHANGE":
            self.lane_change_timer += dt
            if self.lane_change_timer < 2.0:
                car.steer(0.7 * random.choice([-1, 1]))
            else:
                self.lane_change_timer = 0
                self.state = "FOLLOWING"
        else:  # FOLLOWING
            car.accelerate(0.1)
            car.steer(random.uniform(-0.1, 0.1))

class TrafficSign(GameObject):
    def __init__(self, position: Vector2, sign_type: TrafficSignType):
        super().__init__(position, radius=15)
        self.sign_type = sign_type
        self.static = True
        self.apply_gravity = False
        
        self.colors = {
            TrafficSignType.STOP: Color(255, 0, 0),
            TrafficSignType.SPEED_LIMIT: Color(255, 255, 0),
            TrafficSignType.TRAFFIC_LIGHT: Color(255, 255, 255),
            TrafficSignType.YIELD: Color(255, 255, 0),
            TrafficSignType.PEDESTRIAN: Color(255, 255, 0),
            TrafficSignType.SCHOOL: Color(255, 255, 0),
            TrafficSignType.CONSTRUCTION: Color(255, 165, 0),
            TrafficSignType.NO_ENTRY: Color(255, 0, 0)
        }
        
        self.color = self.colors.get(sign_type, Color(255, 255, 255))
        self.text = {
            TrafficSignType.STOP: "STOP",
            TrafficSignType.SPEED_LIMIT: "60",
            TrafficSignType.YIELD: "YIELD",
            TrafficSignType.PEDESTRIAN: "🚶",
            TrafficSignType.SCHOOL: "SCHOOL",
            TrafficSignType.CONSTRUCTION: "🚧",
            TrafficSignType.NO_ENTRY: "🚫"
        }.get(sign_type, "")

class TrafficLight(GameObject):
    def __init__(self, position: Vector2):
        super().__init__(position, radius=10)
        self.static = True
        self.state = "RED"  # RED, YELLOW, GREEN
        self.timer = 0
        self.cycle_time = random.uniform(10, 20)
        self.light_duration = {
            "RED": 10,
            "YELLOW": 3,
            "GREEN": 10
        }
        
    def update(self, dt):
        super().update(dt)
        self.timer += dt
        
        if self.timer >= self.light_duration[self.state]:
            self.timer = 0
            if self.state == "RED":
                self.state = "GREEN"
            elif self.state == "GREEN":
                self.state = "YELLOW"
            else:
                self.state = "RED"

class Building(GameObject):
    def __init__(self, position: Vector2, width=60, height=80, floors=2):
        super().__init__(position, radius=max(width, height)/2)
        self.width = width
        self.height = height
        self.floors = floors
        self.static = True
        self.apply_gravity = False
        self.type = random.choice(["house", "apartment", "office", "shop", "factory"])
        
        colors = {
            "house": [Color(255, 200, 150), Color(200, 150, 100)],
            "apartment": [Color(200, 200, 200), Color(150, 150, 150)],
            "office": [Color(100, 150, 255), Color(50, 100, 200)],
            "shop": [Color(255, 100, 100), Color(200, 50, 50)],
            "factory": [Color(100, 100, 100), Color(50, 50, 50)]
        }
        
        self.color = random.choice(colors.get(self.type, [Color(150, 150, 150)]))
        self.window_color = Color(200, 200, 255)
        self.roof_color = Color(100, 50, 0) if self.type == "house" else Color(50, 50, 50)

class Tree(GameObject):
    def __init__(self, position: Vector2):
        super().__init__(position, radius=20)
        self.static = True
        self.apply_gravity = False
        self.type = random.choice(["pine", "oak", "palm", "bush"])
        
        colors = {
            "pine": Color(0, 100, 0),
            "oak": Color(0, 150, 0),
            "palm": Color(0, 200, 0),
            "bush": Color(0, 120, 0)
        }
        
        self.color = colors.get(self.type, Color(0, 150, 0))
        self.trunk_color = Color(101, 67, 33)

# ==================== HỆ THỐNG BẢN ĐỒ ====================

class MapGenerator:
    def __init__(self, width=2000, height=2000, seed=None):
        self.width = width
        self.height = height
        self.seed = seed if seed else random.randint(0, 1000000)
        random.seed(self.seed)
        
        self.roads = []
        self.buildings = []
        self.trees = []
        self.traffic_signs = []
        self.traffic_lights = []
        self.intersections = []
        
        # Tạo thành phố
        self.generate_city()
        self.generate_highways()
        self.generate_countryside()
        self.generate_special_areas()
    
    def generate_city(self):
        """Tạo khu vực thành phố"""
        city_center = Vector2(self.width/2, self.height/2)
        city_radius = 400
        
        # Tạo đường phố theo grid
        for x in range(-5, 6):
            for y in range(-5, 6):
                road_x = city_center.x + x * 80
                road_y = city_center.y + y * 80
                
                # Đường ngang
                if abs(y) < 5:
                    self.roads.append({
                        'type': RoadType.CITY_STREET,
                        'start': Vector2(road_x - 200, road_y),
                        'end': Vector2(road_x + 200, road_y),
                        'width': 40,
                        'lanes': 2
                    })
                
                # Đường dọc
                if abs(x) < 5:
                    self.roads.append({
                        'type': RoadType.CITY_STREET,
                        'start': Vector2(road_x, road_y - 200),
                        'end': Vector2(road_x, road_y + 200),
                        'width': 40,
                        'lanes': 2
                    })
                
                # Giao lộ
                if abs(x) < 5 and abs(y) < 5:
                    self.intersections.append(Vector2(road_x, road_y))
                    
                    # Đèn giao thông
                    if random.random() < 0.7:
                        self.traffic_lights.append(TrafficLight(Vector2(road_x, road_y)))
                    
                    # Biển báo
                    if random.random() < 0.5:
                        sign_type = random.choice(list(TrafficSignType))
                        self.traffic_signs.append(TrafficSign(
                            Vector2(road_x + random.uniform(-30, 30), 
                                   road_y + random.uniform(-30, 30)),
                            sign_type
                        ))
        
        # Tạo nhà cửa
        for _ in range(100):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(100, city_radius)
            pos = Vector2(
                city_center.x + math.cos(angle) * distance,
                city_center.y + math.sin(angle) * distance
            )
            
            # Kiểm tra không quá gần đường
            near_road = False
            for road in self.roads:
                if pos.distance_to(road['start']) < 50 or pos.distance_to(road['end']) < 50:
                    near_road = True
                    break
            
            if not near_road:
                self.buildings.append(Building(
                    pos,
                    width=random.randint(40, 80),
                    height=random.randint(50, 100),
                    floors=random.randint(1, 5)
                ))
    
    def generate_highways(self):
        """Tạo đường cao tốc"""
        # Highway chính (ngang)
        self.roads.append({
            'type': RoadType.HIGHWAY,
            'start': Vector2(100, self.height/2),
            'end': Vector2(self.width - 100, self.height/2),
            'width': 80,
            'lanes': 4
        })
        
        # Highway phụ (dọc)
        self.roads.append({
            'type': RoadType.HIGHWAY,
            'start': Vector2(self.width/2, 100),
            'end': Vector2(self.width/2, self.height - 100),
            'width': 80,
            'lanes': 4
        })
        
        # Đường nhánh
        for i in range(4):
            angle = i * math.pi/2
            length = 300
            
            start = Vector2(
                self.width/2 + math.cos(angle) * 200,
                self.height/2 + math.sin(angle) * 200
            )
            
            end = Vector2(
                start.x + math.cos(angle + math.pi/4) * length,
                start.y + math.sin(angle + math.pi/4) * length
            )
            
            self.roads.append({
                'type': RoadType.HIGHWAY,
                'start': start,
                'end': end,
                'width': 60,
                'lanes': 3
            })
    
    def generate_countryside(self):
        """Tạo khu vực nông thôn"""
        for _ in range(200):
            # Chọn vị trí xa trung tâm
            margin = 200
            pos = Vector2(
                random.uniform(margin, self.width - margin),
                random.uniform(margin, self.height - margin)
            )
            
            # Kiểm tra không quá gần thành phố
            city_center = Vector2(self.width/2, self.height/2)
            if pos.distance_to(city_center) > 500:
                if random.random() < 0.7:
                    self.trees.append(Tree(pos))
                else:
                    # Nhà nhỏ ở nông thôn
                    self.buildings.append(Building(
                        pos,
                        width=random.randint(30, 60),
                        height=random.randint(40, 80),
                        floors=1
                    ))
    
    def generate_special_areas(self):
        """Tạo khu vực đặc biệt"""
        # Công viên
        park_center = Vector2(self.width * 0.7, self.height * 0.3)
        park_size = 150
        
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, park_size)
            pos = Vector2(
                park_center.x + math.cos(angle) * distance,
                park_center.y + math.sin(angle) * distance
            )
            self.trees.append(Tree(pos))
        
        # Khu công nghiệp
        industrial_center = Vector2(self.width * 0.3, self.height * 0.7)
        
        for i in range(5):
            for j in range(5):
                pos = Vector2(
                    industrial_center.x + i * 100 - 200,
                    industrial_center.y + j * 80 - 160
                )
                self.buildings.append(Building(
                    pos,
                    width=80,
                    height=60,
                    floors=random.randint(2, 4)
                ))
        
        # Cầu
        bridge_start = Vector2(self.width * 0.4, self.height * 0.8)
        bridge_end = Vector2(self.width * 0.6, self.height * 0.8)
        
        self.roads.append({
            'type': RoadType.BRIDGE,
            'start': bridge_start,
            'end': bridge_end,
            'width': 50,
            'lanes': 2,
            'bridge': True
        })
        
        # Đường hầm
        tunnel_start = Vector2(self.width * 0.2, self.height * 0.4)
        tunnel_end = Vector2(self.width * 0.2, self.height * 0.6)
        
        self.roads.append({
            'type': RoadType.TUNNEL,
            'start': tunnel_start,
            'end': tunnel_end,
            'width': 40,
            'lanes': 2,
            'tunnel': True
        })

# ==================== HỆ THỐNG THỜI TIẾT ====================

class WeatherSystem:
    def __init__(self):
        self.weather = WeatherType.SUNNY
        self.temperature = 25  # °C
        self.humidity = 50  # %
        self.wind_speed = 5  # km/h
        self.wind_direction = 0  # degrees
        self.rain_intensity = 0  # 0-1
        self.fog_density = 0  # 0-1
        self.time_of_day = 12  # 0-24
        self.day_night_cycle = True
        self.season = "SUMMER"  # SPRING, SUMMER, AUTUMN, WINTER
        
    def update(self, dt):
        if self.day_night_cycle:
            self.time_of_day = (self.time_of_day + dt * 0.1) % 24
            
            # Thay đổi nhiệt độ theo thời gian
            if 6 <= self.time_of_day < 18:
                self.temperature = 25 + math.sin((self.time_of_day - 12) * math.pi / 12) * 5
            else:
                self.temperature = 20 - math.sin((self.time_of_day - 0) * math.pi / 12) * 5
        
        # Thay đổi thời tiết ngẫu nhiên
        if random.random() < 0.001:
            self.change_weather(random.choice(list(WeatherType)))
    
    def change_weather(self, new_weather):
        self.weather = new_weather
        
        if new_weather == WeatherType.RAINY:
            self.rain_intensity = random.uniform(0.3, 1.0)
            self.humidity = 90
            self.temperature -= 5
        elif new_weather == WeatherType.FOGGY:
            self.fog_density = random.uniform(0.3, 0.8)
            self.humidity = 80
        elif new_weather == WeatherType.STORMY:
            self.rain_intensity = 1.0
            self.wind_speed = random.uniform(20, 50)
            self.temperature -= 3
        elif new_weather == WeatherType.SUNNY:
            self.rain_intensity = 0
            self.fog_density = 0
            self.humidity = 40
            self.temperature += 2
    
    def get_weather_effect(self):
        """Trả về hiệu ứng thời tiết"""
        effects = []
        
        if self.weather == WeatherType.RAINY:
            effects.append({
                'type': 'rain',
                'intensity': self.rain_intensity,
                'effect': 'reduced_traction'
            })
        
        if self.weather == WeatherType.FOGGY:
            effects.append({
                'type': 'fog',
                'density': self.fog_density,
                'effect': 'reduced_visibility'
            })
        
        if self.weather == WeatherType.STORMY:
            effects.append({
                'type': 'storm',
                'intensity': 1.0,
                'effect': 'strong_wind'
            })
        
        if self.time_of_day < 6 or self.time_of_day > 20:
            effects.append({
                'type': 'darkness',
                'intensity': 0.8,
                'effect': 'reduced_visibility'
            })
        
        return effects

# ==================== HỆ THỐNG HIỆU ỨNG ====================

class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.emitters = []
        
    class Particle:
        def __init__(self, position, velocity, color, size, lifetime):
            self.position = position
            self.velocity = velocity
            self.color = color
            self.size = size
            self.lifetime = lifetime
            self.max_lifetime = lifetime
            self.alive = True
        
        def update(self, dt):
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.alive = False
                return
            
            # Cập nhật vị trí
            self.position = self.position + self.velocity * dt
            
            # Giảm kích thước
            self.size = max(0, self.size * (self.lifetime / self.max_lifetime))
            
            # Thêm trọng lực
            self.velocity.y += 9.81 * dt * 0.1
    
    def create_explosion(self, position, intensity=1.0):
        """Tạo hiệu ứng nổ"""
        particle_count = int(50 * intensity)
        
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5) * intensity
            velocity = Vector2(
                math.cos(angle) * speed,
                math.sin(angle) * speed
            )
            
            color = random.choice([
                Color(255, 100, 0),
                Color(255, 200, 0),
                Color(255, 50, 0)
            ])
            
            particle = self.Particle(
                position,
                velocity,
                color,
                size=random.uniform(2, 6) * intensity,
                lifetime=random.uniform(0.5, 1.5)
            )
            
            self.particles.append(particle)
    
    def create_smoke(self, position, color=None):
        """Tạo hiệu ứng khói"""
        if color is None:
            color = Color(100, 100, 100, 150)
        
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.1, 0.5)
            velocity = Vector2(
                math.cos(angle) * speed,
                math.sin(angle) * speed - 0.5  # Khói bay lên
            )
            
            particle = self.Particle(
                position,
                velocity,
                color,
                size=random.uniform(3, 8),
                lifetime=random.uniform(2, 4)
            )
            
            self.particles.append(particle)
    
    def create_tire_marks(self, position, direction):
        """Tạo vết lốp"""
        for _ in range(3):
            offset = Vector2(
                random.uniform(-5, 5),
                random.uniform(-5, 5)
            )
            
            particle = self.Particle(
                position + offset,
                direction * 0.1,
                Color(50, 50, 50, 200),
                size=random.uniform(2, 4),
                lifetime=random.uniform(5, 10)
            )
            
            self.particles.append(particle)
    
    def update(self, dt):
        # Cập nhật tất cả particle
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.alive:
                self.particles.remove(particle)

# ==================== HỆ THỐNG GAME CHÍNH ====================

class Game:
    def __init__(self):
        self.width = 2000
        self.height = 2000
        self.map_generator = MapGenerator(self.width, self.height)
        self.physics_engine = PhysicsEngine()
        self.weather_system = WeatherSystem()
        self.particle_system = ParticleSystem()
        
        self.player = None
        self.ai_cars = []
        self.game_objects = []
        self.road_network = []
        self.game_time = 0
        self.score = 0
        self.camera_position = Vector2(self.width/2, self.height/2)
        self.camera_zoom = 1.0
        self.game_state = "MENU"  # MENU, PLAYING, PAUSED, GAME_OVER
        self.difficulty = "NORMAL"
        self.mission = None
        
        # Thống kê
        self.stats = {
            'total_crashes': 0,
            'total_distance': 0,
            'max_speed': 0,
            'cars_destroyed': 0,
            'play_time': 0
        }
        
        # Tạo bản đồ
        self.generate_map()
    
    def generate_map(self):
        """Tạo toàn bộ bản đồ"""
        # Thêm tất cả đối tượng vào game
        self.game_objects = []
        
        # Thêm buildings
        self.game_objects.extend(self.map_generator.buildings)
        
        # Thêm trees
        self.game_objects.extend(self.map_generator.trees)
        
        # Thêm traffic signs
        self.game_objects.extend(self.map_generator.traffic_signs)
        
        # Thêm traffic lights
        self.game_objects.extend(self.map_generator.traffic_lights)
        
        # Tạo đường
        self.road_network = self.map_generator.roads
        
        # Tạo player car
        self.spawn_player()
        
        # Tạo AI cars
        self.spawn_ai_cars(20)
    
    def spawn_player(self):
        """Tạo xe cho người chơi"""
        start_pos = Vector2(self.width/2, self.height/2)
        self.player = Car(start_pos, CarType.SEDAN)
        self.player.is_player = True
        self.player.color = Color(0, 100, 255)  # Xe màu xanh dương
        self.game_objects.append(self.player)
    
    def spawn_ai_cars(self, count):
        """Tạo các xe AI"""
        for _ in range(count):
            # Chọn vị trí ngẫu nhiên trên đường
            road = random.choice(self.road_network)
            t = random.random()
            pos = Vector2(
                road['start'].x + (road['end'].x - road['start'].x) * t,
                road['start'].y + (road['end'].y - road['start'].y) * t
            )
            
            car_type = random.choice(list(CarType))
            ai_car = Car(pos, car_type)
            ai_car.ai_controller = AIController(
                aggression=random.uniform(0.3, 0.8),
                skill=random.uniform(0.4, 0.9)
            )
            ai_car.rotation = random.uniform(0, 360)
            
            self.ai_cars.append(ai_car)
            self.game_objects.append(ai_car)
    
    def update(self, dt):
        """Cập nhật trạng thái game"""
        if self.game_state != "PLAYING":
            return
        
        self.game_time += dt
        self.stats['play_time'] += dt
        
        # Cập nhật thời tiết
        self.weather_system.update(dt)
        
        # Cập nhật vật lý
        self.physics_engine.update(self.game_objects, dt)
        
        # Cập nhật particle system
        self.particle_system.update(dt)
        
        # Cập nhật traffic lights
        for obj in self.game_objects:
            if isinstance(obj, TrafficLight):
                obj.update(dt)
        
        # Cập nhật AI cars
        for ai_car in self.ai_cars:
            ai_car.update(dt)
            
            # Kiểm tra va chạm với player
            if ai_car != self.player:
                collision = self.physics_engine.check_collision(ai_car, self.player)
                if collision['collision']:
                    self.handle_collision(ai_car, self.player, collision)
        
        # Cập nhật player
        if self.player:
            self.player.update(dt)
            
            # Cập nhật thống kê
            speed = self.player.speed
            if speed > self.stats['max_speed']:
                self.stats['max_speed'] = speed
            
            # Cập nhật khoảng cách
            self.stats['total_distance'] += abs(speed) * dt
            
            # Kiểm tra nhiên liệu
            if self.player.fuel <= 0:
                self.player.speed *= 0.9
            
            # Kiểm tra hư hại
            if self.player.damage >= 100:
                self.game_state = "GAME_OVER"
                
                # Tạo hiệu ứng nổ
                self.particle_system.create_explosion(self.player.position, 1.5)
        
        # Kiểm tra va chạm giữa các AI cars
        for i in range(len(self.ai_cars)):
            for j in range(i + 1, len(self.ai_cars)):
                car1 = self.ai_cars[i]
                car2 = self.ai_cars[j]
                
                collision = self.physics_engine.check_collision(car1, car2)
                if collision['collision']:
                    self.handle_collision(car1, car2, collision)
    
    def handle_collision(self, car1, car2, collision_data):
        """Xử lý va chạm giữa hai xe"""
        # Tính toán damage
        relative_speed = car1.velocity.magnitude() + car2.velocity.magnitude()
        damage = min(relative_speed * 10, 50)
        
        car1.apply_damage(damage)
        car2.apply_damage(damage)
        
        # Cập nhật thống kê
        self.stats['total_crashes'] += 1
        
        # Tạo hiệu ứng
        self.particle_system.create_explosion(collision_data['point'], damage/50)
        
        # Tạo khói
        self.particle_system.create_smoke(car1.position)
        self.particle_system.create_smoke(car2.position)
        
        # Tạo vết lốp
        if isinstance(car1, Car):
            self.particle_system.create_tire_marks(car1.position, car1.velocity)
        if isinstance(car2, Car):
            self.particle_system.create_tire_marks(car2.position, car2.velocity)
        
        # Kiểm tra xe bị phá hủy
        if car1.damage >= 100:
            self.stats['cars_destroyed'] += 1
        if car2.damage >= 100:
            self.stats['cars_destroyed'] += 1
        
        # Cập nhật điểm
        self.score = int(self.stats['total_distance'] / 10 + 
                        self.stats['max_speed'] * 5 + 
                        self.game_time * 2)
    
    def handle_input(self, key):
        """Xử lý input từ người chơi"""
        if not self.player:
            return
        
        if key == "UP":
            self.player.accelerate()
        elif key == "DOWN":
            self.player.brake()
        elif key == "LEFT":
            self.player.steer(-1)
        elif key == "RIGHT":
            self.player.steer(1)
        elif key == "SPACE":
            self.player.brake(2.0)  # Phanh khẩn cấp
        elif key == "LIGHTS":
            self.player.headlights = not self.player.headlights
        elif key == "HORN":
            # Còi xe
            pass
    
    def get_game_data(self):
        """Lấy dữ liệu game để hiển thị"""
        return {
            'player': self.player,
            'ai_cars': self.ai_cars,
            'game_objects': self.game_objects,
            'roads': self.road_network,
            'particles': self.particle_system.particles,
            'weather': self.weather_system,
            'stats': self.stats,
            'score': self.score,
            'game_time': self.game_time,
            'camera_position': self.camera_position,
            'camera_zoom': self.camera_zoom
        }

# ==================== GIAO DIỆN STREAMLIT ====================

def main():
    # Khởi tạo game
    if 'game' not in st.session_state:
        st.session_state.game = Game()
    
    game = st.session_state.game
    
    # CSS tùy chỉnh
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1E88E5;
        padding: 20px;
        background: linear-gradient(90deg, #1E88E5, #0D47A1);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .game-stats {
        background-color: #0A1929;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #1E88E5;
        margin: 10px 0;
    }
    .control-panel {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #FF9800;
    }
    .car-info {
        background-color: #0D1117;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF5722;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚗 CAR CRASH SIMULATOR ULTIMATE</h1>
        <p>Trò chơi mô phỏng lái xe với vật lý va chạm thực tế</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🎮 ĐIỀU KHIỂN")
        
        if game.game_state == "MENU":
            if st.button("🎮 BẮT ĐẦU CHƠI", type="primary", use_container_width=True):
                game.game_state = "PLAYING"
                st.rerun()
            
            st.markdown("---")
            st.subheader("📊 CÀI ĐẶT")
            
            difficulty = st.selectbox(
                "Độ khó",
                ["DỄ", "TRUNG BÌNH", "KHÓ", "CỰC KHÓ"],
                index=1
            )
            game.difficulty = difficulty
            
            weather = st.selectbox(
                "Thời tiết",
                ["NẮNG", "MƯA", "SƯƠNG MÙ", "BÃO", "ĐÊM"],
                index=0
            )
            
            traffic_density = st.slider("Mật độ giao thông", 1, 100, 50)
            
            st.markdown("---")
            st.subheader("🚗 CHỌN XE")
            
            car_type = st.selectbox(
                "Loại xe",
                ["SEDAN", "SUV", "TRUCK", "SPORTS", "BUS", "POLICE", "AMBULANCE", "FIRE_TRUCK"],
                index=0
            )
            
            if st.button("ÁP DỤNG CÀI ĐẶT", use_container_width=True):
                st.rerun()
        
        elif game.game_state == "PLAYING":
            # Điều khiển game
            st.markdown("### 🎮 ĐIỀU KHIỂN XE")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⬆️", use_container_width=True):
                    game.handle_input("UP")
            with col2:
                if st.button("⬇️", use_container_width=True):
                    game.handle_input("DOWN")
            with col3:
                if st.button("⏹️", use_container_width=True):
                    game.game_state = "PAUSED"
                    st.rerun()
            
            col4, col5, col6 = st.columns(3)
            with col4:
                if st.button("⬅️", use_container_width=True):
                    game.handle_input("LEFT")
            with col5:
                if st.button("🔄", use_container_width=True):
                    game.player.steer(0)
            with col6:
                if st.button("➡️", use_container_width=True):
                    game.handle_input("RIGHT")
            
            st.markdown("---")
            
            # Thông tin xe
            if game.player:
                st.markdown("### 🚗 THÔNG TIN XE")
                
                # Thanh nhiên liệu
                fuel_percent = game.player.fuel
                st.progress(fuel_percent/100, f"⛽ Nhiên liệu: {fuel_percent:.1f}%")
                
                # Thanh hư hại
                damage_percent = game.player.damage
                st.progress(damage_percent/100, f"⚠️ Hư hại: {damage_percent:.1f}%")
                
                # Tốc độ
                speed_kmh = game.player.speed * 20
                st.metric("📊 Tốc độ", f"{speed_kmh:.1f} km/h")
                
                # Góc lái
                st.metric("🎛️ Góc lái", f"{game.player.steering * 30:.1f}°")
    
    # Main content
    if game.game_state == "MENU":
        show_main_menu(game)
    elif game.game_state == "PLAYING":
        show_game_screen(game)
    elif game.game_state == "PAUSED":
        show_pause_menu(game)
    elif game.game_state == "GAME_OVER":
        show_game_over(game)

def show_main_menu(game):
    """Hiển thị màn hình chính"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 40px;'>
            <h2>🎮 BẮT ĐẦU CUỘC PHIÊU LƯU</h2>
            <p>Điều khiển xe của bạn trong thành phố rộng lớn với:</p>
            <ul style='text-align: left;'>
                <li>🚗 Hệ thống vật lý va chạm thực tế</li>
                <li>🏙️ Thành phố rộng 2000x2000 pixels</li>
                <li>🚦 Hệ thống giao thông thông minh</li>
                <li>🌧️ Hệ thống thời tiết động</li>
                <li>🤖 Xe AI với hành vi phức tạp</li>
                <li>🏢 Hơn 100 tòa nhà và cơ sở hạ tầng</li>
                <li>🌳 Hệ thống cây cối và môi trường</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Hiển thị bản đồ preview
        st.markdown("### 🗺️ BẢN ĐỒ THẾ GIỚI")
        
        # Tạo hình ảnh bản đồ
        fig = go.Figure()
        
        # Vẽ đường
        for road in game.map_generator.roads:
            fig.add_trace(go.Scatter(
                x=[road['start'].x, road['end'].x],
                y=[road['start'].y, road['end'].y],
                mode='lines',
                line=dict(
                    color='gray' if road['type'] == RoadType.CITY_STREET else 'black',
                    width=road['width']/10
                ),
                name=str(road['type'].value),
                hoverinfo='text',
                text=f"Đường {road['type'].value}"
            ))
        
        # Vẽ buildings
        building_x = [b.position.x for b in game.map_generator.buildings]
        building_y = [b.position.y for b in game.map_generator.buildings]
        building_colors = [b.color.to_hex() for b in game.map_generator.buildings]
        
        fig.add_trace(go.Scatter(
            x=building_x,
            y=building_y,
            mode='markers',
            marker=dict(
                size=10,
                color=building_colors,
                symbol='square'
            ),
            name='Tòa nhà',
            hoverinfo='text',
            text=[f"Tòa nhà {i+1}" for i in range(len(building_x))]
        ))
        
        # Cập nhật layout
        fig.update_layout(
            title="Bản đồ thế giới game",
            xaxis=dict(title='X', range=[0, game.width]),
            yaxis=dict(title='Y', range=[0, game.height]),
            showlegend=True,
            height=600,
            plot_bgcolor='lightblue'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_game_screen(game):
    """Hiển thị màn hình game"""
    # Cập nhật game
    game.update(0.016)  # ~60 FPS
    
    # Tạo container cho game
    game_container = st.container()
    
    with game_container:
        # Hiển thị thông tin game
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏆 ĐIỂM SỐ", f"{game.score:,}")
        
        with col2:
            st.metric("⏱️ THỜI GIAN", f"{game.game_time:.1f}s")
        
        with col3:
            weather_text = {
                WeatherType.SUNNY: "☀️ NẮNG",
                WeatherType.RAINY: "🌧️ MƯA",
                WeatherType.FOGGY: "🌫️ SƯƠNG MÙ",
                WeatherType.NIGHT: "🌃 ĐÊM",
                WeatherType.STORMY: "⛈️ BÃO"
            }
            st.metric("🌤️ THỜI TIẾT", weather_text.get(game.weather_system.weather, "☀️"))
        
        with col4:
            hour = int(game.weather_system.time_of_day)
            minute = int((game.weather_system.time_of_day - hour) * 60)
            st.metric("🕐 THỜI GIAN", f"{hour:02d}:{minute:02d}")
        
        # Vẽ bản đồ game
        draw_game_map(game)
        
        # Hiển thị thống kê chi tiết
        with st.expander("📊 THỐNG KÊ CHI TIẾT", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💥 SỐ VỤ VA CHẠM", game.stats['total_crashes'])
                st.metric("🚗 XE BỊ PHÁ HỦY", game.stats['cars_destroyed'])
            
            with col2:
                st.metric("📏 QUÃNG ĐƯỜNG", f"{game.stats['total_distance']:.1f}m")
                st.metric("⚡ TỐC ĐỘ TỐI ĐA", f"{game.stats['max_speed'] * 20:.1f} km/h")
            
            with col3:
                st.metric("🎮 THỜI GIAN CHƠI", f"{game.stats['play_time']:.1f}s")
                st.metric("🎯 ĐỘ KHÓ", game.difficulty)

def draw_game_map(game):
    """Vẽ bản đồ game với Plotly"""
    data = game.get_game_data()
    
    # Tạo figure
    fig = go.Figure()
    
    # Tính toán viewport dựa trên camera
    view_width = 800 / game.camera_zoom
    view_height = 600 / game.camera_zoom
    
    view_x_min = game.camera_position.x - view_width/2
    view_x_max = game.camera_position.x + view_width/2
    view_y_min = game.camera_position.y - view_height/2
    view_y_max = game.camera_position.y + view_height/2
    
    # Vẽ đường trong viewport
    for road in data['roads']:
        if (view_x_min <= road['start'].x <= view_x_max or 
            view_x_min <= road['end'].x <= view_x_max or
            view_y_min <= road['start'].y <= view_y_max or
            view_y_min <= road['end'].y <= view_y_max):
            
            road_color = {
                RoadType.HIGHWAY: 'black',
                RoadType.CITY_STREET: 'gray',
                RoadType.COUNTRY_ROAD: 'brown',
                RoadType.BRIDGE: 'blue',
                RoadType.TUNNEL: 'darkgray'
            }.get(road['type'], 'gray')
            
            fig.add_trace(go.Scatter(
                x=[road['start'].x, road['end'].x],
                y=[road['start'].y, road['end'].y],
                mode='lines',
                line=dict(color=road_color, width=road['width']/10),
                opacity=0.8,
                showlegend=False
            ))
    
    # Vẽ buildings
    building_x = []
    building_y = []
    building_colors = []
    building_text = []
    
    for obj in data['game_objects']:
        if isinstance(obj, Building):
            if (view_x_min <= obj.position.x <= view_x_max and 
                view_y_min <= obj.position.y <= view_y_max):
                building_x.append(obj.position.x)
                building_y.append(obj.position.y)
                building_colors.append(obj.color.to_hex())
                building_text.append(f"Tòa nhà ({obj.type})")
    
    if building_x:
        fig.add_trace(go.Scatter(
            x=building_x,
            y=building_y,
            mode='markers',
            marker=dict(
                size=15,
                color=building_colors,
                symbol='square',
                line=dict(width=1, color='black')
            ),
            text=building_text,
            hoverinfo='text',
            showlegend=False
        ))
    
    # Vẽ cây
    tree_x = []
    tree_y = []
    tree_colors = []
    
    for obj in data['game_objects']:
        if isinstance(obj, Tree):
            if (view_x_min <= obj.position.x <= view_x_max and 
                view_y_min <= obj.position.y <= view_y_max):
                tree_x.append(obj.position.x)
                tree_y.append(obj.position.y)
                tree_colors.append(obj.color.to_hex())
    
    if tree_x:
        fig.add_trace(go.Scatter(
            x=tree_x,
            y=tree_y,
            mode='markers',
            marker=dict(
                size=12,
                color=tree_colors,
                symbol='circle',
                opacity=0.8
            ),
            showlegend=False
        ))
    
    # Vẽ biển báo
    sign_x = []
    sign_y = []
    sign_colors = []
    sign_text = []
    
    for obj in data['game_objects']:
        if isinstance(obj, TrafficSign):
            if (view_x_min <= obj.position.x <= view_x_max and 
                view_y_min <= obj.position.y <= view_y_max):
                sign_x.append(obj.position.x)
                sign_y.append(obj.position.y)
                sign_colors.append(obj.color.to_hex())
                sign_text.append(obj.sign_type.value)
    
    if sign_x:
        fig.add_trace(go.Scatter(
            x=sign_x,
            y=sign_y,
            mode='markers+text',
            marker=dict(
                size=10,
                color=sign_colors,
                symbol='diamond',
                line=dict(width=1, color='white')
            ),
            text=sign_text,
            textposition="top center",
            textfont=dict(size=8, color='black'),
            hoverinfo='text',
            showlegend=False
        ))
    
    # Vẽ đèn giao thông
    light_x = []
    light_y = []
    light_colors = []
    
    for obj in data['game_objects']:
        if isinstance(obj, TrafficLight):
            if (view_x_min <= obj.position.x <= view_x_max and 
                view_y_min <= obj.position.y <= view_y_max):
                light_x.append(obj.position.x)
                light_y.append(obj.position.y)
                light_colors.append({
                    'RED': 'red',
                    'YELLOW': 'yellow',
                    'GREEN': 'green'
                }.get(obj.state, 'gray'))
    
    if light_x:
        fig.add_trace(go.Scatter(
            x=light_x,
            y=light_y,
            mode='markers',
            marker=dict(
                size=8,
                color=light_colors,
                symbol='circle',
                line=dict(width=2, color='black')
            ),
            showlegend=False
        ))
    
    # Vẽ xe AI
    ai_x = []
    ai_y = []
    ai_colors = []
    ai_text = []
    
    for car in data['ai_cars']:
        if (view_x_min <= car.position.x <= view_x_max and 
            view_y_min <= car.position.y <= view_y_max):
            ai_x.append(car.position.x)
            ai_y.append(car.position.y)
            ai_colors.append(car.color.to_hex())
            ai_text.append(f"Xe AI ({car.car_type.value}) - HP: {100 - car.damage:.0f}%")
    
    if ai_x:
        fig.add_trace(go.Scatter(
            x=ai_x,
            y=ai_y,
            mode='markers',
            marker=dict(
                size=12,
                color=ai_colors,
                symbol='triangle-right',
                angle=[car.rotation for car in data['ai_cars'] if 
                      view_x_min <= car.position.x <= view_x_max and 
                      view_y_min <= car.position.y <= view_y_max],
                line=dict(width=2, color='black')
            ),
            text=ai_text,
            hoverinfo='text',
            showlegend=False
        ))
    
    # Vẽ xe player
    if data['player']:
        player = data['player']
        fig.add_trace(go.Scatter(
            x=[player.position.x],
            y=[player.position.y],
            mode='markers+text',
            marker=dict(
                size=20,
                color=player.color.to_hex(),
                symbol='triangle-right',
                angle=player.rotation,
                line=dict(width=3, color='yellow')
            ),
            text=["BẠN"],
            textposition="top center",
            textfont=dict(size=12, color='white', weight='bold'),
            showlegend=False
        ))
    
    # Vẽ particles
    particle_x = []
    particle_y = []
    particle_colors = []
    particle_sizes = []
    
    for particle in data['particles']:
        particle_x.append(particle.position.x)
        particle_y.append(particle.position.y)
        particle_colors.append(particle.color.to_hex())
        particle_sizes.append(particle.size * 2)
    
    if particle_x:
        fig.add_trace(go.Scatter(
            x=particle_x,
            y=particle_y,
            mode='markers',
            marker=dict(
                size=particle_sizes,
                color=particle_colors,
                opacity=0.6,
                symbol='circle'
            ),
            showlegend=False
        ))
    
    # Cập nhật layout
    fig.update_layout(
        title=f"Car Crash Simulator - Camera Zoom: {game.camera_zoom:.1f}x",
        xaxis=dict(
            title='X',
            range=[view_x_min, view_x_max],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            title='Y',
            range=[view_y_min, view_y_max],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        showlegend=False,
        height=700,
        margin=dict(l=0, r=0, t=50, b=0),
        plot_bgcolor='lightblue' if game.weather_system.weather == WeatherType.SUNNY else 'gray'
    )
    
    # Hiển thị figure
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    
    # Điều khiển camera
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Phóng to"):
            game.camera_zoom = min(3.0, game.camera_zoom * 1.2)
    
    with col2:
        if st.button("🔍 Thu nhỏ"):
            game.camera_zoom = max(0.5, game.camera_zoom / 1.2)
    
    with col3:
        if st.button("🗺️ Reset view"):
            if game.player:
                game.camera_position = game.player.position
            game.camera_zoom = 1.0
    
    with col4:
        if st.button("⏸️ Tạm dừng"):
            game.game_state = "PAUSED"
            st.rerun()

def show_pause_menu(game):
    """Hiển thị menu tạm dừng"""
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>⏸️ TRÒ CHƠI ĐANG TẠM DỪNG</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("▶️ TIẾP TỤC CHƠI", type="primary", use_container_width=True, size="large"):
            game.game_state = "PLAYING"
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🔄 CHƠI LẠI TỪ ĐẦU", use_container_width=True):
            st.session_state.game = Game()
            st.rerun()
        
        if st.button("🏠 VỀ MENU CHÍNH", use_container_width=True):
            game.game_state = "MENU"
            st.rerun()
        
        if st.button("💾 LƯU TIẾN TRÌNH", use_container_width=True):
            # Lưu game
            game_data = {
                'score': game.score,
                'game_time': game.game_time,
                'player_damage': game.player.damage if game.player else 0,
                'player_fuel': game.player.fuel if game.player else 100,
                'stats': game.stats
            }
            st.success(f"Đã lưu tiến trình! Điểm: {game.score}")
        
        st.markdown("---")
        
        # Hiển thị thống kê hiện tại
        st.markdown("### 📊 THỐNG KÊ HIỆN TẠI")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.metric("🏆 Điểm số", f"{game.score:,}")
            st.metric("⏱️ Thời gian", f"{game.game_time:.1f}s")
            st.metric("🚗 Số xe AI", len(game.ai_cars))
        
        with col_b:
            st.metric("💥 Va chạm", game.stats['total_crashes'])
            st.metric("📏 Quãng đường", f"{game.stats['total_distance']:.1f}m")
            st.metric("⚡ Tốc độ tối đa", f"{game.stats['max_speed'] * 20:.1f} km/h")

def show_game_over(game):
    """Hiển thị màn hình game over"""
    st.markdown(f"""
    <div style='text-align: center; padding: 50px; background-color: #ff000020; border-radius: 15px;'>
        <h1>💥 GAME OVER</h1>
        <h2>Xe của bạn đã bị phá hủy hoàn toàn!</h2>
        <h3>🏆 ĐIỂM CUỐI CÙNG: {game.score:,}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Hiển thị thống kê chi tiết
        st.markdown("### 📊 THỐNG KÊ TRẬN ĐẤU")
        
        stats_data = {
            "Thời gian sống": f"{game.game_time:.1f} giây",
            "Tổng quãng đường": f"{game.stats['total_distance']:.1f} mét",
            "Tốc độ tối đa": f"{game.stats['max_speed'] * 20:.1f} km/h",
            "Số vụ va chạm": game.stats['total_crashes'],
            "Xe AI đã phá hủy": game.stats['cars_destroyed'],
            "Nhiên liệu còn lại": f"{game.player.fuel if game.player else 0:.1f}%",
            "Hư hại cuối cùng": f"{game.player.damage if game.player else 100:.1f}%"
        }
        
        for key, value in stats_data.items():
            st.metric(key, value)
        
        st.markdown("---")
        
        if st.button("🔄 CHƠI LẠI", type="primary", use_container_width=True, size="large"):
            st.session_state.game = Game()
            st.session_state.game.game_state = "PLAYING"
            st.rerun()
        
        if st.button("🏠 VỀ MENU CHÍNH", use_container_width=True):
            st.session_state.game = Game()
            st.rerun()
        
        # Hiển thị thành tích
        st.markdown("### 🏆 THÀNH TÍCH")
        
        achievements = []
        if game.score > 10000:
            achievements.append("🔴 HẠNG S: Trên 10,000 điểm")
        elif game.score > 5000:
            achievements.append("🟠 HẠNG A: Trên 5,000 điểm")
        elif game.score > 2000:
            achievements.append("🟡 HẠNG B: Trên 2,000 điểm")
        
        if game.stats['total_crashes'] == 0 and game.game_time > 30:
            achievements.append("🚗 LÁI XE AN TOÀN: Không va chạm trong 30s")
        
        if game.stats['max_speed'] * 20 > 200:
            achievements.append("⚡ TỐC ĐỘ CAO: Trên 200 km/h")
        
        for achievement in achievements:
            st.success(achievement)

# ==================== KHỞI CHẠY ỨNG DỤNG ====================

if __name__ == "__main__":
    main()
