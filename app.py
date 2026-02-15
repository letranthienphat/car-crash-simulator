import streamlit as st

st.set_page_config(page_title="2D Pixel Car Crash", layout="wide", initial_sidebar_state="collapsed")

# Ẩn hoàn toàn giao diện Streamlit
st.markdown("""
<style>
    #MainMenu, footer, header {display: none;}
    .stApp {background: black; padding: 0; margin: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# Đọc file HTML game (được nhúng trực tiếp dưới dạng string)
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>2D Pixel Car Crash</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; }
        body { background: black; overflow: hidden; touch-action: none; }
        #gameCanvas {
            display: block;
            width: 100vw;
            height: 100vh;
            background: #1a2a32;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            cursor: none;
        }
        #ui {
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #4fc3f7;
            pointer-events: none;
            z-index: 10;
            min-width: 220px;
            backdrop-filter: blur(2px);
        }
        #ui div { margin: 5px 0; }
        .part-status {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        .part-name { width: 80px; }
        .part-bar {
            flex: 1;
            height: 12px;
            background: #333;
            border-radius: 6px;
            overflow: hidden;
            margin-left: 10px;
        }
        .part-fill {
            height: 100%;
            transition: width 0.2s;
        }
        .engine-fill { background: #ffaa00; }
        .door-fill { background: #4caf50; }
        .wheel-fill { background: #2196f3; }
        #mobile-controls {
            position: absolute;
            bottom: 20px;
            left: 0;
            width: 100%;
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 15px;
            z-index: 20;
            pointer-events: none;
        }
        .ctrl-btn {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            border: 3px solid rgba(255,255,255,0.6);
            color: white;
            font-size: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: auto;
            backdrop-filter: blur(5px);
            font-weight: bold;
            box-shadow: 0 0 15px rgba(0,170,255,0.5);
            touch-action: manipulation;
        }
        .ctrl-btn:active {
            background: rgba(255,255,255,0.4);
            transform: scale(0.9);
        }
        #game-over {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9);
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            font-family: 'Courier New', monospace;
            z-index: 100;
        }
        #game-over h1 { font-size: 48px; color: #ff5555; margin-bottom: 20px; }
        #game-over button {
            background: #4fc3f7;
            border: none;
            padding: 15px 30px;
            font-size: 24px;
            border-radius: 10px;
            margin-top: 30px;
            cursor: pointer;
        }
        @media (max-width: 768px) {
            #ui { font-size: 14px; padding: 10px; min-width: 160px; }
            .ctrl-btn { width: 60px; height: 60px; font-size: 26px; }
        }
    </style>
</head>
<body>
    <canvas id="gameCanvas"></canvas>
    
    <div id="ui">
        <div style="font-size: 20px; font-weight: bold; color: #4fc3f7; margin-bottom: 10px;">
            💥 2D PIXEL CRASH
        </div>
        <div>🏆 ĐIỂM: <span id="score">0</span></div>
        <div>💥 VA CHẠM: <span id="crashes">0</span></div>
        <div>⚡ TỐC ĐỘ: <span id="speed">0</span> km/h</div>
        <div style="margin: 10px 0;">🛠️ TÌNH TRẠNG XE</div>
        
        <div class="part-status">
            <span class="part-name">🛞 ĐỘNG CƠ</span>
            <div class="part-bar"><div id="engine-fill" class="part-fill engine-fill" style="width:100%"></div></div>
        </div>
        <div class="part-status">
            <span class="part-name">🚪 CỬA TRÁI</span>
            <div class="part-bar"><div id="doorL-fill" class="part-fill door-fill" style="width:100%"></div></div>
        </div>
        <div class="part-status">
            <span class="part-name">🚪 CỬA PHẢI</span>
            <div class="part-bar"><div id="doorR-fill" class="part-fill door-fill" style="width:100%"></div></div>
        </div>
        <div class="part-status">
            <span class="part-name">⚙️ BÁNH TRÁI</span>
            <div class="part-bar"><div id="wheelL-fill" class="part-fill wheel-fill" style="width:100%"></div></div>
        </div>
        <div class="part-status">
            <span class="part-name">⚙️ BÁNH PHẢI</span>
            <div class="part-bar"><div id="wheelR-fill" class="part-fill wheel-fill" style="width:100%"></div></div>
        </div>
    </div>

    <div id="mobile-controls">
        <div class="ctrl-btn" data-key="left">←</div>
        <div class="ctrl-btn" data-key="up">↑</div>
        <div class="ctrl-btn" data-key="down">↓</div>
        <div class="ctrl-btn" data-key="right">→</div>
        <div class="ctrl-btn" data-key="space" style="width:90px; border-radius:40px;">SP</div>
    </div>

    <div id="game-over">
        <h1>💥 GAME OVER</h1>
        <h2>ĐIỂM: <span id="final-score">0</span></h2>
        <h2>VA CHẠM: <span id="final-crashes">0</span></h2>
        <button onclick="location.reload()">CHƠI LẠI</button>
    </div>

    <script>
        (function() {
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            
            // ---------- KÍCH THƯỚC CANVAS ----------
            function resizeCanvas() {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            // ---------- THẾ GIỚI GAME ----------
            const world = {
                width: 3000,   // chiều rộng thế giới ảo
                height: 3000,
                camera: { x: 0, y: 0 }
            };

            // ---------- XE NGƯỜI CHƠI (CÁC BỘ PHẬN) ----------
            const player = {
                // Vị trí và vật lý
                x: 1500, y: 1500,
                vx: 0, vy: 0,
                angle: 0,
                width: 40,     // kích thước pixel
                height: 70,
                
                // Các bộ phận (mỗi bộ có máu riêng, max 100)
                parts: {
                    engine: { health: 100, max: 100, smoke: 0, fire: false },
                    doorL:  { health: 100, max: 100 },
                    doorR:  { health: 100, max: 100 },
                    wheelL: { health: 100, max: 100 },
                    wheelR: { health: 100, max: 100 }
                },
                
                // Thông số vận hành (ảnh hưởng bởi hư hỏng)
                maxSpeed: 6,
                acceleration: 0.2,
                turnSpeed: 0.03,
                friction: 0.98,
                
                // Hiệu ứng
                smokeParticles: [],
                fireParticles: []
            };

            // ---------- XE AI ----------
            const aiCars = [];
            function createAICar(x, y) {
                return {
                    x: x, y: y,
                    vx: 0, vy: 0,
                    angle: Math.random() * Math.PI * 2,
                    width: 36, height: 60,
                    color: `hsl(${Math.random()*360}, 70%, 50%)`,
                    // AI đơn giản: đi theo đường (mô phỏng)
                    targetX: Math.random() * world.width,
                    targetY: Math.random() * world.height,
                    aiTimer: 0,
                    maxSpeed: 3 + Math.random() * 2,
                    turnSpeed: 0.02,
                    // Các bộ phận (AI cũng có thể hư)
                    parts: {
                        engine: { health: 100, max: 100 },
                        wheelL: { health: 100, max: 100 },
                        wheelR: { health: 100, max: 100 }
                    }
                };
            }

            // Tạo 8 xe AI
            for (let i = 0; i < 8; i++) {
                aiCars.push(createAICar(
                    500 + Math.random() * 2000,
                    500 + Math.random() * 2000
                ));
            }

            // ---------- VẬT CẢN (TƯỜNG, CÂY, NHÀ) ----------
            const obstacles = [];
            // Tường bao quanh (để xe không đi ra ngoài)
            const wallThickness = 50;
            obstacles.push({ x: world.width/2, y: -wallThickness/2, w: world.width, h: wallThickness, type: 'wall' }); // top
            obstacles.push({ x: world.width/2, y: world.height + wallThickness/2, w: world.width, h: wallThickness, type: 'wall' }); // bottom
            obstacles.push({ x: -wallThickness/2, y: world.height/2, w: wallThickness, h: world.height, type: 'wall' }); // left
            obstacles.push({ x: world.width + wallThickness/2, y: world.height/2, w: wallThickness, h: world.height, type: 'wall' }); // right
            
            // Cây cối và nhà cửa (dạng hình chữ nhật)
            for (let i = 0; i < 40; i++) {
                obstacles.push({
                    x: 200 + Math.random() * 2600,
                    y: 200 + Math.random() * 2600,
                    w: 30 + Math.random() * 40,
                    h: 30 + Math.random() * 40,
                    type: 'tree',
                    color: `rgb(${40+Math.random()*30},${80+Math.random()*50},${20})`
                });
            }
            for (let i = 0; i < 15; i++) {
                obstacles.push({
                    x: 300 + Math.random() * 2400,
                    y: 300 + Math.random() * 2400,
                    w: 60 + Math.random() * 80,
                    h: 60 + Math.random() * 80,
                    type: 'building',
                    color: `rgb(${100+Math.random()*100},${70+Math.random()*60},${40})`
                });
            }

            // ---------- PIXEL VỠ (CRASH PARTICLES) ----------
            const particles = [];
            function createCrashParticles(x, y, color, count = 10) {
                for (let i = 0; i < count; i++) {
                    particles.push({
                        x: x, y: y,
                        vx: (Math.random() - 0.5) * 6,
                        vy: (Math.random() - 0.5) * 6,
                        size: 2 + Math.random() * 4,
                        color: color,
                        life: 1.0,
                        gravity: 0.1
                    });
                }
            }

            // ---------- KHÓI & LỬA ----------
            function createSmoke(x, y) {
                player.smokeParticles.push({
                    x: x, y: y,
                    vx: (Math.random() - 0.5) * 1,
                    vy: -Math.random() * 2 - 1,
                    size: 5 + Math.random() * 10,
                    life: 1.0,
                    color: '#888'
                });
            }
            function createFire(x, y) {
                player.fireParticles.push({
                    x: x, y: y,
                    vx: (Math.random() - 0.5) * 2,
                    vy: -Math.random() * 3 - 2,
                    size: 4 + Math.random() * 8,
                    life: 1.0,
                    color: `hsl(${30+Math.random()*20}, 100%, 50%)`
                });
            }

            // ---------- ĐIỀU KHIỂN ----------
            const keys = { up: false, down: false, left: false, right: false, space: false };
            
            // Bàn phím PC
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
                // Cho cả mouse (test trên desktop)
                btn.addEventListener('mousedown', (e) => { e.preventDefault(); keys[key] = true; });
                btn.addEventListener('mouseup', (e) => { e.preventDefault(); keys[key] = false; });
                btn.addEventListener('mouseleave', (e) => { keys[key] = false; });
            });

            // ---------- GAME STATE ----------
            let score = 0;
            let totalCrashes = 0;
            let gameRunning = true;
            let gameTime = 0;

            // ---------- HÀM TÍNH TOÁN HƯ HỎNG DỰA TRÊN VỊ TRÍ VA CHẠM ----------
            function applyDamage(force, collisionX, collisionY) {
                // Xác định vị trí va chạm tương đối trên xe
                const localX = collisionX - player.x;
                const localY = collisionY - player.y;
                // Xoay theo góc xe
                const cos = Math.cos(player.angle);
                const sin = Math.sin(player.angle);
                const localRelX = localX * cos + localY * sin; // dọc theo chiều dài xe
                const localRelY = -localX * sin + localY * cos; // ngang xe
                
                // Phân vùng: động cơ phía trước (localRelY < 0), cửa bên trái (localRelX < 0), v.v.
                // Tạm ước lượng: xe dài 70, rộng 40, gốc tọa độ tại tâm
                const halfLen = player.height / 2; // 35
                const halfWid = player.width / 2;  // 20
                
                // Động cơ: phía trước (localRelY < -halfLen/2)
                if (localRelY < -halfLen/2) {
                    player.parts.engine.health = Math.max(0, player.parts.engine.health - force * 2);
                }
                // Cửa trái: bên trái (localRelX < -halfWid/2) và giữa
                if (localRelX < -halfWid/2) {
                    player.parts.doorL.health = Math.max(0, player.parts.doorL.health - force * 1.5);
                }
                // Cửa phải: bên phải
                if (localRelX > halfWid/2) {
                    player.parts.doorR.health = Math.max(0, player.parts.doorR.health - force * 1.5);
                }
                // Bánh trái: phía sau và trái
                if (localRelY > halfLen/2 && localRelX < 0) {
                    player.parts.wheelL.health = Math.max(0, player.parts.wheelL.health - force * 2.5);
                }
                // Bánh phải: phía sau và phải
                if (localRelY > halfLen/2 && localRelX > 0) {
                    player.parts.wheelR.health = Math.max(0, player.parts.wheelR.health - force * 2.5);
                }
                // Nếu không rõ, giảm nhẹ toàn bộ
                if (force > 5) {
                    for (let part in player.parts) {
                        player.parts[part].health = Math.max(0, player.parts[part].health - force * 0.2);
                    }
                }
            }

            // ---------- CẬP NHẬT VẬT LÝ PLAYER ----------
            function updatePlayer() {
                // Điều khiển
                if (keys.up) {
                    player.vx += Math.sin(player.angle) * player.acceleration;
                    player.vy += Math.cos(player.angle) * player.acceleration;
                }
                if (keys.down) {
                    player.vx -= Math.sin(player.angle) * player.acceleration * 0.6;
                    player.vy -= Math.cos(player.angle) * player.acceleration * 0.6;
                }
                if (keys.left) {
                    player.angle -= player.turnSpeed * (keys.up ? 1 : 0.5);
                }
                if (keys.right) {
                    player.angle += player.turnSpeed * (keys.up ? 1 : 0.5);
                }
                if (keys.space) {
                    player.vx *= 0.9;
                    player.vy *= 0.9;
                }

                // Giới hạn tốc độ theo tình trạng bánh xe và động cơ
                let speedFactor = 1.0;
                if (player.parts.engine.health < 30) speedFactor *= 0.5;
                if (player.parts.wheelL.health < 20 || player.parts.wheelR.health < 20) speedFactor *= 0.6;
                
                let speed = Math.hypot(player.vx, player.vy);
                let maxSp = player.maxSpeed * speedFactor;
                if (speed > maxSp) {
                    player.vx = (player.vx / speed) * maxSp;
                    player.vy = (player.vy / speed) * maxSp;
                }

                // Ma sát
                player.vx *= player.friction;
                player.vy *= player.friction;

                // Di chuyển
                player.x += player.vx;
                player.y += player.vy;

                // Giới hạn bởi tường (va chạm cứng)
                if (player.x < 50) { player.x = 50; player.vx = 0; }
                if (player.x > world.width - 50) { player.x = world.width - 50; player.vx = 0; }
                if (player.y < 50) { player.y = 50; player.vy = 0; }
                if (player.y > world.height - 50) { player.y = world.height - 50; player.vy = 0; }

                // Tạo khói nếu động cơ yếu
                if (player.parts.engine.health < 40 && Math.random() < 0.1) {
                    createSmoke(player.x - Math.sin(player.angle)*30, player.y - Math.cos(player.angle)*30);
                }
                // Tạo lửa nếu động cơ = 0
                if (player.parts.engine.health <= 0 && Math.random() < 0.2) {
                    createFire(player.x - Math.sin(player.angle)*20, player.y - Math.cos(player.angle)*20);
                }

                // Nếu tất cả các bộ phận quan trọng đều hỏng? Đơn giản: nếu động cơ = 0 và ít nhất 1 bánh = 0 thì xe không điều khiển được
                if (player.parts.engine.health <= 0) {
                    // xe không thể tăng tốc
                    keys.up = false; // tạm thời vô hiệu hóa tăng tốc
                }
            }

            // ---------- CẬP NHẬT AI (ĐƠN GIẢN NHƯNG CÓ TÍNH TRÁNH) ----------
            function updateAI() {
                aiCars.forEach(ai => {
                    // Di chuyển về target ngẫu nhiên
                    ai.aiTimer += 0.01;
                    if (ai.aiTimer > 3) {
                        ai.targetX = player.x + (Math.random() - 0.5) * 500;
                        ai.targetY = player.y + (Math.random() - 0.5) * 500;
                        ai.aiTimer = 0;
                    }
                    
                    const dx = ai.targetX - ai.x;
                    const dy = ai.targetY - ai.y;
                    const dist = Math.hypot(dx, dy);
                    if (dist > 10) {
                        const targetAngle = Math.atan2(dy, dx);
                        let angleDiff = targetAngle - ai.angle;
                        while (angleDiff > Math.PI) angleDiff -= Math.PI*2;
                        while (angleDiff < -Math.PI) angleDiff += Math.PI*2;
                        ai.angle += angleDiff * 0.03;
                        
                        ai.vx += Math.sin(ai.angle) * 0.1;
                        ai.vy += Math.cos(ai.angle) * 0.1;
                    }
                    
                    // Giới hạn tốc độ
                    let sp = Math.hypot(ai.vx, ai.vy);
                    if (sp > ai.maxSpeed) {
                        ai.vx = (ai.vx / sp) * ai.maxSpeed;
                        ai.vy = (ai.vy / sp) * ai.maxSpeed;
                    }
                    
                    ai.x += ai.vx;
                    ai.y += ai.vy;
                    
                    // Ma sát
                    ai.vx *= 0.98;
                    ai.vy *= 0.98;
                    
                    // Giới hạn map
                    ai.x = Math.max(50, Math.min(world.width - 50, ai.x));
                    ai.y = Math.max(50, Math.min(world.height - 50, ai.y));
                    
                    // Hồi phục nhẹ (để AI không chết mãi)
                    ai.parts.engine.health = Math.min(100, ai.parts.engine.health + 0.1);
                });
            }

            // ---------- KIỂM TRA VA CHẠM ----------
            function checkCollisions() {
                // Player vs AI
                aiCars.forEach(ai => {
                    const dx = player.x - ai.x;
                    const dy = player.y - ai.y;
                    const dist = Math.hypot(dx, dy);
                    const minDist = (player.height/2 + ai.height/2) * 0.8; // ngưỡng va chạm
                    if (dist < minDist) {
                        // Tính lực
                        const vRelX = player.vx - ai.vx;
                        const vRelY = player.vy - ai.vy;
                        const force = Math.hypot(vRelX, vRelY);
                        if (force > 0.5) {
                            // Tạo pixel vỡ từ cả hai xe
                            createCrashParticles((player.x+ai.x)/2, (player.y+ai.y)/2, '#ffaa00', 15);
                            createCrashParticles(player.x, player.y, '#2277cc', 8);
                            createCrashParticles(ai.x, ai.y, ai.color, 8);
                            
                            // Gây damage dựa trên vị trí
                            applyDamage(force, (player.x+ai.x)/2, (player.y+ai.y)/2);
                            
                            // Điểm
                            score += Math.floor(force * 5);
                            totalCrashes++;
                            
                            // Đẩy nhau
                            if (dist > 0) {
                                const overlap = minDist - dist;
                                const normX = dx / dist;
                                const normY = dy / dist;
                                player.x += normX * overlap * 0.5;
                                player.y += normY * overlap * 0.5;
                                ai.x -= normX * overlap * 0.5;
                                ai.y -= normY * overlap * 0.5;
                                
                                // Thay đổi vận tốc
                                player.vx += normX * force * 0.5;
                                player.vy += normY * force * 0.5;
                                ai.vx -= normX * force * 0.5;
                                ai.vy -= normY * force * 0.5;
                            }
                        }
                    }
                });

                // Player vs obstacles
                obstacles.forEach(obs => {
                    // Va chạm AABB đơn giản
                    const halfW = player.width/2;
                    const halfH = player.height/2;
                    const obsHalfW = obs.w/2;
                    const obsHalfH = obs.h/2;
                    
                    if (Math.abs(player.x - obs.x) < halfW + obsHalfW &&
                        Math.abs(player.y - obs.y) < halfH + obsHalfH) {
                        
                        // Tính lực va chạm
                        const speed = Math.hypot(player.vx, player.vy);
                        if (speed > 0.2) {
                            createCrashParticles(player.x, player.y, obs.color || '#888888', 10);
                            applyDamage(speed, player.x, player.y); // tạm thời lấy tâm xe
                            score += Math.floor(speed * 3);
                            totalCrashes++;
                            
                            // Đẩy lùi
                            const dx = player.x - obs.x;
                            const dy = player.y - obs.y;
                            const overlapX = halfW + obsHalfW - Math.abs(dx);
                            const overlapY = halfH + obsHalfH - Math.abs(dy);
                            if (overlapX < overlapY) {
                                player.x += (dx > 0 ? overlapX : -overlapX) * 1.2;
                                player.vx *= -0.3;
                            } else {
                                player.y += (dy > 0 ? overlapY : -overlapY) * 1.2;
                                player.vy *= -0.3;
                            }
                        }
                    }
                });
            }

            // ---------- CẬP NHẬT HIỆU ỨNG (KHÓI, LỬA, PARTICLE) ----------
            function updateEffects() {
                // Smoke
                player.smokeParticles = player.smokeParticles.filter(p => {
                    p.x += p.vx;
                    p.y += p.vy;
                    p.life -= 0.01;
                    p.size *= 0.99;
                    return p.life > 0;
                });
                // Fire
                player.fireParticles = player.fireParticles.filter(p => {
                    p.x += p.vx;
                    p.y += p.vy;
                    p.life -= 0.02;
                    p.size *= 0.98;
                    return p.life > 0;
                });
                // Crash particles
                for (let i = particles.length - 1; i >= 0; i--) {
                    const p = particles[i];
                    p.x += p.vx;
                    p.y += p.vy;
                    p.vy += 0.1; // gravity
                    p.life -= 0.01;
                    if (p.life <= 0) {
                        particles.splice(i, 1);
                    }
                }
            }

            // ---------- CAMERA FOLLOW ----------
            function updateCamera() {
                world.camera.x = player.x - canvas.width/2;
                world.camera.y = player.y - canvas.height/2;
                
                // Không để camera lộ ra ngoài thế giới
                world.camera.x = Math.max(0, Math.min(world.width - canvas.width, world.camera.x));
                world.camera.y = Math.max(0, Math.min(world.height - canvas.height, world.camera.y));
            }

            // ---------- VẼ ----------
            function draw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Hàm chuyển tọa độ thế giới sang màn hình
                function toScreenX(wx) { return wx - world.camera.x; }
                function toScreenY(wy) { return wy - world.camera.y; }

                // Vẽ nền (màu đất)
                ctx.fillStyle = '#2a3a2a';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Vẽ đường lưới (ô vuông)
                ctx.strokeStyle = '#4a5a4a';
                ctx.lineWidth = 1;
                const gridSize = 100;
                const startX = Math.floor(world.camera.x / gridSize) * gridSize;
                const startY = Math.floor(world.camera.y / gridSize) * gridSize;
                for (let x = startX; x < world.camera.x + canvas.width; x += gridSize) {
                    ctx.beginPath();
                    ctx.moveTo(toScreenX(x), 0);
                    ctx.lineTo(toScreenX(x), canvas.height);
                    ctx.strokeStyle = '#3a4a3a';
                    ctx.stroke();
                }
                for (let y = startY; y < world.camera.y + canvas.height; y += gridSize) {
                    ctx.beginPath();
                    ctx.moveTo(0, toScreenY(y));
                    ctx.lineTo(canvas.width, toScreenY(y));
                    ctx.strokeStyle = '#3a4a3a';
                    ctx.stroke();
                }

                // Vẽ vật cản
                obstacles.forEach(obs => {
                    const sx = toScreenX(obs.x - obs.w/2);
                    const sy = toScreenY(obs.y - obs.h/2);
                    ctx.fillStyle = obs.color || '#8B5A2B';
                    ctx.fillRect(sx, sy, obs.w, obs.h);
                    // Viền
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(sx, sy, obs.w, obs.h);
                });

                // Vẽ xe AI
                aiCars.forEach(ai => {
                    const sx = toScreenX(ai.x);
                    const sy = toScreenY(ai.y);
                    ctx.save();
                    ctx.translate(sx, sy);
                    ctx.rotate(ai.angle);
                    // Thân xe
                    ctx.fillStyle = ai.color;
                    ctx.fillRect(-ai.width/2, -ai.height/2, ai.width, ai.height);
                    // Kính
                    ctx.fillStyle = '#aaccff';
                    ctx.fillRect(-ai.width/3, -ai.height/2 + 5, ai.width*2/3, 10);
                    // Viền
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(-ai.width/2, -ai.height/2, ai.width, ai.height);
                    ctx.restore();
                });

                // Vẽ xe player (có các bộ phận riêng)
                const psx = toScreenX(player.x);
                const psy = toScreenY(player.y);
                ctx.save();
                ctx.translate(psx, psy);
                ctx.rotate(player.angle);
                
                // Thân xe chính
                ctx.fillStyle = '#2277cc';
                ctx.fillRect(-player.width/2, -player.height/2, player.width, player.height);
                
                // Vẽ cửa nếu còn
                if (player.parts.doorL.health > 0) {
                    ctx.fillStyle = '#44aaff';
                    ctx.fillRect(-player.width/2, -player.height/4, 5, player.height/2);
                }
                if (player.parts.doorR.health > 0) {
                    ctx.fillStyle = '#44aaff';
                    ctx.fillRect(player.width/2 - 5, -player.height/4, 5, player.height/2);
                }
                
                // Vẽ bánh xe
                ctx.fillStyle = '#333';
                ctx.fillRect(-player.width/2 - 3, -player.height/3, 6, 15); // bánh trái trước
                ctx.fillRect(player.width/2 - 3, -player.height/3, 6, 15); // bánh phải trước
                ctx.fillRect(-player.width/2 - 3, player.height/3 - 10, 6, 15); // bánh trái sau
                ctx.fillRect(player.width/2 - 3, player.height/3 - 10, 6, 15); // bánh phải sau
                
                // Viền xe
                ctx.strokeStyle = '#ffaa00';
                ctx.lineWidth = 3;
                ctx.strokeRect(-player.width/2, -player.height/2, player.width, player.height);
                
                ctx.restore();

                // Vẽ khói và lửa
                player.smokeParticles.forEach(p => {
                    const sx = toScreenX(p.x);
                    const sy = toScreenY(p.y);
                    ctx.globalAlpha = p.life;
                    ctx.fillStyle = p.color;
                    ctx.beginPath();
                    ctx.arc(sx, sy, p.size/2, 0, Math.PI*2);
                    ctx.fill();
                });
                player.fireParticles.forEach(p => {
                    const sx = toScreenX(p.x);
                    const sy = toScreenY(p.y);
                    ctx.globalAlpha = p.life;
                    ctx.fillStyle = p.color;
                    ctx.fillRect(sx - p.size/2, sy - p.size/2, p.size, p.size);
                });
                ctx.globalAlpha = 1.0;

                // Vẽ các mảnh vỡ
                particles.forEach(p => {
                    const sx = toScreenX(p.x);
                    const sy = toScreenY(p.y);
                    ctx.globalAlpha = p.life;
                    ctx.fillStyle = p.color;
                    ctx.fillRect(sx - p.size/2, sy - p.size/2, p.size, p.size);
                });
                ctx.globalAlpha = 1.0;
            }

            // ---------- CẬP NHẬT UI ----------
            function updateUI() {
                document.getElementById('score').innerText = Math.floor(score);
                document.getElementById('crashes').innerText = totalCrashes;
                const speedKmh = Math.floor(Math.hypot(player.vx, player.vy) * 15);
                document.getElementById('speed').innerText = speedKmh;
                
                // Các thanh trạng thái
                document.getElementById('engine-fill').style.width = player.parts.engine.health + '%';
                document.getElementById('doorL-fill').style.width = player.parts.doorL.health + '%';
                document.getElementById('doorR-fill').style.width = player.parts.doorR.health + '%';
                document.getElementById('wheelL-fill').style.width = player.parts.wheelL.health + '%';
                document.getElementById('wheelR-fill').style.width = player.parts.wheelR.health + '%';
            }

            // ---------- KIỂM TRA GAME OVER ----------
            function checkGameOver() {
                // Xe hỏng hoàn toàn khi động cơ = 0 và ít nhất 2 bánh = 0
                const wheelsDead = (player.parts.wheelL.health <= 0 ? 1 : 0) + (player.parts.wheelR.health <= 0 ? 1 : 0);
                if (player.parts.engine.health <= 0 && wheelsDead >= 1) {
                    gameRunning = false;
                    document.getElementById('final-score').innerText = Math.floor(score);
                    document.getElementById('final-crashes').innerText = totalCrashes;
                    document.getElementById('game-over').style.display = 'flex';
                }
            }

            // ---------- GAME LOOP ----------
            let lastTime = 0;
            function gameLoop(now) {
                if (!gameRunning) return;
                
                const dt = Math.min(0.05, (now - lastTime) / 1000);
                lastTime = now;

                // Cập nhật
                updatePlayer();
                updateAI();
                checkCollisions();
                updateEffects();
                updateCamera();
                
                // Vẽ
                draw();
                
                // UI
                updateUI();
                checkGameOver();

                requestAnimationFrame(gameLoop);
            }
            
            // Bắt đầu game loop
            lastTime = performance.now();
            requestAnimationFrame(gameLoop);
        })();
    </script>
</body>
</html>
"""

st.components.v1.html(game_html, height=1000, scrolling=False)
