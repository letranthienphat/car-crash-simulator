import streamlit as st

st.set_page_config(
    page_title="Car Crash Simulator 3D",
    page_icon="💥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ẩn hoàn toàn các thành phần Streamlit
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {max-width: 100%; padding: 0; margin: 0; background: black;}
    .main > div {padding: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# HTML chứa game 3D – dùng Three.js
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>3D Car Crash Simulator</title>
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Courier New', monospace; background: black; }
        #info {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #00aaff;
            pointer-events: none;
            z-index: 100;
            min-width: 200px;
            border: 2px solid #00aaff;
            box-shadow: 0 0 20px rgba(0,170,255,0.3);
        }
        #health-bar {
            width: 100%;
            height: 20px;
            background: #333;
            border-radius: 10px;
            margin: 10px 0;
            overflow: hidden;
        }
        #health-fill {
            height: 100%;
            width: 100%;
            background: linear-gradient(90deg, #00ff00, #ff0000);
            transition: width 0.2s;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 14px;
        }
        #upgrade-menu {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #ffaa00;
            width: 260px;
            z-index: 200;
        }
        .upgrade-btn {
            background: #ffaa00;
            color: black;
            border: none;
            padding: 10px;
            margin: 5px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: 0.2s;
        }
        .upgrade-btn:hover { background: #ffcc00; transform: scale(1.02); }
        .upgrade-btn:disabled { background: #555; cursor: not-allowed; }
        #controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 15px;
            border-radius: 10px;
            font-size: 14px;
            border: 1px solid #888;
        }
        a { color: #00aaff; }
        .pixel-crash { color: #ff5555; }
    </style>
</head>
<body>
    <div id="info">
        <div style="font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #00aaff;">
            💥 3D PIXEL CRASH
        </div>
        <div class="stat">
            <span>🏆 ĐIỂM:</span>
            <span id="score">0</span>
        </div>
        <div class="stat">
            <span>💥 VA CHẠM:</span>
            <span id="crashes">0</span>
        </div>
        <div id="health-bar">
            <div id="health-fill" style="width: 100%;"></div>
        </div>
        <div class="stat">
            <span>🛡️ MÁU:</span>
            <span id="health">100%</span>
        </div>
        <div class="stat">
            <span>⚡ TỐC ĐỘ:</span>
            <span id="speed">0 km/h</span>
        </div>
        <div class="stat">
            <span>🚗 XE AI:</span>
            <span id="ai-count">5</span>
        </div>
    </div>

    <div id="upgrade-menu">
        <div style="font-size: 18px; color: #ffaa00; margin-bottom: 10px;">⬆️ NÂNG CẤP</div>
        <div style="display: flex; justify-content: space-between;">
            <span>💰 ĐIỂM: <span id="upgrade-score">0</span></span>
        </div>
        <button class="upgrade-btn" id="upgrade-speed" onclick="upgrade('speed')">TỐC ĐỘ (+10%) - 50 điểm</button>
        <button class="upgrade-btn" id="upgrade-armor" onclick="upgrade('armor')">GIÁP (+20%) - 30 điểm</button>
        <button class="upgrade-btn" id="upgrade-accel" onclick="upgrade('accel')">TĂNG TỐC (+15%) - 40 điểm</button>
    </div>

    <div id="controls">
        <strong>ĐIỀU KHIỂN</strong><br>
        W/↑ : Tăng tốc<br>
        S/↓ : Phanh<br>
        A/← : Trái<br>
        D/→ : Phải<br>
        Space: Phanh tay
    </div>

    <!-- Nhúng Three.js từ CDN -->
    <script type="importmap">
        {
            "imports": {
                "three": "https://unpkg.com/three@0.128.0/build/three.module.js",
                "three/addons/": "https://unpkg.com/three@0.128.0/examples/jsm/"
            }
        }
    </script>

    <script type="module">
        import * as THREE from 'three';
        import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

        // ---------- KHỞI TẠO CẢNH 3D ----------
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0a1a); // màu xanh đen pixel

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(15, 10, 25);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: false }); // antialias false giữ phong cách pixel
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.setPixelRatio(window.devicePixelRatio);
        document.body.appendChild(renderer.domElement);

        // ---------- ÁNH SÁNG ----------
        const ambientLight = new THREE.AmbientLight(0x404060);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffeedd, 1);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        dirLight.receiveShadow = true;
        dirLight.shadow.mapSize.width = 1024;
        dirLight.shadow.mapSize.height = 1024;
        const d = 30;
        dirLight.shadow.camera.left = -d;
        dirLight.shadow.camera.right = d;
        dirLight.shadow.camera.top = d;
        dirLight.shadow.camera.bottom = -d;
        dirLight.shadow.camera.near = 1;
        dirLight.shadow.camera.far = 50;
        scene.add(dirLight);

        const fillLight = new THREE.PointLight(0x4466aa, 0.5);
        fillLight.position.set(-5, 5, 10);
        scene.add(fillLight);

        // ---------- MẶT ĐẤT + ĐƯỜNG (phong cách pixel) ----------
        const groundGeo = new THREE.PlaneGeometry(100, 100);
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x222233, roughness: 0.8, metalness: 0.2 });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.5;
        ground.receiveShadow = true;
        scene.add(ground);

        // Vạch kẻ đường (pixel style)
        function createRoadMarking(x, z, length, width, isVertical = false) {
            const box = new THREE.BoxGeometry(width, 0.1, length);
            const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x444444 });
            const marking = new THREE.Mesh(box, mat);
            marking.position.set(x, -0.45, z);
            marking.receiveShadow = true;
            scene.add(marking);
        }
        // Đường kẻ dọc
        for (let i = -40; i <= 40; i += 10) {
            createRoadMarking(i, 0, 100, 0.5, true);
        }
        // Đường kẻ ngang
        for (let i = -40; i <= 40; i += 10) {
            createRoadMarking(0, i, 100, 0.5, false);
        }

        // ---------- VẬT CẢN (hộp màu) ----------
        const obstacles = [];
        function createObstacle(x, z, color = 0xff5500) {
            const box = new THREE.BoxGeometry(1.5, 1, 1.5);
            const mat = new THREE.MeshStandardMaterial({ color, emissive: 0x331100 });
            const obs = new THREE.Mesh(box, mat);
            obs.position.set(x, 0, z);
            obs.castShadow = true;
            obs.receiveShadow = true;
            scene.add(obs);
            return obs;
        }
        obstacles.push(createObstacle(5, 8, 0xff0000));
        obstacles.push(createObstacle(-3, -5, 0x00ff00));
        obstacles.push(createObstacle(10, -2, 0x0000ff));
        obstacles.push(createObstacle(-8, 7, 0xffff00));

        // ---------- TÒA NHÀ PIXEL ----------
        function createBuilding(x, z, w, h, d, color) {
            const box = new THREE.BoxGeometry(w, h, d);
            const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.7, emissive: 0x111122 });
            const building = new THREE.Mesh(box, mat);
            building.position.set(x, h/2 - 0.5, z);
            building.castShadow = true;
            building.receiveShadow = true;
            scene.add(building);
            // Cửa sổ pixel
            const windowMat = new THREE.MeshStandardMaterial({ color: 0xffaa00, emissive: 0x442200 });
            for (let i = 0; i < 3; i++) {
                const windowBox = new THREE.BoxGeometry(0.3, 0.3, 0.1);
                const win = new THREE.Mesh(windowBox, windowMat);
                win.position.set(x + (i-1)*0.8, h/2, z + d/2 + 0.1);
                scene.add(win);
            }
        }
        createBuilding(-15, -15, 4, 3, 4, 0x8B4513);
        createBuilding(15, -12, 5, 4, 5, 0xA0522D);
        createBuilding(-12, 18, 6, 5, 6, 0xD2691E);
        createBuilding(18, 15, 4, 6, 4, 0xCD853F);

        // ---------- HỆ THỐNG XE ----------
        // Xe người chơi (màu xanh dương + viền vàng)
        const playerCar = new THREE.Group();
        // Thân
        const bodyGeo = new THREE.BoxGeometry(2, 0.6, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x0066cc, emissive: 0x001133 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.castShadow = true;
        body.receiveShadow = true;
        body.position.y = 0.5;
        playerCar.add(body);
        // Kính
        const glassGeo = new THREE.BoxGeometry(1.2, 0.3, 1.5);
        const glassMat = new THREE.MeshStandardMaterial({ color: 0x88ccff, emissive: 0x224466, transparent: true, opacity: 0.7 });
        const glass = new THREE.Mesh(glassGeo, glassMat);
        glass.castShadow = true;
        glass.receiveShadow = true;
        glass.position.set(0, 0.9, -0.5);
        playerCar.add(glass);
        // Bánh xe
        const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.8 });
        const positions = [[-0.8, 0.2, -1.2], [0.8, 0.2, -1.2], [-0.8, 0.2, 1.2], [0.8, 0.2, 1.2]];
        positions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.rotation.z = Math.PI / 2;
            wheel.position.set(pos[0], pos[1], pos[2]);
            wheel.castShadow = true;
            wheel.receiveShadow = true;
            playerCar.add(wheel);
        });
        // Viền vàng cho xe player
        const outlineGeo = new THREE.EdgesGeometry(bodyGeo);
        const outlineMat = new THREE.LineBasicMaterial({ color: 0xffaa00 });
        const outline = new THREE.LineSegments(outlineGeo, outlineMat);
        outline.position.copy(body.position);
        playerCar.add(outline);
        
        playerCar.position.set(0, 0.2, 0);
        scene.add(playerCar);

        // Xe AI (mảng)
        const aiCars = [];
        function createAICar(x, z, colorHex) {
            const car = new THREE.Group();
            const bodyGeo = new THREE.BoxGeometry(2, 0.6, 4);
            const bodyMat = new THREE.MeshStandardMaterial({ color: colorHex, emissive: 0x221100 });
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            body.castShadow = true;
            body.receiveShadow = true;
            body.position.y = 0.5;
            car.add(body);
            const glassGeo = new THREE.BoxGeometry(1.2, 0.3, 1.5);
            const glassMat = new THREE.MeshStandardMaterial({ color: 0x88aacc, emissive: 0x224466, transparent: true, opacity: 0.7 });
            const glass = new THREE.Mesh(glassGeo, glassMat);
            glass.castShadow = true;
            glass.receiveShadow = true;
            glass.position.set(0, 0.9, -0.5);
            car.add(glass);
            const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.8 });
            const positions = [[-0.8, 0.2, -1.2], [0.8, 0.2, -1.2], [-0.8, 0.2, 1.2], [0.8, 0.2, 1.2]];
            positions.forEach(pos => {
                const wheel = new THREE.Mesh(wheelGeo, wheelMat);
                wheel.rotation.z = Math.PI / 2;
                wheel.position.set(pos[0], pos[1], pos[2]);
                wheel.castShadow = true;
                wheel.receiveShadow = true;
                car.add(wheel);
            });
            car.position.set(x, 0.2, z);
            // Hướng ngẫu nhiên
            car.rotation.y = Math.random() * Math.PI * 2;
            scene.add(car);
            return {
                mesh: car,
                vx: (Math.random() - 0.5) * 0.2,
                vz: (Math.random() - 0.5) * 0.2,
                color: colorHex,
                health: 100
            };
        }
        const aiColors = [0xff3333, 0x33ff33, 0xffdd33, 0xff9933, 0xaa33aa];
        for (let i = 0; i < 5; i++) {
            let x = (Math.random() - 0.5) * 30;
            let z = (Math.random() - 0.5) * 30;
            aiCars.push(createAICar(x, z, aiColors[i % aiColors.length]));
        }

        // ---------- HỆ THỐNG PARTICLE (pixel vỡ) ----------
        const particles = [];
        function createCrashParticles(x, y, z, color) {
            for (let i = 0; i < 20; i++) {
                const size = Math.random() * 0.3 + 0.1;
                const geometry = new THREE.BoxGeometry(size, size, size);
                const material = new THREE.MeshStandardMaterial({ 
                    color: color, 
                    emissive: 0x442200,
                    emissiveIntensity: 0.3
                });
                const particle = new THREE.Mesh(geometry, material);
                particle.position.set(x, y, z);
                particle.userData = {
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: Math.random() * 0.5,
                    vz: (Math.random() - 0.5) * 0.5,
                    life: 1.0,
                    size: size
                };
                scene.add(particle);
                particles.push(particle);
            }
        }

        // ---------- VẬT LÝ ĐƠN GIẢN ----------
        const player = {
            mesh: playerCar,
            vx: 0,
            vz: 0,
            angle: 0,
            health: 100,
            maxSpeed: 0.3,
            acceleration: 0.015,
            brake: 0.05,
            turnSpeed: 0.03
        };

        // Điều khiển
        const keys = {
            up: false, down: false, left: false, right: false, space: false
        };
        window.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'w': case 'W': case 'ArrowUp': keys.up = true; e.preventDefault(); break;
                case 's': case 'S': case 'ArrowDown': keys.down = true; e.preventDefault(); break;
                case 'a': case 'A': case 'ArrowLeft': keys.left = true; e.preventDefault(); break;
                case 'd': case 'D': case 'ArrowRight': keys.right = true; e.preventDefault(); break;
                case ' ': keys.space = true; e.preventDefault(); break;
            }
        });
        window.addEventListener('keyup', (e) => {
            switch(e.key) {
                case 'w': case 'W': case 'ArrowUp': keys.up = false; e.preventDefault(); break;
                case 's': case 'S': case 'ArrowDown': keys.down = false; e.preventDefault(); break;
                case 'a': case 'A': case 'ArrowLeft': keys.left = false; e.preventDefault(); break;
                case 'd': case 'D': case 'ArrowRight': keys.right = false; e.preventDefault(); break;
                case ' ': keys.space = false; e.preventDefault(); break;
            }
        });

        // Hỗ trợ mobile (cảm ứng) – đơn giản: giả lập phím
        // Có thể bổ sung nút ảo nhưng tạm bỏ qua

        // ---------- GAME STATE ----------
        let score = 0;
        let totalCrashes = 0;
        let gameTime = 0;
        let gameRunning = true;

        // Nâng cấp
        let upgradeLevel = {
            speed: 1,
            armor: 1,
            accel: 1
        };
        window.upgrade = function(type) {
            const cost = { speed: 50, armor: 30, accel: 40 };
            if (score >= cost[type]) {
                score -= cost[type];
                upgradeLevel[type] += 0.1;
                // Cập nhật chỉ số
                if (type === 'speed') player.maxSpeed *= 1.1;
                if (type === 'accel') player.acceleration *= 1.15;
                if (type === 'armor') player.health = Math.min(player.health + 20, 100);
                document.getElementById('upgrade-score').innerText = score;
            }
        };

        // ---------- CAMERA FOLLOW ----------
        // Sử dụng OrbitControls để người chơi có thể xoay góc nhìn
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = false;
        controls.enableZoom = true;
        controls.target.copy(player.mesh.position);

        // ---------- VÒNG LẶP GAME ----------
        function animate() {
            if (!gameRunning) return;

            const delta = 1; // đơn giản, mỗi frame 1 đơn vị

            // 1. Điều khiển xe player
            if (keys.up) {
                player.vx += Math.sin(player.mesh.rotation.y) * player.acceleration;
                player.vz += Math.cos(player.mesh.rotation.y) * player.acceleration;
            }
            if (keys.down) {
                player.vx -= Math.sin(player.mesh.rotation.y) * player.brake;
                player.vz -= Math.cos(player.mesh.rotation.y) * player.brake;
            }
            if (keys.left) {
                player.mesh.rotation.y += player.turnSpeed;
            }
            if (keys.right) {
                player.mesh.rotation.y -= player.turnSpeed;
            }
            if (keys.space) {
                player.vx *= 0.95;
                player.vz *= 0.95;
            }

            // Giới hạn tốc độ
            let speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
            if (speed > player.maxSpeed) {
                player.vx = (player.vx / speed) * player.maxSpeed;
                player.vz = (player.vz / speed) * player.maxSpeed;
            }
            // Ma sát
            player.vx *= 0.98;
            player.vz *= 0.98;

            // Cập nhật vị trí
            player.mesh.position.x += player.vx;
            player.mesh.position.z += player.vz;

            // Giới hạn bản đồ
            const bound = 45;
            player.mesh.position.x = Math.max(-bound, Math.min(bound, player.mesh.position.x));
            player.mesh.position.z = Math.max(-bound, Math.min(bound, player.mesh.position.z));

            // 2. Xe AI di chuyển ngẫu nhiên
            aiCars.forEach(ai => {
                ai.vx += (Math.random() - 0.5) * 0.02;
                ai.vz += (Math.random() - 0.5) * 0.02;
                let aiSpeed = Math.sqrt(ai.vx*ai.vx + ai.vz*ai.vz);
                if (aiSpeed > 0.2) {
                    ai.vx = (ai.vx / aiSpeed) * 0.2;
                    ai.vz = (ai.vz / aiSpeed) * 0.2;
                }
                ai.mesh.position.x += ai.vx;
                ai.mesh.position.z += ai.vz;
                // Quay đầu theo hướng di chuyển
                if (aiSpeed > 0.01) {
                    ai.mesh.rotation.y = Math.atan2(ai.vx, ai.vz);
                }
                // Giới hạn
                ai.mesh.position.x = Math.max(-bound, Math.min(bound, ai.mesh.position.x));
                ai.mesh.position.z = Math.max(-bound, Math.min(bound, ai.mesh.position.z));
                // Hồi máu từ từ
                ai.health = Math.min(100, ai.health + 0.01);
            });

            // 3. Va chạm
            // Player vs AI
            aiCars.forEach(ai => {
                const dx = player.mesh.position.x - ai.mesh.position.x;
                const dz = player.mesh.position.z - ai.mesh.position.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                if (dist < 2.0) {
                    // Lực va chạm
                    const force = Math.sqrt(player.vx*player.vx + player.vz*player.vz) + Math.sqrt(ai.vx*ai.vx + ai.vz*ai.vz);
                    if (force > 0.1) {
                        // Damage
                        const damage = force * 20 / upgradeLevel.armor;
                        player.health = Math.max(0, player.health - damage);
                        ai.health = Math.max(0, ai.health - damage * 0.8);
                        // Điểm
                        totalCrashes++;
                        score += Math.floor(force * 10);
                        // Particles
                        createCrashParticles(
                            (player.mesh.position.x + ai.mesh.position.x)/2,
                            0.5,
                            (player.mesh.position.z + ai.mesh.position.z)/2,
                            0xffaa00
                        );
                        // Đẩy nhau
                        if (dist > 0) {
                            const push = force * 2;
                            player.mesh.position.x += (dx / dist) * push * 0.1;
                            player.mesh.position.z += (dz / dist) * push * 0.1;
                            ai.mesh.position.x -= (dx / dist) * push * 0.1;
                            ai.mesh.position.z -= (dz / dist) * push * 0.1;
                        }
                    }
                    // Nếu AI chết
                    if (ai.health <= 0) {
                        score += 100;
                        totalCrashes += 1;
                        createCrashParticles(ai.mesh.position.x, 0.5, ai.mesh.position.z, ai.color);
                        ai.health = 100;
                        ai.mesh.position.x = (Math.random() - 0.5) * 30;
                        ai.mesh.position.z = (Math.random() - 0.5) * 30;
                    }
                }
            });

            // Player vs vật cản
            obstacles.forEach(obs => {
                const dx = player.mesh.position.x - obs.position.x;
                const dz = player.mesh.position.z - obs.position.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                if (dist < 2.0) {
                    const speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
                    if (speed > 0.1) {
                        const damage = speed * 15 / upgradeLevel.armor;
                        player.health = Math.max(0, player.health - damage);
                        totalCrashes++;
                        score += Math.floor(speed * 5);
                        createCrashParticles(obs.position.x, 0.5, obs.position.z, 0xff5500);
                        // Đẩy lùi
                        if (dist > 0) {
                            player.mesh.position.x += (dx / dist) * 2;
                            player.mesh.position.z += (dz / dist) * 2;
                        }
                    }
                }
            });

            // Cập nhật thời gian
            gameTime += 1/60;

            // Kiểm tra game over
            if (player.health <= 0) {
                gameRunning = false;
                alert('💥 GAME OVER! Điểm: ' + score);
                // Reset (có thể reload trang)
                location.reload();
            }

            // Cập nhật camera target
            controls.target.copy(player.mesh.position);
            controls.update();

            // Cập nhật particles
            particles.forEach((p, index) => {
                p.userData.life -= 0.01;
                if (p.userData.life <= 0) {
                    scene.remove(p);
                    particles.splice(index, 1);
                } else {
                    p.position.x += p.userData.vx;
                    p.position.y += p.userData.vy;
                    p.position.z += p.userData.vz;
                    p.userData.vy -= 0.005; // gravity
                    p.scale.setScalar(p.userData.life);
                }
            });

            // Cập nhật UI
            document.getElementById('score').innerText = score;
            document.getElementById('crashes').innerText = totalCrashes;
            document.getElementById('health').innerText = Math.floor(player.health) + '%';
            document.getElementById('health-fill').style.width = player.health + '%';
            document.getElementById('speed').innerText = Math.floor(speed * 200) + ' km/h';
            document.getElementById('ai-count').innerText = aiCars.length;
            document.getElementById('upgrade-score').innerText = score;

            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        animate();

        // Resize handler
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    </script>
</body>
</html>
"""

# Hiển thị game HTML qua Streamlit component
st.components.v1.html(game_html, height=1000, scrolling=False)
