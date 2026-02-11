import streamlit as st
import numpy as np
import math
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum
import json
from PIL import Image, ImageDraw
import io

# ==================== CẤU HÌNH HỆ THỐNG ====================
st.set_page_config(
    page_title="BeamNG-Style Car Crash Simulator",
    page_icon="🚗",
    layout="wide"
)

# ==================== CÁC LỚP VẬT LÝ NÂNG CAO ====================

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
    
    def __truediv__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return self / mag
        return Vector2(0, 0)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y
    
    def cross(self, other):
        return self.x * other.y - self.y * other.x
    
    def rotate(self, angle):
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

@dataclass
class Material:
    density: float = 1.0
    elasticity: float = 0.3
    friction: float = 0.7
    strength: float = 100.0
    deformation_threshold: float = 10.0

class DamageZone:
    def __init__(self, vertices: List[Vector2], material: Material, max_deformation: float = 5.0):
        self.original_vertices = vertices.copy()
        self.current_vertices = vertices.copy()
        self.material = material
        self.deformation = 0.0
        self.max_deformation = max_deformation
        self.broken = False
        self.crack_points = []
        
    def apply_force(self, force_point: Vector2, force: Vector2):
        if self.broken:
            return 0.0
            
        # Tính toán deformation dựa trên khoảng cách và lực
        total_deformation = 0.0
        for i, vertex in enumerate(self.current_vertices):
            dist = (vertex - force_point).magnitude()
            if dist < 50:  # Ảnh hưởng trong bán kính 50px
                deformation_factor = 1.0 - (dist / 50)
                deformation = force.magnitude() * deformation_factor * 0.01
                
                # Di chuyển vertex
                direction = (vertex - force_point).normalize()
                self.current_vertices[i] = vertex + direction * deformation
                total_deformation += deformation
                
                # Tạo điểm nứt ngẫu nhiên
                if deformation > self.material.deformation_threshold and random.random() < 0.1:
                    self.crack_points.append({
                        'point': vertex,
                        'size': deformation * 0.5,
                        'angle': random.uniform(0, 360)
                    })
        
        self.deformation += total_deformation
        if self.deformation > self.material.strength:
            self.broken = True
            
        return total_deformation

