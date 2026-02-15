import streamlit as st

st.set_page_config(page_title="2D Pixel Car Crash - Deform", layout="wide", initial_sidebar_state="collapsed")

# Ẩn giao diện Streamlit
st.markdown("""
<style>
    #MainMenu, footer, header {display: none;}
    .stApp {background: black; padding: 0; margin: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>2D Deformable Pixel Car Crash</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; -webkit-tap-highlight-color: transparent; }
        body { background: black; overflow: hidden; touch-action: none; }
        #gameCanvas {
            display: block;
            width: 100vw;
            height: 100vh;
            background: #1a2a2a;
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
        #mobile-controls {
            position: absolute;
            bottom: 30px;
            left: 0;
            width: 100%;
            display: none;  /* ẩn trên PC, hiện trên mobile */
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
            transition: 0.1s;
            font-weight: bold;
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
        <div style="font-size: 18px; font-weight: bold; color: #4fc3f7;">💥 PIXEL CRASH</div>
        <div>🏆 ĐIỂM: <span id="score">0</span></div>
        <div>💥 VA CHẠM: <span id="crashes">0</span></div>
        <div id="speedometer">⚡ <span id="speed">0</span> km/h</div>
        <div>🛞 ĐỘNG CƠ: <span id="engine">100%</span></div>
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
                width: 3000,
                height: 3000,
                camera: { x: 0, y: 0 }
            };

            // ---------- HÌNH DẠNG XE (PIXEL) ----------
            // Xe được định nghĩa bởi một mảng 2D các pixel (màu sắc).
            // Khi va chạm, các pixel tại vùng va chạm sẽ bị xóa (chuyển thành trong suốt) hoặc chuyển màu tối.
            const CAR_WIDTH = 30;   // pixel
            const CAR_HEIGHT = 50;
            
            // Tạo hình dạng xe ban đầu (màu sắc)
            function createCarShape() {
                const shape = [];
                for (let row = 0; row < CAR_HEIGHT; row++) {
                    const line = [];
                    for (let col = 0; col < CAR_WIDTH; col++) {
                        // Xác định màu dựa trên vị trí (tạo hình xe đơn giản)
                        let color = '#2277cc'; // thân chính
                        
                        // Động cơ (mũi xe) phía trên
                        if (row < 10) {
                            if (col > 8 && col < 22) color = '#44aaff'; // kính chắn gió
                            else color = '#115599'; // nắp capo
                        }
                        // Cửa sổ
                        if (row > 12 && row < 25 && col > 5 && col < 25) {
                            if (col > 10 && col < 20 && row > 15 && row < 22) color = '#aaddff'; // kính cửa
                            else color = '#3366aa';
                        }
                        // Bánh xe (màu đen)
                        if ((row < 8 || row > 42) && (col < 8 || col > 22)) color = '#222222';
                        // Đèn trước
                        if (row < 5 && (col < 5 || col > 25)) color = '#ffffaa';
                        // Đèn sau
                        if (row > 45 && (col < 5 || col > 25)) color = '#ff5555';
                        
                        line.push(color);
                    }
                    shape.push(line);
                }
                return shape;
            }

            // Xe người chơi
            const player = {
                x: 1500, y: 1500,
                vx: 0, vy: 0,
                angle: 0,
                width: CAR_WIDTH,
                height: CAR_HEIGHT,
                shape: createCarShape(),  // ma trận màu (pixel)
                health: 100,
                engineHealth: 100,
                // Các thông số vật lý
                maxSpeed: 5,
                acceleration: 0.2,
                turnSpeed: 0.03,
                friction: 0.98
            };

            // ---------- XE AI ----------
            const aiCars = [];
            function createAICar(x, y) {
                return {
                    x: x, y: y,
                    vx: 0, vy: 0,
                    angle: Math.random() * Math.PI * 2,
                    width: CAR_WIDTH,
                    height: CAR_HEIGHT,
                    shape: createCarShape(), // mỗi AI có hình dạng riêng (có thể random màu)
                    color: `hsl(${Math.random()*360}, 70%, 50%)`,
                    maxSpeed: 2 + Math.random() * 2,
                    turnSpeed: 0.02,
                    targetX: x + (Math.random()-0.5)*500,
                    targetY: y + (Math.random()-0.5)*500,
                    aiTimer: 0
                };
            }
            for (let i = 0; i < 6; i++) {
                aiCars.push(createAICar(500+Math.random()*2000, 500+Math.random()*2000));
            }

            // ---------- VẬT CẢN ----------
            const obstacles = [];
            // Tường
            obstacles.push({ x: world.width/2, y: -25, w: world.width, h: 50, type: 'wall', color: '#555' });
            obstacles.push({ x: world.width/2, y: world.height+25, w: world.width, h: 50, color: '#555' });
            obstacles.push({ x: -25, y: world.height/2, w: 50, h: world.height, color: '#555' });
            obstacles.push({ x: world.width+25, y: world.height/2, w: 50, h: world.height, color: '#555' });
            // Cây, nhà
            for (let i = 0; i < 30; i++) {
                obstacles.push({
                    x: 100 + Math.random() * 2800,
                    y: 100 + Math.random() * 2800,
                    w: 30 + Math.random()*30,
                    h: 30 + Math.random()*30,
                    color: `rgb(${30+Math.random()*50},${50+Math.random()*80},${20})`
                });
            }

            // ---------- HỆ THỐNG PIXEL VỠ (CRASH) ----------
            const particles = [];
            function createCrashParticles(x, y, color, count) {
                for (let i = 0; i < count; i++) {
                    particles.push({
                        x: x + (Math.random()-0.5)*20,
                        y: y + (Math.random()-0.5)*20,
                        vx: (Math.random()-0.5)*5,
                        vy: (Math.random()-0.5)*5,
                        size: 2 + Math.random()*4,
                        color: color,
                        life: 1.0
                    });
                }
            }

            // ---------- HÀM XÓA PIXEL TRÊN XE (LÕM) ----------
            // Tại vị trí va chạm (world coordinates), xóa một vùng pixel trên shape của xe.
            function deformCar(car, worldX, worldY, intensity) {
                // Chuyển world coordinates về tọa độ xe (có tính góc)
                const dx = worldX - car.x;
                const dy = worldY - car.y;
                // Xoay ngược
                const cos = Math.cos(-car.angle);
                const sin = Math.sin(-car.angle);
                const localX = dx * cos - dy * sin;
                const localY = dx * sin + dy * cos;
                
                // Tọa độ trong shape (gốc tại tâm xe)
                const shapeX = Math.floor(localX + car.width/2);
                const shapeY = Math.floor(localY + car.height/2);
                
                // Bán kính vùng xóa tỷ lệ với intensity
                const radius = Math.max(2, Math.floor(intensity / 2));
                
                for (let dy = -radius; dy <= radius; dy++) {
                    for (let dx = -radius; dx <= radius; dx++) {
                        const ny = shapeY + dy;
                        const nx = shapeX + dx;
                        if (nx >= 0 && nx < car.width && ny >= 0 && ny < car.height) {
                            // Khoảng cách từ tâm
                            const dist = Math.hypot(dx, dy);
                            if (dist <= radius) {
                                // Xóa pixel (chuyển thành màu đen trong suốt? nhưng ta cần lõm -> vẽ màu nền?)
                                // Ở đây ta đặt màu thành màu nền tối (mô phỏng lõm)
                                car.shape[ny][nx] = '#331111'; // màu tối
                            }
                        }
                    }
                }
            }

            // ---------- ĐIỀU KHIỂN ----------
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

            // Mobile touch controls
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
                // Mouse events for testing on PC
                btn.addEventListener('mousedown', (e) => { e.preventDefault(); keys[key] = true; });
                btn.addEventListener('mouseup', (e) => { e.preventDefault(); keys[key] = false; });
                btn.addEventListener('mouseleave', (e) => { keys[key] = false; });
            });

            // ---------- GAME STATE ----------
            let score = 0;
            let totalCrashes = 0;
            let gameRunning = true;

            // ---------- VẬT LÝ PLAYER ----------
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

                // Giới hạn tốc độ
                let speed = Math.hypot(player.vx, player.vy);
                if (speed > player.maxSpeed) {
                    player.vx = (player.vx / speed) * player.maxSpeed;
                    player.vy = (player.vy / speed) * player.maxSpeed;
                }

                // Ma sát
                player.vx *= player.friction;
                player.vy *= player.friction;

                // Cập nhật vị trí
                player.x += player.vx;
                player.y += player.vy;

                // Giới hạn map
                player.x = Math.max(30, Math.min(world.width - 30, player.x));
                player.y = Math.max(30, Math.min(world.height - 30, player.y));

                // Giảm dần máu động cơ theo thời gian nếu nặng?
                // (có thể bỏ qua)
            }

            // ---------- AI ĐƠN GIẢN ----------
            function updateAI() {
                aiCars.forEach(ai => {
                    ai.aiTimer += 0.01;
                    if (ai.aiTimer > 3) {
                        ai.targetX = player.x + (Math.random()-0.5)*400;
                        ai.targetY = player.y + (Math.random()-0.5)*400;
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
                    ai.vx *= 0.98;
                    ai.vy *= 0.98;
                    // Giới hạn map
                    ai.x = Math.max(30, Math.min(world.width - 30, ai.x));
                    ai.y = Math.max(30, Math.min(world.height - 30, ai.y));
                });
            }

            // ---------- VA CHẠM ----------
            function checkCollisions() {
                // Player vs AI
                aiCars.forEach(ai => {
                    const dx = player.x - ai.x;
                    const dy = player.y - ai.y;
                    const dist = Math.hypot(dx, dy);
                    const minDist = (player.height/2 + ai.height/2) * 0.8;
                    if (dist < minDist) {
                        // Tính lực va chạm
                        const vRelX = player.vx - ai.vx;
                        const vRelY = player.vy - ai.vy;
                        const force = Math.hypot(vRelX, vRelY);
                        
                        if (force > 0.5) {
                            // Tạo pixel vỡ
                            createCrashParticles((player.x+ai.x)/2, (player.y+ai.y)/2, '#ffaa00', 15);
                            
                            // Làm lõm xe player tại điểm va chạm
                            const crashX = (player.x + ai.x)/2;
                            const crashY = (player.y + ai.y)/2;
                            deformCar(player, crashX, crashY, force * 5);
                            
                            // Gây damage (giảm máu động cơ)
                            player.engineHealth -= force * 2;
                            if (player.engineHealth < 0) player.engineHealth = 0;
                            
                            score += Math.floor(force * 5);
                            totalCrashes++;
                            
                            // Đẩy nhau
                            if (dist > 0) {
                                const normX = dx / dist;
                                const normY = dy / dist;
                                const overlap = minDist - dist;
                                player.x += normX * overlap * 0.5;
                                player.y += normY * overlap * 0.5;
                                ai.x -= normX * overlap * 0.5;
                                ai.y -= normY * overlap * 0.5;
                                
                                player.vx += normX * force * 0.3;
                                player.vy += normY * force * 0.3;
                                ai.vx -= normX * force * 0.3;
                                ai.vy -= normY * force * 0.3;
                            }
                        }
                    }
                });

                // Player vs obstacles
                obstacles.forEach(obs => {
                    const halfW = player.width/2;
                    const halfH = player.height/2;
                    const obsHalfW = obs.w/2;
                    const obsHalfH = obs.h/2;
                    
                    if (Math.abs(player.x - obs.x) < halfW + obsHalfW &&
                        Math.abs(player.y - obs.y) < halfH + obsHalfH) {
                        
                        const speed = Math.hypot(player.vx, player.vy);
                        if (speed > 0.2) {
                            createCrashParticles(player.x, player.y, obs.color || '#888', 10);
                            deformCar(player, player.x, player.y, speed * 8);
                            player.engineHealth -= speed * 3;
                            score += Math.floor(speed * 2);
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

            // ---------- CẬP NHẬT HIỆU ỨNG ----------
            function updateParticles() {
                for (let i = particles.length - 1; i >= 0; i--) {
                    const p = particles[i];
                    p.x += p.vx;
                    p.y += p.vy;
                    p.vy += 0.05; // gravity
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
                world.camera.x = Math.max(0, Math.min(world.width - canvas.width, world.camera.x));
                world.camera.y = Math.max(0, Math.min(world.height - canvas.height, world.camera.y));
            }

            // ---------- VẼ ----------
            function draw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                function toScreenX(wx) { return wx - world.camera.x; }
                function toScreenY(wy) { return wy - world.camera.y; }

                // Nền
                ctx.fillStyle = '#1a2a2a';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Vẽ lưới đường
                ctx.strokeStyle = '#3a4a3a';
                ctx.lineWidth = 1;
                const grid = 100;
                const startX = Math.floor(world.camera.x / grid) * grid;
                const startY = Math.floor(world.camera.y / grid) * grid;
                for (let x = startX; x < world.camera.x + canvas.width; x += grid) {
                    ctx.beginPath();
                    ctx.moveTo(toScreenX(x), 0);
                    ctx.lineTo(toScreenX(x), canvas.height);
                    ctx.strokeStyle = '#3a4a3a';
                    ctx.stroke();
                }
                for (let y = startY; y < world.camera.y + canvas.height; y += grid) {
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
                    ctx.strokeStyle = '#000';
                    ctx.strokeRect(sx, sy, obs.w, obs.h);
                });

                // Vẽ xe AI (dạng pixel đơn giản)
                aiCars.forEach(ai => {
                    const sx = toScreenX(ai.x - ai.width/2);
                    const sy = toScreenY(ai.y - ai.height/2);
                    // Vẽ từng pixel
                    for (let row = 0; row < ai.height; row++) {
                        for (let col = 0; col < ai.width; col++) {
                            const color = ai.shape[row][col];
                            ctx.fillStyle = color;
                            ctx.fillRect(sx + col, sy + row, 1, 1);
                        }
                    }
                });

                // Vẽ xe player (pixel)
                const psx = toScreenX(player.x - player.width/2);
                const psy = toScreenY(player.y - player.height/2);
                for (let row = 0; row < player.height; row++) {
                    for (let col = 0; col < player.width; col++) {
                        const color = player.shape[row][col];
                        ctx.fillStyle = color;
                        ctx.fillRect(psx + col, psy + row, 1, 1);
                    }
                }

                // Vẽ particles
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
                const speedKmh = Math.floor(Math.hypot(player.vx, player.vy) * 20);
                document.getElementById('speed').innerText = speedKmh;
                document.getElementById('engine').innerText = Math.floor(player.engineHealth) + '%';
            }

            // ---------- GAME LOOP ----------
            let lastTime = 0;
            function gameLoop(now) {
                if (!gameRunning) return;
                
                const dt = Math.min(0.05, (now - lastTime) / 1000);
                lastTime = now;

                updatePlayer();
                updateAI();
                checkCollisions();
                updateParticles();
                updateCamera();
                
                draw();
                updateUI();

                // Kiểm tra game over (động cơ hết máu)
                if (player.engineHealth <= 0) {
                    gameRunning = false;
                    alert('💥 GAME OVER! Điểm: ' + Math.floor(score));
                    location.reload();
                }

                requestAnimationFrame(gameLoop);
            }

            lastTime = performance.now();
            requestAnimationFrame(gameLoop);
        })();
    </script>
</body>
</html>
"""

st.components.v1.html(game_html, height=1000, scrolling=False)
