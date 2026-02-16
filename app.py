import streamlit as st

st.set_page_config(page_title="Soft‑Body Pixel Car Crash", layout="wide", initial_sidebar_state="collapsed")

# Ẩn giao diện Streamlit
st.markdown("""
<style>
    #MainMenu, footer, header {display: none;}
    .stApp {background: black; padding: 0; margin: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# Toàn bộ game HTML (đã bao gồm JavaScript cải tiến)
GAME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Soft‑Body Pixel Car Crash</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; user-select: none; -webkit-tap-highlight-color: transparent; }
        body { background: black; overflow: hidden; touch-action: none; }
        #gameCanvas {
            display: block;
            width: 100vw;
            height: 100vh;
            background: #1a2c2c;
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
        <div style="font-size: 18px; font-weight: bold; color: #4fc3f7;">💥 SOFT‑BODY CRASH</div>
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

            // ==================== SOFT‑BODY XE (CẢI TIẾN) ====================
            class SoftCar {
                constructor(x, y, color) {
                    this.x = x; this.y = y;
                    this.color = color;
                    this.points = [];
                    this.springs = [];
                    
                    // Tạo lưới 5x4 điểm
                    const cols = 5, rows = 4;
                    const w = 60, h = 40;
                    for (let row = 0; row < rows; row++) {
                        for (let col = 0; col < cols; col++) {
                            this.points.push({
                                x: (col / (cols-1) - 0.5) * w,
                                y: (row / (rows-1) - 0.5) * h,
                                px: 0, py: 0, // vị trí cũ cho Verlet
                                vx: 0, vy: 0,
                                mass: 1,
                            });
                        }
                    }
                    
                    // Khởi tạo vị trí cũ bằng vị trí hiện tại
                    for (let p of this.points) {
                        p.px = p.x;
                        p.py = p.y;
                    }
                    
                    // Tạo lò xo với độ cứng cao và damping
                    const strength = 1.5;  // tăng độ cứng để giữ hình dạng
                    const damping = 0.3;
                    
                    // Lò xo dọc và ngang
                    for (let row = 0; row < rows; row++) {
                        for (let col = 0; col < cols; col++) {
                            const idx = row * cols + col;
                            if (col < cols-1) {
                                const idx2 = row * cols + (col+1);
                                this.addSpring(idx, idx2, strength, damping);
                            }
                            if (row < rows-1) {
                                const idx2 = (row+1) * cols + col;
                                this.addSpring(idx, idx2, strength, damping);
                            }
                        }
                    }
                    // Lò xo chéo (tăng độ cứng tổng thể)
                    for (let row = 0; row < rows-1; row++) {
                        for (let col = 0; col < cols-1; col++) {
                            const idx = row * cols + col;
                            const idx2 = (row+1) * cols + (col+1);
                            this.addSpring(idx, idx2, strength*0.7, damping);
                        }
                    }
                    
                    // Đánh dấu bánh xe (các góc)
                    this.wheelIndices = [0, cols-1, (rows-1)*cols, rows*cols-1];
                    
                    // Trạng thái hư hỏng
                    this.damage = {
                        engine: 100,
                        doorL: 100,
                        doorR: 100,
                        wheelL: 100,
                        wheelR: 100
                    };
                    
                    // Khói
                    this.smoke = [];
                }
                
                addSpring(i, j, strength, damping) {
                    const p1 = this.points[i];
                    const p2 = this.points[j];
                    const dx = p1.x - p2.x;
                    const dy = p1.y - p2.y;
                    const restLength = Math.hypot(dx, dy);
                    this.springs.push({ i, j, restLength, strength, damping });
                }
                
                // Verlet integration
                verlet(dt) {
                    for (let p of this.points) {
                        const vx = p.x - p.px;
                        const vy = p.y - p.py;
                        p.px = p.x;
                        p.py = p.y;
                        p.x += vx + p.vx * dt;
                        p.y += vy + p.vy * dt;
                        // reset lực
                        p.vx = 0;
                        p.vy = 0;
                    }
                }
                
                // Tính lực lò xo
                applySpringForces() {
                    for (let s of this.springs) {
                        const p1 = this.points[s.i];
                        const p2 = this.points[s.j];
                        const dx = p2.x - p1.x;
                        const dy = p2.y - p1.y;
                        const dist = Math.hypot(dx, dy);
                        if (dist === 0) continue;
                        const force = (dist - s.restLength) * s.strength;
                        const nx = dx / dist;
                        const ny = dy / dist;
                        
                        // Lực tác dụng lên vận tốc (Verlet sẽ dùng để cập nhật vị trí)
                        p1.vx += nx * force * 0.5;
                        p1.vy += ny * force * 0.5;
                        p2.vx -= nx * force * 0.5;
                        p2.vy -= ny * force * 0.5;
                        
                        // Damping (lực cản nhớt)
                        const vdx = p2.vx - p1.vx;
                        const vdy = p2.vy - p1.vy;
                        p1.vx += vdx * s.damping;
                        p1.vy += vdy * s.damping;
                        p2.vx -= vdx * s.damping;
                        p2.vy -= vdy * s.damping;
                    }
                }
                
                // Cập nhật tổng thể
                update(dt) {
                    this.applySpringForces();
                    this.verlet(dt);
                    
                    // Giới hạn trong thế giới (phản xạ)
                    for (let p of this.points) {
                        if (p.x < 0) { p.x = 0; p.px = p.x + (p.x - p.px)*0.5; }
                        if (p.x > world.width) { p.x = world.width; p.px = p.x + (p.x - p.px)*0.5; }
                        if (p.y < 0) { p.y = 0; p.py = p.y + (p.y - p.py)*0.5; }
                        if (p.y > world.height) { p.y = world.height; p.py = p.y + (p.y - p.py)*0.5; }
                    }
                    
                    // Tính tâm xe (để camera)
                    this.x = 0; this.y = 0;
                    for (let p of this.points) {
                        this.x += p.x;
                        this.y += p.y;
                    }
                    this.x /= this.points.length;
                    this.y /= this.points.length;
                    
                    // Tính hư hỏng dựa trên độ biến dạng của các lò xo (đơn giản)
                    let engineStress = 0;
                    for (let s of this.springs) {
                        const p1 = this.points[s.i];
                        const p2 = this.points[s.j];
                        const dx = p2.x - p1.x;
                        const dy = p2.y - p1.y;
                        const dist = Math.hypot(dx, dy);
                        const stretch = Math.abs(dist - s.restLength) / s.restLength;
                        engineStress += stretch;
                    }
                    engineStress /= this.springs.length;
                    
                    // Giảm máu động cơ nhẹ nhàng
                    this.damage.engine = Math.max(0, this.damage.engine - engineStress * 0.5);
                    
                    // Tạo khói nếu động cơ yếu
                    if (this.damage.engine < 40 && Math.random() < 0.1) {
                        this.smoke.push({
                            x: this.x + (Math.random()-0.5)*30,
                            y: this.y + (Math.random()-0.5)*30,
                            vx: (Math.random()-0.5)*0.5,
                            vy: -Math.random()*1,
                            life: 1.0,
                            size: 5+Math.random()*8
                        });
                    }
                    // Lọc khói
                    this.smoke = this.smoke.filter(p => {
                        p.x += p.vx;
                        p.y += p.vy;
                        p.life -= 0.01;
                        return p.life > 0;
                    });
                }
                
                // Vẽ bằng pixel (mỗi điểm là một pixel vuông)
                draw(ctx, offX, offY) {
                    const cellSize = 3; // kích thước mỗi pixel (phóng to để dễ thấy)
                    for (let p of this.points) {
                        ctx.fillStyle = this.color;
                        ctx.fillRect(offX + p.x - cellSize/2, offY + p.y - cellSize/2, cellSize, cellSize);
                    }
                    // Vẽ bánh xe (các góc)
                    ctx.fillStyle = '#222';
                    for (let idx of this.wheelIndices) {
                        const p = this.points[idx];
                        ctx.beginPath();
                        ctx.arc(offX + p.x, offY + p.y, 4, 0, 2*Math.PI);
                        ctx.fill();
                    }
                    // Vẽ khói
                    ctx.globalAlpha = 0.5;
                    for (let p of this.smoke) {
                        ctx.fillStyle = '#888';
                        ctx.beginPath();
                        ctx.arc(offX + p.x, offY + p.y, p.size * p.life, 0, 2*Math.PI);
                        ctx.fill();
                    }
                    ctx.globalAlpha = 1.0;
                }
                
                // Điều khiển: tác động lực lên các điểm phía sau
                applyControl(direction, strength) {
                    const cols = 5, rows = 4;
                    // direction: 0=tiến, 1=lùi, 2=trái, 3=phải
                    if (direction === 0) { // tiến
                        for (let col = 1; col < cols-1; col++) {
                            const idx = (rows-1) * cols + col; // hàng sau
                            const p = this.points[idx];
                            p.vx += Math.sin(this.angle) * strength;
                            p.vy += Math.cos(this.angle) * strength;
                        }
                    } else if (direction === 1) { // lùi
                        for (let col = 1; col < cols-1; col++) {
                            const idx = (rows-1) * cols + col;
                            const p = this.points[idx];
                            p.vx -= Math.sin(this.angle) * strength * 0.6;
                            p.vy -= Math.cos(this.angle) * strength * 0.6;
                        }
                    } else if (direction === 2) { // trái
                        for (let row = 0; row < rows; row++) {
                            const idx = row * cols; // cột trái
                            const p = this.points[idx];
                            p.vx -= strength * 2;
                        }
                    } else if (direction === 3) { // phải
                        for (let row = 0; row < rows; row++) {
                            const idx = row * cols + (cols-1); // cột phải
                            const p = this.points[idx];
                            p.vx += strength * 2;
                        }
                    }
                }
                
                // Phanh tay: tăng ma sát các điểm bánh
                handbrake() {
                    for (let idx of this.wheelIndices) {
                        const p = this.points[idx];
                        p.vx *= 0.7;
                        p.vy *= 0.7;
                    }
                }
            }

            // Tạo xe người chơi
            const player = new SoftCar(1500, 1500, '#2277cc');
            // Góc quay ban đầu (tính từ vận tốc, nhưng soft-body không có góc cố định)
            player.angle = 0; // thêm thuộc tính để điều khiển
            
            // Tạo xe AI (cũng dùng soft-body nhưng số lượng ít để giữ hiệu suất)
            const aiCars = [];
            for (let i = 0; i < 3; i++) {
                aiCars.push(new SoftCar(1000+Math.random()*1000, 1000+Math.random()*1000, '#cc4444'));
            }

            // ---------- VẬT CẢN ----------
            const obstacles = [];
            // Tường
            obstacles.push({ x: world.width/2, y: -25, w: world.width, h: 50 });
            obstacles.push({ x: world.width/2, y: world.height+25, w: world.width, h: 50 });
            obstacles.push({ x: -25, y: world.height/2, w: 50, h: world.height });
            obstacles.push({ x: world.width+25, y: world.height/2, w: 50, h: world.height });
            // Cây cối, nhà
            for (let i = 0; i < 20; i++) {
                obstacles.push({
                    x: 200+Math.random()*2600,
                    y: 200+Math.random()*2600,
                    w: 30+Math.random()*30,
                    h: 30+Math.random()*30,
                    color: `rgb(${30+Math.random()*50},${50+Math.random()*50},${20})`
                });
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
                // Mouse events for testing on PC
                btn.addEventListener('mousedown', (e) => { e.preventDefault(); keys[key] = true; });
                btn.addEventListener('mouseup', (e) => { e.preventDefault(); keys[key] = false; });
                btn.addEventListener('mouseleave', (e) => { keys[key] = false; });
            });

            // ---------- GAME STATE ----------
            let score = 0;
            let totalCrashes = 0;
            let gameRunning = true;

            // ---------- VA CHẠM (CHỈ TÍNH KHI VẬN TỐC ĐỦ LỚN) ----------
            function handleCollisions() {
                const threshold = 1.5; // ngưỡng vận tốc tương đối để tính va chạm
                
                // Player vs AI cars
                for (let ai of aiCars) {
                    for (let pi of player.points) {
                        for (let pj of ai.points) {
                            const dx = pi.x - pj.x;
                            const dy = pi.y - pj.y;
                            const dist = Math.hypot(dx, dy);
                            if (dist < 10) { // khoảng cách va chạm
                                // Tính vận tốc tương đối
                                const vRelX = pi.vx - pj.vx;
                                const vRelY = pi.vy - pj.vy;
                                const vRel = Math.hypot(vRelX, vRelY);
                                
                                if (vRel > threshold) {
                                    // Tạo phản lực
                                    const nx = dx / (dist || 1);
                                    const ny = dy / (dist || 1);
                                    const force = vRel * 0.8;
                                    pi.vx += nx * force;
                                    pi.vy += ny * force;
                                    pj.vx -= nx * force;
                                    pj.vy -= ny * force;
                                    
                                    totalCrashes++;
                                    score += Math.floor(vRel * 10);
                                    
                                    // Làm hỏng động cơ (tạm thời)
                                    player.damage.engine = Math.max(0, player.damage.engine - vRel * 2);
                                }
                            }
                        }
                    }
                }
                
                // Player vs obstacles (hình chữ nhật)
                for (let obs of obstacles) {
                    for (let p of player.points) {
                        if (p.x > obs.x - obs.w/2 && p.x < obs.x + obs.w/2 &&
                            p.y > obs.y - obs.h/2 && p.y < obs.y + obs.h/2) {
                            
                            const speed = Math.hypot(p.vx, p.vy);
                            if (speed > threshold) {
                                // Đẩy điểm ra khỏi vật cản
                                const left = p.x - (obs.x - obs.w/2);
                                const right = (obs.x + obs.w/2) - p.x;
                                const top = p.y - (obs.y - obs.h/2);
                                const bottom = (obs.y + obs.h/2) - p.y;
                                
                                const minX = Math.min(left, right);
                                const minY = Math.min(top, bottom);
                                
                                if (minX < minY) {
                                    if (left < right) {
                                        p.x = obs.x - obs.w/2 - 2;
                                        p.vx = -Math.abs(p.vx) * 0.3;
                                    } else {
                                        p.x = obs.x + obs.w/2 + 2;
                                        p.vx = Math.abs(p.vx) * 0.3;
                                    }
                                } else {
                                    if (top < bottom) {
                                        p.y = obs.y - obs.h/2 - 2;
                                        p.vy = -Math.abs(p.vy) * 0.3;
                                    } else {
                                        p.y = obs.y + obs.h/2 + 2;
                                        p.vy = Math.abs(p.vy) * 0.3;
                                    }
                                }
                                
                                totalCrashes++;
                                score += Math.floor(speed * 5);
                                player.damage.engine = Math.max(0, player.damage.engine - speed * 1.5);
                            }
                        }
                    }
                }
            }

            // ---------- CẬP NHẬT GÓC XE (cho điều khiển) ----------
            function updatePlayerAngle() {
                // Tính góc từ vận tốc trung bình của các điểm
                let avgVx = 0, avgVy = 0;
                for (let p of player.points) {
                    avgVx += p.vx;
                    avgVy += p.vy;
                }
                avgVx /= player.points.length;
                avgVy /= player.points.length;
                if (Math.hypot(avgVx, avgVy) > 0.1) {
                    player.angle = Math.atan2(avgVx, avgVy);
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
                
                const offX = -world.camera.x;
                const offY = -world.camera.y;
                
                // Nền
                ctx.fillStyle = '#1a2c2c';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Lưới đường
                ctx.strokeStyle = '#3a5a5a';
                ctx.lineWidth = 1;
                const grid = 100;
                const startX = Math.floor(world.camera.x / grid) * grid;
                const startY = Math.floor(world.camera.y / grid) * grid;
                for (let x = startX; x < world.camera.x + canvas.width; x += grid) {
                    ctx.beginPath();
                    ctx.moveTo(x - world.camera.x, 0);
                    ctx.lineTo(x - world.camera.x, canvas.height);
                    ctx.stroke();
                }
                for (let y = startY; y < world.camera.y + canvas.height; y += grid) {
                    ctx.beginPath();
                    ctx.moveTo(0, y - world.camera.y);
                    ctx.lineTo(canvas.width, y - world.camera.y);
                    ctx.stroke();
                }
                
                // Vẽ vật cản
                for (let obs of obstacles) {
                    ctx.fillStyle = obs.color || '#6b4e3a';
                    ctx.fillRect(obs.x - obs.w/2 - world.camera.x, obs.y - obs.h/2 - world.camera.y, obs.w, obs.h);
                }
                
                // Vẽ xe AI
                for (let ai of aiCars) {
                    ai.draw(ctx, offX, offY);
                }
                
                // Vẽ xe player
                player.draw(ctx, offX, offY);
            }

            // ---------- CẬP NHẬT UI ----------
            function updateUI() {
                document.getElementById('score').innerText = Math.floor(score);
                document.getElementById('crashes').innerText = totalCrashes;
                // Tính tốc độ trung bình
                let sp = 0;
                for (let p of player.points) sp += Math.hypot(p.vx, p.vy);
                sp = (sp / player.points.length) * 20;
                document.getElementById('speed').innerText = Math.floor(sp);
                
                document.getElementById('engine-health').style.width = player.damage.engine + '%';
                document.getElementById('doorL-health').style.width = player.damage.doorL + '%';
                document.getElementById('doorR-health').style.width = player.damage.doorR + '%';
                document.getElementById('wheelL-health').style.width = player.damage.wheelL + '%';
                document.getElementById('wheelR-health').style.width = player.damage.wheelR + '%';
            }

            // ---------- GAME LOOP ----------
            let lastTime = 0;
            function gameLoop(now) {
                if (!gameRunning) return;
                
                const dt = Math.min(0.05, (now - lastTime) / 1000);
                lastTime = now;
                
                // Điều khiển (tác động lực lên các điểm)
                const force = 0.8;
                if (keys.up) player.applyControl(0, force);
                if (keys.down) player.applyControl(1, force);
                if (keys.left) player.applyControl(2, force);
                if (keys.right) player.applyControl(3, force);
                if (keys.space) player.handbrake();
                
                // Cập nhật góc xe để điều khiển hướng
                updatePlayerAngle();
                
                // Cập nhật vật lý cho player
                player.update(dt);
                
                // Cập nhật vật lý cho AI (đơn giản)
                for (let ai of aiCars) {
                    // AI di chuyển ngẫu nhiên nhẹ
                    if (Math.random() < 0.01) {
                        ai.applyControl(Math.floor(Math.random()*2), 0.5);
                    }
                    ai.update(dt);
                }
                
                // Va chạm
                handleCollisions();
                
                // Camera
                updateCamera();
                
                // Vẽ
                draw();
                updateUI();
                
                // Game over
                if (player.damage.engine <= 0) {
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

st.components.v1.html(GAME_HTML, height=1000, scrolling=False)