class CarPart:
    def __init__(self, name: str, position: Vector2, vertices: List[Vector2], 
                 material: Material, mass: float = 1.0, is_fixed: bool = False):
        self.name = name
        self.position = position
        self.original_vertices = vertices
        self.vertices = vertices.copy()
        self.material = material
        self.mass = mass
        self.is_fixed = is_fixed
        
        self.velocity = Vector2(0, 0)
        self.angular_velocity = 0.0
        self.angle = 0.0
        
        self.deformation = 0.0
        self.damage_zones = []
        self.broken = False
        
        # Tạo damage zones cho part
        self.create_damage_zones()
        
    def create_damage_zones(self):
        # Chia part thành các zone nhỏ để tính toán deformation
        num_zones = max(2, len(self.vertices) // 3)
        for i in range(num_zones):
            zone_vertices = []
            for j in range(len(self.vertices)):
                if j % num_zones == i:
                    zone_vertices.append(self.vertices[j])
            if len(zone_vertices) >= 3:
                self.damage_zones.append(DamageZone(zone_vertices, self.material))
    
    def update_physics(self, dt: float, gravity: Vector2 = Vector2(0, 0)):
        if self.broken or self.is_fixed:
            return
            
        # Áp dụng trọng lực
        self.velocity = self.velocity + gravity * dt
        
        # Áp dụng ma sát
        friction_force = self.velocity * -self.material.friction * dt
        self.velocity = self.velocity + friction_force
        
        # Cập nhật vị trí
        self.position = self.position + self.velocity * dt
        
        # Cập nhật góc quay
        self.angle += self.angular_velocity * dt
        self.angular_velocity *= 0.99  # Damping
        
    def apply_force(self, force: Vector2, application_point: Vector2):
        if self.broken:
            return
            
        # Tính toán lực tịnh tiến
        acceleration = force / self.mass
        self.velocity = self.velocity + acceleration
        
        # Tính toán mô-men xoắn
        r = application_point - self.position
        torque = r.cross(force)
        moment_of_inertia = self.mass * 100  # Ước lượng đơn giản
        angular_acceleration = torque / moment_of_inertia
        self.angular_velocity += angular_acceleration
        
        # Áp dụng deformation cho các damage zones
        for zone in self.damage_zones:
            zone.apply_force(application_point, force)
            
        # Kiểm tra hỏng hoàn toàn
        total_deformation = sum(z.deformation for z in self.damage_zones)
        if total_deformation > self.material.strength * 3:
            self.broken = True

class AdvancedCar:
    def __init__(self, position: Vector2, car_type: str = "sedan"):
        self.position = position
        self.car_type = car_type
        self.parts = []
        self.suspension_stiffness = 0.2
        self.wheel_base = 60
        self.track_width = 40
        
        # Màu sắc
        self.base_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        self.damage_color = (255, 50, 50)
        
        # Tạo các bộ phận xe
        self.create_car_parts()
        
        # Thuộc tính vật lý
        self.speed = 0.0
        self.steering_angle = 0.0
        self.max_steering = 30.0
        self.engine_power = 0.0
        self.braking = False
        
        # Thống kê damage
        self.part_damage = {}
        
    def create_car_parts(self):
        # Tạo chassis (khung xe)
        chassis_vertices = [
            Vector2(-40, -20), Vector2(40, -20),
            Vector2(50, 0), Vector2(50, 30),
            Vector2(-50, 30), Vector2(-50, 0)
        ]
        chassis_material = Material(density=1.5, elasticity=0.2, strength=200)
        chassis = CarPart("chassis", self.position, chassis_vertices, chassis_material, mass=80)
        self.parts.append(chassis)
        
        # Tạo các cửa
        door_vertices = [
            Vector2(-40, -15), Vector2(0, -15),
            Vector2(0, 25), Vector2(-40, 25)
        ]
        door_material = Material(density=1.0, elasticity=0.4, strength=80)
        door = CarPart("door_left", self.position + Vector2(-20, 5), door_vertices, door_material, mass=15)
        self.parts.append(door)
        
        # Tạo mui xe
        hood_vertices = [
            Vector2(0, -20), Vector2(40, -20),
            Vector2(40, 0), Vector2(0, 0)
        ]
        hood_material = Material(density=1.0, elasticity=0.3, strength=70)
        hood = CarPart("hood", self.position + Vector2(20, -10), hood_vertices, hood_material, mass=10)
        self.parts.append(hood)
        
        # Tạo cốp xe
        trunk_vertices = [
            Vector2(-40, -20), Vector2(0, -20),
            Vector2(0, 0), Vector2(-40, 0)
        ]
        trunk_material = Material(density=1.0, elasticity=0.3, strength=70)
        trunk = CarPart("trunk", self.position + Vector2(-20, -10), trunk_vertices, trunk_material, mass=10)
        self.parts.append(trunk)
        
        # Tạo bánh xe
        wheel_material = Material(density=2.0, elasticity=0.8, strength=150, friction=0.9)
        
        # Bánh trước trái
        wheel_fl = CarPart("wheel_fl", self.position + Vector2(-30, -25), 
                          self.create_wheel_vertices(15), wheel_material, mass=8)
        self.parts.append(wheel_fl)
        
        # Bánh trước phải
        wheel_fr = CarPart("wheel_fr", self.position + Vector2(30, -25), 
                          self.create_wheel_vertices(15), wheel_material, mass=8)
        self.parts.append(wheel_fr)
        
        # Bánh sau trái
        wheel_rl = CarPart("wheel_rl", self.position + Vector2(-30, 25), 
                          self.create_wheel_vertices(15), wheel_material, mass=8)
        self.parts.append(wheel_rl)
        
        # Bánh sau phải
        wheel_rr = CarPart("wheel_rr", self.position + Vector2(30, 25), 
                          self.create_wheel_vertices(15), wheel_material, mass=8)
        self.parts.append(wheel_rr)
        
    def create_wheel_vertices(self, radius: float, segments: int = 16):
        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append(Vector2(math.cos(angle) * radius, math.sin(angle) * radius))
        return vertices
    
    def update(self, dt: float):
        # Cập nhật vật lý cho tất cả parts
        for part in self.parts:
            part.update_physics(dt)
            
            # Cập nhật thống kê damage
            if part.name not in self.part_damage:
                self.part_damage[part.name] = 0
            damage_percent = sum(z.deformation for z in part.damage_zones) / (part.material.strength * len(part.damage_zones)) * 100
            self.part_damage[part.name] = min(100, damage_percent)
    
    def apply_control(self, throttle: float, brake: float, steering: float):
        self.engine_power = throttle * 500
        self.braking = brake > 0
        self.steering_angle = steering * self.max_steering
        
        # Áp dụng lực động cơ
        if self.engine_power > 0:
            force_direction = Vector2(math.cos(math.radians(self.parts[0].angle)), 
                                     math.sin(math.radians(self.parts[0].angle)))
            force = force_direction * self.engine_power
            self.parts[0].apply_force(force, self.parts[0].position)
        
        # Áp dụng phanh
        if self.braking:
            brake_force = self.parts[0].velocity * -10 * brake
            self.parts[0].apply_force(brake_force, self.parts[0].position)
    
    def check_collision(self, other: 'AdvancedCar'):
        collisions = []
        
        for part1 in self.parts:
            for part2 in other.parts:
                collision = self.check_part_collision(part1, part2)
                if collision['collision']:
                    collisions.append(collision)
                    
        return collisions
    
    def check_part_collision(self, part1: CarPart, part2: CarPart):
        # Kiểm tra collision đơn giản giữa hai convex polygons
        vertices1 = [v + part1.position for v in part1.vertices]
        vertices2 = [v + part2.position for v in part2.vertices]
        
        # Sử dụng Separating Axis Theorem đơn giản
        collision = self.sat_collision(vertices1, vertices2)
        
        if collision['collision']:
            # Tính toán lực va chạm
            relative_velocity = part2.velocity - part1.velocity
            normal = collision['normal']
            velocity_along_normal = relative_velocity.dot(normal)
            
            if velocity_along_normal > 0:
                return {'collision': False}
            
            # Tính toán impulse
            e = min(part1.material.elasticity, part2.material.elasticity)
            j = -(1 + e) * velocity_along_normal
            j /= (1/part1.mass + 1/part2.mass)
            
            impulse = normal * j
            
            # Áp dụng lực cho cả hai parts
            application_point = collision['point']
            part1.apply_force(-impulse, application_point)
            part2.apply_force(impulse, application_point)
            
            # Tạo deformation
            deformation_force = impulse.magnitude() * 0.5
            for zone in part1.damage_zones:
                zone.apply_force(application_point, -impulse * 0.1)
            for zone in part2.damage_zones:
                zone.apply_force(application_point, impulse * 0.1)
            
            return {
                'collision': True,
                'part1': part1.name,
                'part2': part2.name,
                'force': impulse.magnitude(),
                'point': application_point
            }
        
        return {'collision': False}
    
    def sat_collision(self, poly1: List[Vector2], poly2: List[Vector2]):
        # Triển khai SAT đơn giản
        best_depth = float('inf')
        best_normal = Vector2(0, 0)
        best_point = Vector2(0, 0)
        
        polygons = [poly1, poly2]
        
        for i in range(2):
            poly = polygons[i]
            other_poly = polygons[1 - i]
            
            for j in range(len(poly)):
                k = (j + 1) % len(poly)
                edge = poly[k] - poly[j]
                normal = Vector2(-edge.y, edge.x).normalize()
                
                # Tìm min và max projection cho poly1
                min1, max1 = float('inf'), float('-inf')
                for vertex in poly:
                    projection = vertex.dot(normal)
                    min1 = min(min1, projection)
                    max1 = max(max1, projection)
                
                # Tìm min và max projection cho poly2
                min2, max2 = float('inf'), float('-inf')
                for vertex in other_poly:
                    projection = vertex.dot(normal)
                    min2 = min(min2, projection)
                    max2 = max(max2, projection)
                
                # Kiểm tra overlap
                if max1 < min2 or max2 < min1:
                    return {'collision': False}
                
                # Tính depth của overlap
                overlap = min(max1, max2) - max(min1, min2)
                if overlap < best_depth:
                    best_depth = overlap
                    best_normal = normal if i == 0 else normal * -1
                    best_point = (poly[j] + poly[k]) / 2
        
        return {
            'collision': True,
            'depth': best_depth,
            'normal': best_normal,
            'point': best_point
        }
    
    def get_total_damage(self):
        total = 0
        for damage in self.part_damage.values():
            total += damage
        return total / len(self.part_damage) if self.part_damage else 0

class BeamNGPhysicsEngine:
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.cars = []
        self.obstacles = []
        self.gravity = Vector2(0, 9.81 * 10)  # Mạnh hơn cho hiệu ứng rõ ràng
        self.collisions = []
        self.particles = []
        
        # Tạo vật cản
        self.create_obstacles()
    
    def create_obstacles(self):
        # Tạo tường xung quanh
        wall_thickness = 50
        wall_material = Material(density=10.0, elasticity=0.1, strength=1000, friction=0.8)
        
        # Tường trên
        wall_top = CarPart("wall_top", Vector2(self.width//2, -wall_thickness//2),
                          [Vector2(-self.width//2, -wall_thickness//2), 
                           Vector2(self.width//2, -wall_thickness//2),
                           Vector2(self.width//2, wall_thickness//2),
                           Vector2(-self.width//2, wall_thickness//2)],
                          wall_material, mass=1000, is_fixed=True)
        self.obstacles.append(wall_top)
        
        # Tường dưới
        wall_bottom = CarPart("wall_bottom", Vector2(self.width//2, self.height + wall_thickness//2),
                             [Vector2(-self.width//2, -wall_thickness//2), 
                              Vector2(self.width//2, -wall_thickness//2),
                              Vector2(self.width//2, wall_thickness//2),
                              Vector2(-self.width//2, wall_thickness//2)],
                             wall_material, mass=1000, is_fixed=True)
        self.obstacles.append(wall_bottom)
        
        # Tường trái
        wall_left = CarPart("wall_left", Vector2(-wall_thickness//2, self.height//2),
                           [Vector2(-wall_thickness//2, -self.height//2), 
                            Vector2(wall_thickness//2, -self.height//2),
                            Vector2(wall_thickness//2, self.height//2),
                            Vector2(-wall_thickness//2, self.height//2)],
                           wall_material, mass=1000, is_fixed=True)
        self.obstacles.append(wall_left)
        
        # Tường phải
        wall_right = CarPart("wall_right", Vector2(self.width + wall_thickness//2, self.height//2),
                            [Vector2(-wall_thickness//2, -self.height//2), 
                             Vector2(wall_thickness//2, -self.height//2),
                             Vector2(wall_thickness//2, self.height//2),
                             Vector2(-wall_thickness//2, self.height//2)],
                            wall_material, mass=1000, is_fixed=True)
        self.obstacles.append(wall_right)
        
        # Tạo vật cản ngẫu nhiên
        for i in range(10):
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            
            obstacle_type = random.choice(["box", "cylinder", "triangle"])
            
            if obstacle_type == "box":
                size = random.randint(20, 60)
                vertices = [
                    Vector2(-size, -size), Vector2(size, -size),
                    Vector2(size, size), Vector2(-size, size)
                ]
            elif obstacle_type == "cylinder":
                radius = random.randint(15, 30)
                vertices = []
                segments = 12
                for j in range(segments):
                    angle = 2 * math.pi * j / segments
                    vertices.append(Vector2(math.cos(angle) * radius, math.sin(angle) * radius))
            else:  # triangle
                size = random.randint(20, 50)
                vertices = [
                    Vector2(0, -size), Vector2(size, size), Vector2(-size, size)
                ]
            
            obstacle_material = Material(density=random.uniform(0.5, 2.0), 
                                        elasticity=random.uniform(0.1, 0.5),
                                        strength=random.uniform(50, 200))
            
            obstacle = CarPart(f"obstacle_{i}", Vector2(x, y), vertices, 
                              obstacle_material, mass=random.uniform(10, 100))
            self.obstacles.append(obstacle)
    
    def add_car(self, position: Vector2, car_type: str = "sedan"):
        car = AdvancedCar(position, car_type)
        self.cars.append(car)
        return car
    
    def update(self, dt: float):
        self.collisions = []
        
        # Cập nhật tất cả xe
        for car in self.cars:
            car.update(dt)
            
            # Kiểm tra va chạm với các vật cản
            for obstacle in self.obstacles:
                for part in car.parts:
                    collision = car.check_part_collision(part, obstacle)
                    if collision['collision']:
                        self.collisions.append(collision)
            
            # Kiểm tra va chạm giữa các xe
            for i in range(len(self.cars)):
                for j in range(i + 1, len(self.cars)):
                    collisions = self.cars[i].check_collision(self.cars[j])
                    self.collisions.extend(collisions)
        
        # Cập nhật vật cản
        for obstacle in self.obstacles:
            if not obstacle.is_fixed:
                obstacle.update_physics(dt, self.gravity)
    
    def create_crash_test_scenario(self):
        """Tạo scenario test va chạm như BeamNG"""
        # Xe mục tiêu đứng yên
        target_car = self.add_car(Vector2(self.width//2, self.height//2), "sedan")
        
        # Xe tấn công với tốc độ cao
        crash_car = self.add_car(Vector2(self.width//4, self.height//2), "sedan")
        crash_car.parts[0].velocity = Vector2(200, 0)  # Tốc độ cao
        crash_car.speed = 200
        
        return target_car, crash_car

# ==================== HỆ THỐNG VẼ PIXEL ART ====================

class PixelRenderer:
    def __init__(self, width: int = 800, height: int = 600, pixel_size: int = 2):
        self.width = width
        self.height = height
        self.pixel_size = pixel_size
        self.image = Image.new('RGB', (width, height), (40, 44, 52))
        self.draw = ImageDraw.Draw(self.image)
        
    def draw_car(self, car: AdvancedCar, show_damage: bool = True):
        # Vẽ từng bộ phận của xe
        for part in car.parts:
            if part.broken:
                continue
                
            # Tính toán màu dựa trên damage
            damage_level = car.part_damage.get(part.name, 0) / 100
            base_r, base_g, base_b = car.base_color
            
            if damage_level > 0.5:
                # Chuyển sang màu damage
                r = min(255, base_r + 100 * damage_level)
                g = max(0, base_g - 100 * damage_level)
                b = max(0, base_b - 100 * damage_level)
                color = (int(r), int(g), int(b))
            else:
                color = car.base_color
            
            # Vẽ các damage zones
            if show_damage:
                for zone in part.damage_zones:
                    zone_color = color
                    if zone.deformation > zone.material.strength * 0.7:
                        zone_color = (255, 50, 50)  # Đỏ khi sắp vỡ
                    elif zone.deformation > zone.material.strength * 0.3:
                        zone_color = (255, 150, 50)  # Cam khi hư hại
                    
                    # Vẽ các cạnh của zone
                    points = []
                    for vertex in zone.current_vertices:
                        world_pos = vertex + part.position
                        points.append((world_pos.x, world_pos.y))
                    
                    if len(points) >= 3:
                        # Vẽ polygon với viền đậm
                        self.draw.polygon(points, fill=zone_color, outline=(0, 0, 0))
                        
                        # Vẽ các vết nứt
                        for crack in zone.crack_points:
                            cx, cy = crack['point'].x + part.position.x, crack['point'].y + part.position.y
                            size = crack['size']
                            angle = crack['angle']
                            
                            # Vẽ đường nứt
                            dx = math.cos(math.radians(angle)) * size
                            dy = math.sin(math.radians(angle)) * size
                            self.draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], 
                                         fill=(0, 0, 0), width=2)
            else:
                # Vẽ part đơn giản
                points = []
                for vertex in part.vertices:
                    world_pos = vertex + part.position
                    points.append((world_pos.x, world_pos.y))
                
                if len(points) >= 3:
                    self.draw.polygon(points, fill=color, outline=(0, 0, 0))
    
    def draw_obstacles(self, obstacles: List[CarPart]):
        for obstacle in obstacles:
            if obstacle.broken:
                continue
                
            color = (150, 150, 150) if obstacle.name.startswith('wall') else (200, 200, 100)
            
            points = []
            for vertex in obstacle.vertices:
                world_pos = vertex + obstacle.position
                points.append((world_pos.x, world_pos.y))
            
            if len(points) >= 3:
                self.draw.polygon(points, fill=color, outline=(0, 0, 0))
    
    def draw_collision_points(self, collisions: List[Dict]):
        for collision in collisions:
            if collision.get('collision', False):
                point = collision.get('point', Vector2(0, 0))
                force = collision.get('force', 0)
                
                # Kích thước hiệu ứng dựa trên lực
                size = min(20, force * 0.1)
                
                # Màu sắc dựa trên lực
                if force > 100:
                    color = (255, 0, 0)  # Đỏ cho va chạm mạnh
                elif force > 50:
                    color = (255, 150, 0)  # Cam
                else:
                    color = (255, 255, 0)  # Vàng
                
                # Vẽ vòng tròn va chạm
                self.draw.ellipse([(point.x - size, point.y - size),
                                 (point.x + size, point.y + size)],
                                fill=color, outline=(255, 255, 255))
    
    def draw_grid(self, grid_size: int = 50):
        """Vẽ grid để dễ hình dung tỉ lệ"""
        for x in range(0, self.width, grid_size):
            self.draw.line([(x, 0), (x, self.height)], fill=(60, 60, 60), width=1)
        for y in range(0, self.height, grid_size):
            self.draw.line([(0, y), (self.width, y)], fill=(60, 60, 60), width=1)
    
    def get_image(self):
        return self.image
    
    def clear(self):
        self.image = Image.new('RGB', (self.width, self.height), (40, 44, 52))
        self.draw = ImageDraw.Draw(self.image)

# ==================== GIAO DIỆN STREAMLIT ====================

def main():
    st.title("🚗 BeamNG-Style Car Crash Physics Simulator")
    st.markdown("### Mô phỏng vật lý va chạm thực tế với hệ thống phá hủy chi tiết")
    
    # Khởi tạo session state
    if 'physics_engine' not in st.session_state:
        st.session_state.physics_engine = BeamNGPhysicsEngine(800, 600)
        st.session_state.renderer = PixelRenderer(800, 600, pixel_size=2)
        st.session_state.simulation_running = False
        st.session_state.simulation_speed = 1.0
        st.session_state.last_update = time.time()
        st.session_state.cars = []
        st.session_state.total_crashes = 0
        st.session_state.max_force = 0
    
    # Sidebar điều khiển
    with st.sidebar:
        st.header("⚙️ Điều Khiển Va Chạm")
        
        # Scenario selector
        scenario = st.selectbox(
            "Chọn kịch bản va chạm",
            ["Tự do", "Frontal Crash", "T-Bone", "Rollover", "Multi-Car Pileup", "Crash Test Dummy"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Thêm Xe", use_container_width=True):
                x = random.randint(100, 700)
                y = random.randint(100, 500)
                new_car = st.session_state.physics_engine.add_car(Vector2(x, y))
                st.session_state.cars.append(new_car)
                st.rerun()
        
        with col2:
            if st.button("🗑️ Xóa Tất Cả", use_container_width=True):
                st.session_state.physics_engine.cars.clear()
                st.session_state.cars.clear()
                st.rerun()
        
        # Crash test button
        if st.button("💥 Crash Test!", type="primary", use_container_width=True):
            st.session_state.physics_engine.create_crash_test_scenario()
            st.session_state.simulation_running = True
            st.rerun()
        
        st.markdown("---")
        
        # Simulation controls
        st.subheader("🎮 Điều Khiển Mô Phỏng")
        
        if st.button("▶️ Bắt đầu" if not st.session_state.simulation_running else "⏸️ Dừng", 
                    use_container_width=True):
            st.session_state.simulation_running = not st.session_state.simulation_running
        
        st.session_state.simulation_speed = st.slider("Tốc độ mô phỏng", 0.1, 5.0, 1.0, 0.1)
        
        if st.button("🔁 Reset", use_container_width=True):
            st.session_state.physics_engine = BeamNGPhysicsEngine(800, 600)
            st.session_state.renderer = PixelRenderer(800, 600, pixel_size=2)
            st.session_state.simulation_running = False
            st.session_state.total_crashes = 0
            st.session_state.max_force = 0
            st.session_state.cars = []
            st.rerun()
        
        st.markdown("---")
        
        # Physics settings
        st.subheader("⚛️ Cài Đặt Vật Lý")
        
        gravity = st.slider("Trọng lực", 0.0, 20.0, 9.81, 0.1)
        st.session_state.physics_engine.gravity = Vector2(0, gravity * 10)
        
        show_grid = st.checkbox("Hiển thị lưới", value=True)
        show_damage = st.checkbox("Hiển thị hư hại chi tiết", value=True)
        show_collision_points = st.checkbox("Hiển thị điểm va chạm", value=True)
        
        st.markdown("---")
        
        # Stats
        st.subheader("📊 Thống Kê Va Chạm")
        st.metric("Số lần va chạm", st.session_state.total_crashes)
        st.metric("Lực mạnh nhất", f"{st.session_state.max_force:.1f}N")
        
        if st.session_state.cars:
            avg_damage = sum(car.get_total_damage() for car in st.session_state.cars) / len(st.session_state.cars)
            st.metric("Hư hại trung bình", f"{avg_damage:.1f}%")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Game canvas
        canvas_container = st.empty()
        
        # Car controls if we have cars
        if st.session_state.cars and len(st.session_state.cars) > 0:
            st.subheader("🎮 Điều Khiển Xe")
            
            selected_car_idx = st.selectbox("Chọn xe để điều khiển", 
                                          range(len(st.session_state.cars)),
                                          format_func=lambda i: f"Xe {i+1}")
            
            if selected_car_idx < len(st.session_state.cars):
                car = st.session_state.cars[selected_car_idx]
                
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    throttle = st.slider("Ga", 0.0, 1.0, 0.0, 0.1, key="throttle")
                
                with col_b:
                    brake = st.slider("Phanh", 0.0, 1.0, 0.0, 0.1, key="brake")
                
                with col_c:
                    steering = st.slider("Lái", -1.0, 1.0, 0.0, 0.1, key="steering")
                
                with col_d:
                    if st.button("🚀 Đạp Ga!", use_container_width=True):
                        car.parts[0].velocity = Vector2(300, 0)
                
                # Apply controls
                car.apply_control(throttle, brake, steering)
    
    with col2:
        # Damage display
        st.subheader("⚠️ Hư Hại Chi Tiết")
        
        if st.session_state.cars:
            for i, car in enumerate(st.session_state.cars):
                with st.expander(f"Xe {i+1} - {car.get_total_damage():.1f}%", expanded=i==0):
                    for part_name, damage in car.part_damage.items():
                        st.progress(damage/100, f"{part_name}: {damage:.1f}%")
        
        # Real-time collision info
        st.subheader("💥 Va Chạm Thời Gian Thực")
        if st.session_state.physics_engine.collisions:
            latest_collision = st.session_state.physics_engine.collisions[-1]
            if latest_collision.get('collision', False):
                st.metric("Lực va chạm", f"{latest_collision.get('force', 0):.1f}N")
                st.metric("Bộ phận 1", latest_collision.get('part1', 'N/A'))
                st.metric("Bộ phận 2", latest_collision.get('part2', 'N/A'))
    
    # Simulation loop
    if st.session_state.simulation_running:
        current_time = time.time()
        dt = (current_time - st.session_state.last_update) * st.session_state.simulation_speed
        
        if dt > 0.016:  # Cap at ~60 FPS
            # Update physics
            st.session_state.physics_engine.update(dt)
            
            # Update stats
            for collision in st.session_state.physics_engine.collisions:
                if collision.get('collision', False):
                    st.session_state.total_crashes += 1
                    force = collision.get('force', 0)
                    if force > st.session_state.max_force:
                        st.session_state.max_force = force
            
            # Render frame
            st.session_state.renderer.clear()
            
            if show_grid:
                st.session_state.renderer.draw_grid()
            
            st.session_state.renderer.draw_obstacles(st.session_state.physics_engine.obstacles)
            
            for car in st.session_state.physics_engine.cars:
                st.session_state.renderer.draw_car(car, show_damage)
            
            if show_collision_points:
                st.session_state.renderer.draw_collision_points(st.session_state.physics_engine.collisions)
            
            # Display image
            img = st.session_state.renderer.get_image()
            canvas_container.image(img, caption="Mô phỏng vật lý va chạm thời gian thực", 
                                 use_column_width=True)
            
            st.session_state.last_update = current_time
            st.rerun()
    else:
        # Render static frame
        st.session_state.renderer.clear()
        
        if show_grid:
            st.session_state.renderer.draw_grid()
        
        st.session_state.renderer.draw_obstacles(st.session_state.physics_engine.obstacles)
        
        for car in st.session_state.physics_engine.cars:
            st.session_state.renderer.draw_car(car, show_damage)
        
        img = st.session_state.renderer.get_image()
        canvas_container.image(img, caption="Mô phỏng vật lý va chạm", use_column_width=True)
    
    # Footer with instructions
    st.markdown("---")
    with st.expander("📖 Hướng Dẫn Sử Dụng & Vật Lý"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎮 Cách Chơi:
            1. **Thêm xe** bằng nút trong sidebar
            2. **Chọn kịch bản** va chạm hoặc tạo tự do
            3. **Bắt đầu mô phỏng** để xem vật lý hoạt động
            4. **Điều khiển xe** đã chọn bằng thanh trượt
            5. **Quan sát hư hại** chi tiết từng bộ phận
            
            ### ⚡ Tính Năng Vật Lý:
            - **Deformation thực tế**: Xe biến dạng theo lực va chạm
            - **Hệ thống phá hủy**: Bộ phận vỡ khi chịu lực quá lớn
            - **Mô-men xoắn**: Xe xoay khi va chạm lệch tâm
            - **Ma sát & đàn hồi**: Vật liệu có thuộc tính riêng
            """)
        
        with col2:
            st.markdown("""
            ### 🔬 Các Loại Va Chạm:
            
            **Frontal Crash**:
            - Va chạm trực diện
            - Hư hại tập trung ở đầu xe
            - Mui xe biến dạng nhiều
            
            **T-Bone**:
            - Va chạm bên hông
            - Cửa xe hư hại nặng
            - Xe bị đẩy xoay
            
            **Rollover**:
            - Xe lật nhiều vòng
            - Hư hại toàn bộ thân xe
            - Các bộ phận có thể rơi ra
            
            **Multi-Car**:
            - Chuỗi va chạm dây chuyền
            - Hư hại tích lũy
            - Hiệu ứng domino
            """)
    
    # Physics formulas display
    st.markdown("""
    ### ⚛️ Công Thức Vật Lý Sử Dụng:
    
    ```python
    # 1. Động lượng va chạm:
    impulse = -(1 + elasticity) * relative_velocity.dot(normal)
    impulse /= (1/mass1 + 1/mass2)
    
    # 2. Lực tác động:
    force = mass * acceleration
    torque = r.cross(force)  # r: vector từ tâm đến điểm tác động
    
    # 3. Deformation:
    deformation = force * deformation_factor / material_strength
    
    # 4. Tốc độ góc:
    angular_velocity += torque / moment_of_inertia
    ```
    """)

if __name__ == "__main__":
    main()
