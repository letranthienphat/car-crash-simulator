import streamlit as st

st.set_page_config(page_title="Soft‑Body Pixel Car Crash", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    #MainMenu, footer, header {display: none;}
    .stApp {background: black; padding: 0; margin: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# Toàn bộ mã game (JavaScript + HTML) được nhúng dưới đây
GAME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Soft‑Body Pixel Crash</title>
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

            // ==================== SOFT‑BODY XE ====================
            // Xe được định nghĩa bởi 20 điểm (vertices) và các lò xo (springs)
            class SoftCar {
                constructor(x, y, color) {
                    this.x = x;
                    this.y = y;
                    this.color = color;
                    this.points = [];
                    this.springs = [];
                    this.angle = 0; // không dùng trực tiếp, do soft-body tự biến dạng
                    
                    // Khởi tạo các điểm – hình chữ nhật bo tròn (12 điểm ngoài + 8 điểm trong)
                    // Tạo lưới 5x4 điểm
                    const cols = 5;
                    const rows = 4;
                    const w = 60; // chiều rộng
                    const h = 40; // chiều cao
                    for (let row = 0; row < rows; row++) {
                        for (let col = 0; col < cols; col++) {
                            const px = (col / (cols-1) - 0.5) * w;
                            const py = (row / (rows-1) - 0.5) * h;
                            this.points.push({
                                x: px, y: py,
                                vx: 0, vy: 0,
                                mass: 1,
                                pinned: false
                            });
                        }
                    }
                    
                    // Tạo lò xo giữa các điểm kề nhau (theo hàng và cột)
                    for (let row = 0; row < rows; row++) {
                        for (let col = 0; col < cols; col++) {
                            const idx = row * cols + col;
                            // hàng ngang
                            if (col < cols-1) {
                                const idx2 = row * cols + (col+1);
                                this.addSpring(idx, idx2);
                            }
                            // hàng dọc
                            if (row < rows-1) {
                                const idx2 = (row+1) * cols + col;
                                this.addSpring(idx, idx2);
                            }
                            // đường chéo (tùy chọn, tăng độ cứng)
                            if (col < cols-1 && row < rows-1) {
                                const idx2 = (row+1) * cols + (col+1);
                                this.addSpring(idx, idx2, 0.5); // độ cứng thấp hơn
                            }
                            if (col > 0 && row < rows-1) {
                                const idx2 = (row+1) * cols + (col-1);
                                this.addSpring(idx, idx2, 0.5);
                            }
                        }
                    }
                    
                    // Đánh dấu các bánh xe (các góc) để xác định hư hỏng sau
                    this.wheelIndices = [0, cols-1, (rows-1)*cols, rows*cols-1];
                    this.doorIndices = [1, 2, cols+1, cols*2+1]; // ví dụ
                    this.engineIndices = [cols*2+2, cols*2+3]; // tạm
                    
                    // Lưu trạng thái hư hỏng
                    this.damage = {
                        engine: 100,
                        doorL: 100,
                        doorR: 100,
                        wheelL: 100,
                        wheelR: 100
                    };
                    
                    // Smoker
                    this.smokeParticles = [];
                }
                
                addSpring(i, j, strength = 1.0) {
                    const p1 = this.points[i];
                    const p2 = this.points[j];
                    const dx = p1.x - p2.x;
                    const dy = p1.y - p2.y;
                    const restLength = Math.hypot(dx, dy);
                    this.springs.push({
                        i, j,
                        restLength,
                        strength: 0.3 * strength, // độ cứng
                        damping: 0.1
                    });
                }
                
                // Áp dụng vật lý lò xo
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
                        
                        // Lực tác dụng lên hai điểm
                        const fx = nx * force;
                        const fy = ny * force;
                        if (!p1.pinned) {
                            p1.vx += fx * 0.5;
                            p1.vy += fy * 0.5;
                        }
                        if (!p2.pinned) {
                            p2.vx -= fx * 0.5;
                            p2.vy -= fy * 0.5;
                        }
                        
                        // Giảm chấn (damping)
                        const vdx = p2.vx - p1.vx;
                        const vdy = p2.vy - p1.vy;
                        const damping = s.damping;
                        if (!p1.pinned) {
                            p1.vx += vdx * damping;
                            p1.vy += vdy * damping;
                        }
                        if (!p2.pinned) {
                            p2.vx -= vdx * damping;
                            p2.vy -= vdy * damping;
                        }
                    }
                }
                
                // Cập nhật vị trí các điểm
                update(dt) {
                    // Lực lò xo
                    this.applySpringForces();
                    
                    // Trọng lực (có thể bỏ qua)
                    // for (let p of this.points) {
                    //     p.vy += 0.05;
                    // }
                    
                    // Ma sát không khí
                    for (let p of this.points) {
                        p.vx *= 0.99;
                        p.vy *= 0.99;
                    }
                    
                    // Di chuyển
                    for (let p of this.points) {
                        p.x += p.vx;
                        p.y += p.vy;
                    }
                    
                    // Giới hạn trong thế giới (để không bay ra ngoài)
                    for (let p of this.points) {
                        if (p.x < 0) { p.x = 0; p.vx *= -0.3; }
                        if (p.x > world.width) { p.x = world.width; p.vx *= -0.3; }
                        if (p.y < 0) { p.y = 0; p.vy *= -0.3; }
                        if (p.y > world.height) { p.y = world.height; p.vy *= -0.3; }
                    }
                    
                    // Cập nhật vị trí tổng thể (lấy trung bình)
                    this.x = 0; this.y = 0;
                    for (let p of this.points) {
                        this.x += p.x;
                        this.y += p.y;
                    }
                    this.x /= this.points.length;
                    this.y /= this.points.length;
                    
                    // Cập nhật damage dựa trên độ biến dạng của lò xo
                    let engineStress = 0, doorLStress = 0, doorRStress = 0, wheelLStress = 0, wheelRStress = 0;
                    for (let s of this.springs) {
                        const p1 = this.points[s.i];
                        const p2 = this.points[s.j];
                        const dx = p2.x - p1.x;
                        const dy = p2.y - p1.y;
                        const dist = Math.hypot(dx, dy);
                        const stretch = Math.abs(dist - s.restLength) / s.restLength;
                        // Nếu lò xo thuộc vùng nào đó thì tăng stress
                        if (this.engineIndices.includes(s.i) || this.engineIndices.includes(s.j)) {
                            engineStress += stretch;
                        }
                        if (this.doorIndices.includes(s.i) || this.doorIndices.includes(s.j)) {
                            doorLStress += stretch; // phân biệt trái/phải cần logic phức tạp hơn
                        }
                        if (this.wheelIndices.includes(s.i) || this.wheelIndices.includes(s.j)) {
                            wheelLStress += stretch;
                        }
                    }
                    // Giảm máu
                    this.damage.engine = Math.max(0, this.damage.engine - engineStress * 0.1);
                    this.damage.doorL = Math.max(0, this.damage.doorL - doorLStress * 0.05);
                    this.damage.doorR = Math.max(0, this.damage.doorR - doorLStress * 0.05);
                    this.damage.wheelL = Math.max(0, this.damage.wheelL - wheelLStress * 0.2);
                    this.damage.wheelR = Math.max(0, this.damage.wheelR - wheelLStress * 0.2);
                    
                    // Tạo khói nếu động cơ yếu
                    if (this.damage.engine < 40 && Math.random() < 0.1) {
                        this.smokeParticles.push({
                            x: this.x + (Math.random()-0.5)*20,
                            y: this.y + (Math.random()-0.5)*20,
                            vx: (Math.random()-0.5)*1,
                            vy: -Math.random()*2,
                            life: 1.0,
                            size: 5+Math.random()*10
                        });
                    }
                    // Lọc khói
                    this.smokeParticles = this.smokeParticles.filter(p => {
                        p.x += p.vx;
                        p.y += p.vy;
                        p.life -= 0.01;
                        return p.life > 0;
                    });
                }
                
                // Vẽ xe (dùng các điểm để tạo đa giác)
                draw(ctx, offsetX, offsetY) {
                    // Vẽ các mặt (tô màu)
                    ctx.fillStyle = this.color;
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 2;
                    
                    // Sắp xếp các điểm theo thứ tự bao quanh (đơn giản: vẽ từng tam giác từ điểm đầu)
                    // Thực tế nên dùng delaunay, nhưng ở đây ta vẽ các ô lưới
                    const cols = 5;
                    const rows = 4;
                    for (let row = 0; row < rows-1; row++) {
                        for (let col = 0; col < cols-1; col++) {
                            const i0 = row * cols + col;
                            const i1 = row * cols + (col+1);
                            const i2 = (row+1) * cols + col;
                            const i3 = (row+1) * cols + (col+1);
                            
                            const p0 = this.points[i0];
                            const p1 = this.points[i1];
                            const p2 = this.points[i2];
                            const p3 = this.points[i3];
                            
                            // Vẽ hai tam giác
                            ctx.beginPath();
                            ctx.moveTo(offsetX + p0.x, offsetY + p0.y);
                            ctx.lineTo(offsetX + p1.x, offsetY + p1.y);
                            ctx.lineTo(offsetX + p2.x, offsetY + p2.y);
                            ctx.closePath();
                            ctx.fill();
                            ctx.stroke();
                            
                            ctx.beginPath();
                            ctx.moveTo(offsetX + p1.x, offsetY + p1.y);
                            ctx.lineTo(offsetX + p3.x, offsetY + p3.y);
                            ctx.lineTo(offsetX + p2.x, offsetY + p2.y);
                            ctx.closePath();
                            ctx.fill();
                            ctx.stroke();
                        }
                    }
                    
                    // Vẽ bánh xe (các điểm góc)
                    ctx.fillStyle = '#222';
                    for (let idx of this.wheelIndices) {
                        const p = this.points[idx];
                        ctx.beginPath();
                        ctx.arc(offsetX + p.x, offsetY + p.y, 6, 0, 2*Math.PI);
                        ctx.fill();
                    }
                    
                    // Vẽ khói
                    ctx.globalAlpha = 0.5;
                    for (let p of this.smokeParticles) {
                        ctx.fillStyle = '#888';
                        ctx.beginPath();
                        ctx.arc(offsetX + p.x, offsetY + p.y, p.size * p.life, 0, 2*Math.PI);
                        ctx.fill();
                    }
                    ctx.globalAlpha = 1.0;
                }
                
                // Tác động lực điều khiển (ví dụ đẩy các điểm phía sau)
                applyControlForce(direction, strength) {
                    // direction: 0 = lên (tiến), 1 = xuống (lùi), 2 = trái, 3 = phải
                    // Chọn các điểm phía sau (theo chiều dọc)
                    const cols = 5;
                    const rows = 4;
                    for (let col = 1; col < cols-1; col++) {
                        const idx = (rows-1) * cols + col; // hàng cuối
                        const p = this.points[idx];
                        if (direction === 0) { // tiến
                            p.vy -= strength;
                        } else if (direction === 1) { // lùi
                            p.vy += strength;
                        }
                    }
                    // Lái: tác động lệch bên
                    if (direction === 2) { // trái
                        for (let row = 0; row < rows; row++) {
                            const idx = row * cols; // cột trái
                            const p = this.points[idx];
                            p.vx -= strength * 0.5;
                        }
                    } else if (direction === 3) { // phải
                        for (let row = 0; row < rows; row++) {
                            const idx = row * cols + (cols-1); // cột phải
                            const p = this.points[idx];
                            p.vx += strength * 0.5;
                        }
                    }
                }
                
                // Phanh tay: tăng ma sát các điểm bánh
                handbrake() {
                    for (let idx of this.wheelIndices) {
                        const p = this.points[idx];
                        p.vx *= 0.8;
                        p.vy *= 0.8;
                    }
                }
            }

            // Tạo xe người chơi
            const player = new SoftCar(1500, 1500, '#2277cc');
            
            // Tạo xe AI (đơn giản hóa, không dùng soft-body cho AI để tăng hiệu suất)
            const aiCars = [];
            for (let i = 0; i < 4; i++) {
                aiCars.push(new SoftCar(1000+Math.random()*1000, 1000+Math.random()*1000, '#cc4444'));
            }

            // ---------- VẬT CẢN ----------
            const obstacles = [];
            // Tường
            obstacles.push({ x: world.width/2, y: -25, w: world.width, h: 50 });
            obstacles.push({ x: world.width/2, y: world.height+25, w: world.width, h: 50 });
            obstacles.push({ x: -25, y: world.height/2, w: 50, h: world.height });
            obstacles.push({ x: world.width+25, y: world.height/2, w: 50, h: world.height });
            // Cây cối
            for (let i = 0; i < 20; i++) {
                obstacles.push({
                    x: 200+Math.random()*2600,
                    y: 200+Math.random()*2600,
                    w: 30+Math.random()*30,
                    h: 30+Math.random()*30
                });
            }

            // ---------- ĐIỀU KHIỂN ----------
            const keys = { up: false, down: false, left: false, right: false, space: false };
            
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

            // ---------- GAME STATE ----------
            let score = 0;
            let totalCrashes = 0;
            let gameRunning = true;

            // ---------- HÀM VA CHẠM (đơn giản) ----------
            function handleCollisions() {
                // Player vs AI cars (va chạm điểm - điểm)
                for (let ai of aiCars) {
                    for (let pi of player.points) {
                        for (let pj of ai.points) {
                            const dx = pi.x - pj.x;
                            const dy = pi.y - pj.y;
                            const dist = Math.hypot(dx, dy);
                            if (dist < 10) { // ngưỡng va chạm
                                // Tạo phản lực
                                const force = 0.5;
                                const nx = dx / (dist || 1);
                                const ny = dy / (dist || 1);
                                pi.vx += nx * force;
                                pi.vy += ny * force;
                                pj.vx -= nx * force;
                                pj.vy -= ny * force;
                                
                                totalCrashes++;
                                score += Math.floor(Math.hypot(pi.vx, pi.vy) * 5);
                                
                                // Làm hỏng xe (dựa trên vị trí va chạm)
                                // ... (có thể thêm)
                            }
                        }
                    }
                }
                
                // Player vs obstacles (hình chữ nhật)
                for (let obs of obstacles) {
                    for (let p of player.points) {
                        if (p.x > obs.x - obs.w/2 && p.x < obs.x + obs.w/2 &&
                            p.y > obs.y - obs.h/2 && p.y < obs.y + obs.h/2) {
                            // Đẩy điểm ra khỏi vật cản
                            const left = p.x - (obs.x - obs.w/2);
                            const right = (obs.x + obs.w/2) - p.x;
                            const top = p.y - (obs.y - obs.h/2);
                            const bottom = (obs.y + obs.h/2) - p.y;
                            
                            const minX = Math.min(left, right);
                            const minY = Math.min(top, bottom);
                            
                            if (minX < minY) {
                                if (left < right) {
                                    p.x = obs.x - obs.w/2 - 1;
                                    p.vx = -Math.abs(p.vx) * 0.3;
                                } else {
                                    p.x = obs.x + obs.w/2 + 1;
                                    p.vx = Math.abs(p.vx) * 0.3;
                                }
                            } else {
                                if (top < bottom) {
                                    p.y = obs.y - obs.h/2 - 1;
                                    p.vy = -Math.abs(p.vy) * 0.3;
                                } else {
                                    p.y = obs.y + obs.h/2 + 1;
                                    p.vy = Math.abs(p.vy) * 0.3;
                                }
                            }
                            
                            totalCrashes++;
                            score += Math.floor(Math.hypot(p.vx, p.vy) * 2);
                        }
                    }
                }
            }

            // ---------- CAMERA ----------
            function updateCamera() {
                world.camera.x = player.x - canvas.width/2;
                world.camera.y = player.y - canvas.height/2;
                world.camera.x = Math.max(0, Math.min(world.width - canvas.width, world.camera.x));
                world.camera.y = Math.max(0, Math.min(world.height - canvas.height, world.camera.y));
            }

            // ---------- VẼ ----------
            function draw() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                const camX = world.camera.x;
                const camY = world.camera.y;
                
                // Nền
                ctx.fillStyle = '#1a2c2c';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Lưới đường
                ctx.strokeStyle = '#3a5a5a';
                ctx.lineWidth = 1;
                const grid = 100;
                const startX = Math.floor(camX / grid) * grid;
                const startY = Math.floor(camY / grid) * grid;
                for (let x = startX; x < camX + canvas.width; x += grid) {
                    ctx.beginPath();
                    ctx.moveTo(x - camX, 0);
                    ctx.lineTo(x - camX, canvas.height);
                    ctx.stroke();
                }
                for (let y = startY; y < camY + canvas.height; y += grid) {
                    ctx.beginPath();
                    ctx.moveTo(0, y - camY);
                    ctx.lineTo(canvas.width, y - camY);
                    ctx.stroke();
                }
                
                // Vẽ vật cản
                ctx.fillStyle = '#6b4e3a';
                for (let obs of obstacles) {
                    ctx.fillRect(obs.x - obs.w/2 - camX, obs.y - obs.h/2 - camY, obs.w, obs.h);
                }
                
                // Vẽ xe AI
                for (let ai of aiCars) {
                    ai.draw(ctx, -camX, -camY);
                }
                
                // Vẽ xe player
                player.draw(ctx, -camX, -camY);
            }

            // ---------- CẬP NHẬT UI ----------
            function updateUI() {
                document.getElementById('score').innerText = Math.floor(score);
                document.getElementById('crashes').innerText = totalCrashes;
                const speed = Math.hypot(player.points[0].vx, player.points[0].vy) * 10;
                document.getElementById('speed').innerText = Math.floor(speed);
                
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
                
                // Điều khiển
                const force = 0.5;
                if (keys.up) player.applyControlForce(0, force);
                if (keys.down) player.applyControlForce(1, force * 0.6);
                if (keys.left) player.applyControlForce(2, force * 2);
                if (keys.right) player.applyControlForce(3, force * 2);
                if (keys.space) player.handbrake();
                
                // Cập nhật vật lý
                player.update(dt);
                for (let ai of aiCars) {
                    ai.update(dt);
                }
                
                // Va chạm
                handleCollisions();
                
                // Camera
                updateCamera();
                
                // Vẽ
                draw();
                updateUI();
                
                // Game over khi động cơ hết máu
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
