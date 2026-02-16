import streamlit as st

st.set_page_config(page_title="3D Pixel Car Crash", layout="wide", initial_sidebar_state="collapsed")

# Ẩn giao diện Streamlit
st.markdown("""
<style>
    #MainMenu, footer, header {display: none;}
    .stApp {background: black; padding: 0; margin: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# Game HTML với Three.js 3D pixel
GAME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>3D Pixel Car Crash</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; -webkit-tap-highlight-color: transparent; }
        body { background: black; overflow: hidden; touch-action: none; }
        #gameCanvas {
            display: block;
            width: 100vw;
            height: 100vh;
            background: #0a0a1a;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }
        #ui {
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            background: rgba(0,0,0,0.7);
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #4fc3f7;
            pointer-events: none;
            z-index: 10;
            min-width: 200px;
            backdrop-filter: blur(2px);
        }
        #ui div { margin: 4px 0; }
        #speedometer { font-size: 18px; color: #ffaa00; }
        .health-bar {
            width: 100%;
            height: 10px;
            background: #333;
            border-radius: 5px;
            margin: 5px 0;
            overflow: hidden;
        }
        .health-fill { height: 100%; background: #4caf50; }
        #mobile-controls {
            position: absolute;
            bottom: 30px;
            left: 0;
            width: 100%;
            display: none;
            justify-content: center;
            gap: 15px;
            padding: 0 15px;
            z-index: 20;
            pointer-events: none;
        }
        .ctrl-row {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .ctrl-btn {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: rgba(40,40,50,0.8);
            border: 3px solid #4fc3f7;
            color: white;
            font-size: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: auto;
            backdrop-filter: blur(5px);
            box-shadow: 0 0 15px #4fc3f7;
            touch-action: manipulation;
            font-weight: bold;
            cursor: pointer;
        }
        .ctrl-btn:active {
            background: #4fc3f7;
            color: black;
            transform: scale(0.9);
        }
        @media (max-width: 768px) {
            #mobile-controls { display: flex; }
            #ui { font-size: 12px; padding: 8px; min-width: 160px; }
        }
    </style>
</head>
<body>
    <canvas id="gameCanvas"></canvas>

    <div id="ui">
        <div style="font-size: 18px; font-weight: bold; color: #4fc3f7;">💥 3D PIXEL CRASH</div>
        <div>🏆 ĐIỂM: <span id="score">0</span></div>
        <div>💥 VA CHẠM: <span id="crashes">0</span></div>
        <div id="speedometer">⚡ <span id="speed">0</span> km/h</div>
        <div>🛞 ĐỘNG CƠ</div>
        <div class="health-bar"><div id="engine-health" class="health-fill" style="width:100%"></div></div>
        <div>🚪 CỬA TRÁI</div>
        <div class="health-bar"><div id="doorL-health" class="health-fill" style="width:100%"></div></div>
        <div>🚪 CỬA PHẢI</div>
        <div class="health-bar"><div id="doorR-health" class="health-fill" style="width:100%"></div></div>
        <div>⚙️ BÁNH TRÁI</div>
        <div class="health-bar"><div id="wheelL-health" class="health-fill" style="width:100%"></div></div>
        <div>⚙️ BÁNH PHẢI</div>
        <div class="health-bar"><div id="wheelR-health" class="health-fill" style="width:100%"></div></div>
    </div>

    <div id="mobile-controls">
        <div class="ctrl-row">
            <div class="ctrl-btn" data-key="left">←</div>
            <div class="ctrl-btn" data-key="up">↑</div>
            <div class="ctrl-btn" data-key="down">↓</div>
            <div class="ctrl-btn" data-key="right">→</div>
            <div class="ctrl-btn" data-key="space" style="width:90px; border-radius:40px;">⏹️</div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        (function() {
            // ---------- KHỞI TẠO THREE.JS ----------
            const canvas = document.getElementById('gameCanvas');
            const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: "high-performance" });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0a1a);

            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 15, 30);
            camera.lookAt(0, 0, 0);

            // ---------- ÁNH SÁNG ----------
            const ambientLight = new THREE.AmbientLight(0x404060);
            scene.add(ambientLight);

            const dirLight = new THREE.DirectionalLight(0xffeedd, 1.2);
            dirLight.position.set(10, 20, 10);
            dirLight.castShadow = true;
            dirLight.receiveShadow = true;
            dirLight.shadow.mapSize.width = 1024;
            dirLight.shadow.mapSize.height = 1024;
            const d = 50;
            dirLight.shadow.camera.left = -d;
            dirLight.shadow.camera.right = d;
            dirLight.shadow.camera.top = d;
            dirLight.shadow.camera.bottom = -d;
            dirLight.shadow.camera.near = 1;
            dirLight.shadow.camera.far = 50;
            scene.add(dirLight);

            const pointLight = new THREE.PointLight(0x4466ff, 0.5);
            pointLight.position.set(-5, 5, 10);
            scene.add(pointLight);

            // ---------- MẶT ĐẤT ----------
            const groundGeo = new THREE.PlaneGeometry(200, 200);
            const groundMat = new THREE.MeshStandardMaterial({ color: 0x1a2a2a, roughness: 0.8 });
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -0.5;
            ground.receiveShadow = true;
            scene.add(ground);

            // Đường kẻ (dùng hình hộp nhỏ)
            const lineMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
            for (let i = -90; i <= 90; i += 20) {
                const line = new THREE.Mesh(new THREE.BoxGeometry(1, 0.1, 10), lineMat);
                line.position.set(i, -0.45, 0);
                line.receiveShadow = true;
                scene.add(line);
                
                const line2 = new THREE.Mesh(new THREE.BoxGeometry(10, 0.1, 1), lineMat);
                line2.position.set(0, -0.45, i);
                line2.receiveShadow = true;
                scene.add(line2);
            }

            // ---------- VẬT CẢN ----------
            const obstacles = [];
            function createObstacle(x, z, color) {
                const box = new THREE.Mesh(
                    new THREE.BoxGeometry(4, 2, 4),
                    new THREE.MeshStandardMaterial({ color })
                );
                box.position.set(x, 0.5, z);
                box.castShadow = true;
                box.receiveShadow = true;
                scene.add(box);
                obstacles.push(box);
            }
            
            // Tường bao
            const wallMat = new THREE.MeshStandardMaterial({ color: 0x884422 });
            const walls = [
                new THREE.Mesh(new THREE.BoxGeometry(200, 5, 5), wallMat),
                new THREE.Mesh(new THREE.BoxGeometry(200, 5, 5), wallMat),
                new THREE.Mesh(new THREE.BoxGeometry(5, 5, 200), wallMat),
                new THREE.Mesh(new THREE.BoxGeometry(5, 5, 200), wallMat)
            ];
            walls[0].position.set(0, 1, -100);
            walls[1].position.set(0, 1, 100);
            walls[2].position.set(-100, 1, 0);
            walls[3].position.set(100, 1, 0);
            walls.forEach(w => { w.castShadow = true; w.receiveShadow = true; scene.add(w); });
            
            // Vật cản rải rác
            for (let i = 0; i < 15; i++) {
                createObstacle(
                    (Math.random() - 0.5) * 160,
                    (Math.random() - 0.5) * 160,
                    Math.random() * 0xffffff
                );
            }

            // ---------- XE PLAYER (PIXEL 3D) ----------
            const playerGroup = new THREE.Group();
            
            // Thân xe chính (tạo từ các pixel)
            const pixelMat = new THREE.MeshStandardMaterial({ color: 0x2277cc });
            const pixelSize = 2;
            const positions = [
                [-3, 0, -5], [-1, 0, -5], [1, 0, -5], [3, 0, -5],
                [-4, 1, -3], [-2, 1, -3], [0, 1, -3], [2, 1, -3], [4, 1, -3],
                [-4, 2, -1], [-2, 2, -1], [0, 2, -1], [2, 2, -1], [4, 2, -1],
                [-3, 3, 1], [-1, 3, 1], [1, 3, 1], [3, 3, 1],
                [-2, 2, 3], [0, 2, 3], [2, 2, 3],
                [-1, 1, 5], [1, 1, 5]
            ];
            
            positions.forEach(pos => {
                const pixel = new THREE.Mesh(
                    new THREE.BoxGeometry(pixelSize, pixelSize, pixelSize),
                    new THREE.MeshStandardMaterial({ color: 0x2277cc })
                );
                pixel.position.set(pos[0], pos[1], pos[2]);
                pixel.castShadow = true;
                pixel.receiveShadow = true;
                playerGroup.add(pixel);
            });
            
            // Bánh xe
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
            const wheelPos = [[-4, 0, -6], [4, 0, -6], [-4, 0, 6], [4, 0, 6]];
            wheelPos.forEach(pos => {
                const wheel = new THREE.Mesh(
                    new THREE.CylinderGeometry(1.5, 1.5, 1, 8),
                    wheelMat
                );
                wheel.rotation.z = Math.PI/2;
                wheel.position.set(pos[0], pos[1], pos[2]);
                wheel.castShadow = true;
                wheel.receiveShadow = true;
                playerGroup.add(wheel);
            });
            
            // Đèn
            const lightMat = new THREE.MeshStandardMaterial({ color: 0xffffaa, emissive: 0x442200 });
            const headLights = [[-3, 1, -7], [3, 1, -7]];
            headLights.forEach(pos => {
                const light = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), lightMat);
                light.position.set(pos[0], pos[1], pos[2]);
                light.castShadow = true;
                playerGroup.add(light);
            });
            
            playerGroup.position.set(0, 1, 0);
            scene.add(playerGroup);

            // ---------- XE AI ----------
            const aiCars = [];
            const aiColors = [0xff3333, 0x33ff33, 0xffaa00, 0xff44aa, 0x44aaff];
            for (let i = 0; i < 5; i++) {
                const aiGroup = new THREE.Group();
                const color = aiColors[i % aiColors.length];
                
                // Thân AI (đơn giản hơn)
                for (let x = -3; x <= 3; x+=2) {
                    for (let z = -5; z <= 5; z+=2) {
                        const pixel = new THREE.Mesh(
                            new THREE.BoxGeometry(1.5, 1.5, 1.5),
                            new THREE.MeshStandardMaterial({ color })
                        );
                        pixel.position.set(x, 0.5, z);
                        pixel.castShadow = true;
                        pixel.receiveShadow = true;
                        aiGroup.add(pixel);
                    }
                }
                
                aiGroup.position.set(
                    (Math.random() - 0.5) * 150,
                    1,
                    (Math.random() - 0.5) * 150
                );
                scene.add(aiGroup);
                aiCars.push({
                    mesh: aiGroup,
                    vx: (Math.random() - 0.5) * 0.2,
                    vz: (Math.random() - 0.5) * 0.2,
                    color: color
                });
            }

            // ---------- HỆ THỐNG PARTICLE ----------
            const particles = [];
            function createCrashParticles(x, y, z, color) {
                for (let i = 0; i < 20; i++) {
                    const size = Math.random() * 0.5 + 0.2;
                    const particle = new THREE.Mesh(
                        new THREE.BoxGeometry(size, size, size),
                        new THREE.MeshStandardMaterial({ color, emissive: 0x442200 })
                    );
                    particle.position.set(x, y, z);
                    particle.userData = {
                        vx: (Math.random() - 0.5) * 0.5,
                        vy: Math.random() * 0.5,
                        vz: (Math.random() - 0.5) * 0.5,
                        life: 1.0
                    };
                    scene.add(particle);
                    particles.push(particle);
                }
            }

            // ---------- BIẾN ĐIỀU KHIỂN ----------
            const keys = { up: false, down: false, left: false, right: false, space: false };
            
            // PC keyboard
            window.addEventListener('keydown', (e) => {
                const k = e.key;
                if (k === 'w' || k === 'W' || k === 'ArrowUp') { keys.up = true; e.preventDefault(); }
                if (k === 's' || k === 'S' || k === 'ArrowDown') { keys.down = true; e.preventDefault(); }
                if (k === 'a' || k === 'A' || k === 'ArrowLeft') { keys.left = true; e.preventDefault(); }
                if (k === 'd' || k === 'D' || k === 'ArrowRight') { keys.right = true; e.preventDefault(); }
                if (k === ' ') { keys.space = true; e.preventDefault(); }
            });
            window.addEventListener('keyup', (e) => {
                const k = e.key;
                if (k === 'w' || k === 'W' || k === 'ArrowUp') { keys.up = false; e.preventDefault(); }
                if (k === 's' || k === 'S' || k === 'ArrowDown') { keys.down = false; e.preventDefault(); }
                if (k === 'a' || k === 'A' || k === 'ArrowLeft') { keys.left = false; e.preventDefault(); }
                if (k === 'd' || k === 'D' || k === 'ArrowRight') { keys.right = false; e.preventDefault(); }
                if (k === ' ') { keys.space = false; e.preventDefault(); }
            });

            // Mobile controls
            document.querySelectorAll('.ctrl-btn').forEach(btn => {
                const key = btn.dataset.key;
                btn.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    keys[key] = true;
                });
                btn.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    keys[key] = false;
                });
                btn.addEventListener('touchcancel', (e) => {
                    e.preventDefault();
                    keys[key] = false;
                });
                btn.addEventListener('mousedown', (e) => { e.preventDefault(); keys[key] = true; });
                btn.addEventListener('mouseup', (e) => { e.preventDefault(); keys[key] = false; });
                btn.addEventListener('mouseleave', (e) => { keys[key] = false; });
            });

            // ---------- VẬT LÝ ----------
            const player = {
                mesh: playerGroup,
                vx: 0, vz: 0,
                angle: 0,
                maxSpeed: 0.5,
                acceleration: 0.02,
                turnSpeed: 0.02,
                health: 100,
                engineHealth: 100,
                doorL: 100,
                doorR: 100,
                wheelL: 100,
                wheelR: 100
            };

            // ---------- GAME STATE ----------
            let score = 0;
            let totalCrashes = 0;
            let gameRunning = true;

            // ---------- VA CHẠM ----------
            function checkCollisions() {
                // Player vs AI (đơn giản: khoảng cách)
                aiCars.forEach(ai => {
                    const dx = player.mesh.position.x - ai.mesh.position.x;
                    const dz = player.mesh.position.z - ai.mesh.position.z;
                    const dist = Math.sqrt(dx*dx + dz*dz);
                    if (dist < 8) {
                        const speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
                        if (speed > 0.1) {
                            createCrashParticles(
                                (player.mesh.position.x + ai.mesh.position.x)/2,
                                1,
                                (player.mesh.position.z + ai.mesh.position.z)/2,
                                0xffaa00
                            );
                            player.engineHealth -= speed * 10;
                            score += Math.floor(speed * 20);
                            totalCrashes++;
                            
                            // Đẩy
                            if (dist > 0) {
                                const nx = dx / dist;
                                const nz = dz / dist;
                                player.mesh.position.x += nx * 2;
                                player.mesh.position.z += nz * 2;
                                ai.mesh.position.x -= nx * 2;
                                ai.mesh.position.z -= nz * 2;
                                player.vx = -player.vx * 0.3;
                                player.vz = -player.vz * 0.3;
                                ai.vx = -ai.vx * 0.3;
                                ai.vz = -ai.vz * 0.3;
                            }
                        }
                    }
                });
                
                // Player vs obstacles
                obstacles.forEach(obs => {
                    const dx = player.mesh.position.x - obs.position.x;
                    const dz = player.mesh.position.z - obs.position.z;
                    const dist = Math.sqrt(dx*dx + dz*dz);
                    if (dist < 6) {
                        const speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
                        if (speed > 0.1) {
                            createCrashParticles(
                                (player.mesh.position.x + obs.position.x)/2,
                                1,
                                (player.mesh.position.z + obs.position.z)/2,
                                0xff5500
                            );
                            player.engineHealth -= speed * 8;
                            score += Math.floor(speed * 10);
                            totalCrashes++;
                            
                            if (dist > 0) {
                                const nx = dx / dist;
                                const nz = dz / dist;
                                player.mesh.position.x += nx * 3;
                                player.mesh.position.z += nz * 3;
                                player.vx = -player.vx * 0.2;
                                player.vz = -player.vz * 0.2;
                            }
                        }
                    }
                });
            }

            // ---------- CẬP NHẬT CAMERA ----------
            function updateCamera() {
                camera.position.x = player.mesh.position.x;
                camera.position.z = player.mesh.position.z + 25;
                camera.position.y = player.mesh.position.y + 10;
                camera.lookAt(player.mesh.position.x, player.mesh.position.y + 2, player.mesh.position.z);
            }

            // ---------- CẬP NHẬT UI ----------
            function updateUI() {
                document.getElementById('score').innerText = Math.floor(score);
                document.getElementById('crashes').innerText = totalCrashes;
                const speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz) * 50;
                document.getElementById('speed').innerText = Math.floor(speed);
                
                document.getElementById('engine-health').style.width = Math.max(0, player.engineHealth) + '%';
                document.getElementById('doorL-health').style.width = player.doorL + '%';
                document.getElementById('doorR-health').style.width = player.doorR + '%';
                document.getElementById('wheelL-health').style.width = player.wheelL + '%';
                document.getElementById('wheelR-health').style.width = player.wheelR + '%';
            }

            // ---------- GAME LOOP ----------
            function gameLoop() {
                if (!gameRunning) return;
                
                // Điều khiển
                if (keys.up) {
                    player.vx += Math.sin(player.angle) * player.acceleration;
                    player.vz += Math.cos(player.angle) * player.acceleration;
                }
                if (keys.down) {
                    player.vx -= Math.sin(player.angle) * player.acceleration * 0.6;
                    player.vz -= Math.cos(player.angle) * player.acceleration * 0.6;
                }
                if (keys.left) {
                    player.angle += player.turnSpeed;
                }
                if (keys.right) {
                    player.angle -= player.turnSpeed;
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
                player.mesh.rotation.y = player.angle;
                
                // Giới hạn map
                const bound = 90;
                player.mesh.position.x = Math.max(-bound, Math.min(bound, player.mesh.position.x));
                player.mesh.position.z = Math.max(-bound, Math.min(bound, player.mesh.position.z));
                
                // AI di chuyển
                aiCars.forEach(ai => {
                    ai.vx += (Math.random() - 0.5) * 0.02;
                    ai.vz += (Math.random() - 0.5) * 0.02;
                    let sp = Math.sqrt(ai.vx*ai.vx + ai.vz*ai.vz);
                    if (sp > 0.2) {
                        ai.vx = (ai.vx / sp) * 0.2;
                        ai.vz = (ai.vz / sp) * 0.2;
                    }
                    ai.mesh.position.x += ai.vx;
                    ai.mesh.position.z += ai.vz;
                    if (sp > 0.01) {
                        ai.mesh.rotation.y = Math.atan2(ai.vx, ai.vz);
                    }
                    ai.mesh.position.x = Math.max(-bound, Math.min(bound, ai.mesh.position.x));
                    ai.mesh.position.z = Math.max(-bound, Math.min(bound, ai.mesh.position.z));
                });
                
                // Va chạm
                checkCollisions();
                
                // Particles
                particles.forEach((p, index) => {
                    p.userData.life -= 0.01;
                    if (p.userData.life <= 0) {
                        scene.remove(p);
                        particles.splice(index, 1);
                    } else {
                        p.position.x += p.userData.vx;
                        p.position.y += p.userData.vy;
                        p.position.z += p.userData.vz;
                        p.userData.vy -= 0.005;
                        p.scale.setScalar(p.userData.life);
                    }
                });
                
                // Camera
                updateCamera();
                
                // UI
                updateUI();
                
                // Game over
                if (player.engineHealth <= 0) {
                    gameRunning = false;
                    setTimeout(() => {
                        alert('💥 GAME OVER! ĐIỂM: ' + Math.floor(score));
                        location.reload();
                    }, 100);
                }
                
                renderer.render(scene, camera);
                requestAnimationFrame(gameLoop);
            }
            
            gameLoop();

            // ---------- RESIZE ----------
            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
        })();
    </script>
</body>
</html>
"""

st.components.v1.html(GAME_HTML, height=1000, scrolling=False)
