import streamlit as st

st.set_page_config(page_title="3D Pixel Car Crash", layout="wide", initial_sidebar_state="collapsed")

# Ẩn hoàn toàn giao diện Streamlit
st.markdown("""
<style>
    #MainMenu, footer, header {display: none;}
    .stApp {background: black; padding: 0; margin: 0;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# HTML game 3D – nhúng qua component
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>3D Pixel Car Crash</title>
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Courier New', monospace; background: black; }
        #info, #upgrade, #controls {
            position: absolute; z-index: 100; color: white; text-shadow: 2px 2px 0 #000;
            background: rgba(0,0,0,0.7); border-radius: 12px; backdrop-filter: blur(2px);
            border: 2px solid #00aaff; box-shadow: 0 0 15px #00aaff80;
            padding: 16px; pointer-events: none;
        }
        #info { top: 20px; left: 20px; width: 240px; }
        #upgrade { bottom: 20px; left: 20px; width: 260px; pointer-events: auto; }
        #controls { bottom: 20px; right: 20px; width: 200px; }
        .stat { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 15px; }
        .health-bg { width: 100%; height: 18px; background: #333; border-radius: 9px; margin: 8px 0; overflow: hidden; }
        .health-fill { height: 100%; background: linear-gradient(90deg, #0f0, #f00); width: 100%; }
        .upgrade-btn {
            background: #ffaa00; color: #000; border: none; padding: 10px; margin: 6px 0;
            border-radius: 6px; font-weight: bold; width: 100%; cursor: pointer; font-size: 15px;
            transition: 0.2s; border-bottom: 3px solid #884400; pointer-events: auto;
        }
        .upgrade-btn:hover { background: #ffcc00; transform: scale(1.02); }
        .upgrade-btn:disabled { background: #555; border-bottom-color: #222; }
        #focus-hint {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.9); color: #ffaa00; padding: 20px; border-radius: 16px;
            border: 2px solid #ffaa00; font-size: 22px; display: none; z-index: 1000;
        }
        a { color: #00aaff; }
        .pixel-text { letter-spacing: 2px; }
    </style>
</head>
<body>
    <div id="focus-hint">🔲 CLICK VÀO ĐÂY ĐỂ ĐIỀU KHIỂN</div>
    
    <div id="info">
        <div style="font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #00aaff; text-align: center;">
            💥 3D PIXEL CRASH
        </div>
        <div class="stat"><span>🏆 SCORE</span><span id="score">0</span></div>
        <div class="stat"><span>💥 CRASHES</span><span id="crashes">0</span></div>
        <div class="health-bg"><div id="health-fill" class="health-fill" style="width:100%"></div></div>
        <div class="stat"><span>🛡️ HEALTH</span><span id="health">100%</span></div>
        <div class="stat"><span>⚡ SPEED</span><span id="speed">0 km/h</span></div>
        <div class="stat"><span>🚗 AI</span><span id="ai-count">8</span></div>
        <div class="stat"><span>⏱️ TIME</span><span id="time">0s</span></div>
    </div>

    <div id="upgrade">
        <div style="font-size: 20px; color: #ffaa00; margin-bottom: 12px;">⬆️ UPGRADE</div>
        <div class="stat"><span>💰 POINTS</span><span id="upgrade-score">0</span></div>
        <button class="upgrade-btn" id="upgrade-speed" onclick="upgradeStat('speed')">⚡ TỐC ĐỘ +10% (50đ)</button>
        <button class="upgrade-btn" id="upgrade-armor" onclick="upgradeStat('armor')">🛡️ GIÁP +20% (30đ)</button>
        <button class="upgrade-btn" id="upgrade-accel" onclick="upgradeStat('accel')">🚀 GIA TỐC +15% (40đ)</button>
    </div>

    <div id="controls">
        <div style="font-size: 16px; margin-bottom: 6px; color: #aaa;">🎮 ĐIỀU KHIỂN</div>
        <div>W / ↑ : Tăng tốc</div>
        <div>S / ↓ : Phanh</div>
        <div>A / ← : Trái</div>
        <div>D / → : Phải</div>
        <div>SPACE : Phanh tay</div>
        <div style="margin-top: 8px; font-size: 13px;">🖱️ CLICK vào game để điều khiển</div>
    </div>

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

        // ---------- FIX ĐIỀU KHIỂN: focus vào canvas ----------
        const focusHint = document.getElementById('focus-hint');
        function setupCanvasFocus(renderer) {
            const canvas = renderer.domElement;
            canvas.setAttribute('tabindex', '0');  // cho phép focus
            canvas.style.outline = 'none';
            
            // Click vào canvas -> ẩn hint, focus
            canvas.addEventListener('click', () => {
                canvas.focus();
                focusHint.style.display = 'none';
            });
            
            // Nếu chưa focus, hiển thị hint
            setTimeout(() => {
                if (document.activeElement !== canvas) {
                    focusHint.style.display = 'block';
                }
            }, 500);
            
            // Bắt sự kiện keydown/keyup trên canvas
            return canvas;
        }

        // ---------- KHỞI TẠO THREE.JS ----------
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0a20); // xanh đêm
        
        const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 500);
        camera.position.set(20, 12, 30);
        
        const renderer = new THREE.WebGLRenderer({ antialias: false }); // pixel style
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.setPixelRatio(window.devicePixelRatio);
        document.body.appendChild(renderer.domElement);
        
        const canvas = setupCanvasFocus(renderer);
        
        // OrbitControls để người chơi xoay view
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = false;
        controls.enableZoom = true;
        controls.target.set(0, 0, 0);
        controls.maxPolarAngle = Math.PI / 2.4;
        controls.minDistance = 15;
        controls.maxDistance = 80;

        // ---------- ÁNH SÁNG ĐẸP ----------
        const ambient = new THREE.AmbientLight(0x404c6b);
        scene.add(ambient);
        
        const sun = new THREE.DirectionalLight(0xffeedd, 1.2);
        sun.position.set(10, 20, 15);
        sun.castShadow = true;
        sun.receiveShadow = true;
        sun.shadow.mapSize.width = 1024;
        sun.shadow.mapSize.height = 1024;
        sun.shadow.camera.near = 1;
        sun.shadow.camera.far = 80;
        sun.shadow.camera.left = -40;
        sun.shadow.camera.right = 40;
        sun.shadow.camera.top = 40;
        sun.shadow.camera.bottom = -40;
        scene.add(sun);
        
        // Ánh sáng phụ
        const backLight = new THREE.PointLight(0x4466aa, 0.6);
        backLight.position.set(-15, 5, -20);
        scene.add(backLight);
        
        const fillLight = new THREE.PointLight(0x7799cc, 0.5);
        fillLight.position.set(0, 10, 20);
        scene.add(fillLight);

        // ---------- HỆ THỐNG ĐƯỜNG XÁ - NGÃ TƯ, VẠCH KẺ ----------
        function createRoad() {
            // Mặt đường nền
            const roadMat = new THREE.MeshStandardMaterial({ color: 0x2a2a3a, roughness: 0.8, metalness: 0.2 });
            const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), roadMat);
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -0.51;
            ground.receiveShadow = true;
            scene.add(ground);
            
            // Vạch kẻ đường - dạng lưới ô vuông tạo ngã tư
            const lineMat = new THREE.MeshStandardMaterial({ color: 0xffdd77, emissive: 0x443311 });
            const stripeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x444444 });
            
            // Vạch dọc
            for (let i = -80; i <= 80; i += 20) {
                const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 10), stripeMat);
                stripe.position.set(i, -0.5, 0);
                stripe.receiveShadow = true;
                scene.add(stripe);
            }
            // Vạch ngang
            for (let i = -80; i <= 80; i += 20) {
                const stripe = new THREE.Mesh(new THREE.BoxGeometry(10, 0.1, 0.3), stripeMat);
                stripe.position.set(0, -0.5, i);
                stripe.receiveShadow = true;
                scene.add(stripe);
            }
            
            // Vỉa hè / lề đường
            const curbMat = new THREE.MeshStandardMaterial({ color: 0x8a7a6a });
            for (let x = -90; x <= 90; x += 30) {
                for (let z = -90; z <= 90; z += 30) {
                    if (Math.abs(x) < 85 && Math.abs(z) < 85) continue; // chừa đường
                    const curb = new THREE.Mesh(new THREE.BoxGeometry(2, 0.4, 2), curbMat);
                    curb.position.set(x, -0.3, z);
                    curb.receiveShadow = true;
                    scene.add(curb);
                }
            }
            
            // Ngã tư trung tâm - vạch đi bộ
            const crossMat = new THREE.MeshStandardMaterial({ color: 0xffcc88 });
            for (let i = -4; i <= 4; i+=2) {
                const bar1 = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.1, 10), crossMat);
                bar1.position.set(i, -0.48, 0);
                bar1.receiveShadow = true;
                scene.add(bar1);
                const bar2 = new THREE.Mesh(new THREE.BoxGeometry(10, 0.1, 0.5), crossMat);
                bar2.position.set(0, -0.48, i);
                bar2.receiveShadow = true;
                scene.add(bar2);
            }
        }
        createRoad();

        // ---------- CÔNG TRÌNH - NHÀ CỬA CHI TIẾT ----------
        function createBuilding(x, z, width, height, depth, color) {
            const group = new THREE.Group();
            // Thân chính
            const body = new THREE.Mesh(
                new THREE.BoxGeometry(width, height, depth),
                new THREE.MeshStandardMaterial({ color, roughness: 0.6, emissive: 0x111122 })
            );
            body.castShadow = true;
            body.receiveShadow = true;
            body.position.y = height/2 - 0.5;
            group.add(body);
            
            // Mái
            const roof = new THREE.Mesh(
                new THREE.ConeGeometry(width * 0.8, height*0.2, 4),
                new THREE.MeshStandardMaterial({ color: 0x884444, roughness: 0.8 })
            );
            roof.rotation.y = Math.PI/4;
            roof.position.y = height - 0.3;
            roof.castShadow = true;
            roof.receiveShadow = true;
            group.add(roof);
            
            // Cửa sổ pixel
            const winMat = new THREE.MeshStandardMaterial({ color: 0xffcc00, emissive: 0x553300 });
            for (let i = 0; i < 3; i++) {
                for (let j = 0; j < 2; j++) {
                    const win = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.2), winMat);
                    win.position.set((i-1)*0.9, j*0.8 + 0.5, depth/2 + 0.1);
                    win.castShadow = true;
                    group.add(win);
                    
                    const winBack = win.clone();
                    winBack.position.z = -depth/2 - 0.1;
                    group.add(winBack);
                }
            }
            
            group.position.set(x, 0, z);
            scene.add(group);
            return group;
        }
        
        // Thêm nhiều nhà
        createBuilding(-20, -25, 5, 4, 5, 0xb85e3a);
        createBuilding(25, -20, 6, 5, 6, 0x8b5a2b);
        createBuilding(-22, 22, 5, 6, 5, 0xa0522d);
        createBuilding(20, 25, 7, 5, 7, 0x9c7c3b);
        createBuilding(-30, 5, 4, 3, 4, 0x7a5c3a);
        createBuilding(30, -5, 4, 4, 4, 0x6b4e3a);
        createBuilding(5, -35, 6, 5, 6, 0x8b4513);
        createBuilding(-5, 35, 6, 5, 6, 0x8b4513);

        // ---------- CÂY CỐI (PIXEL) ----------
        function createTree(x, z) {
            const group = new THREE.Group();
            const trunkMat = new THREE.MeshStandardMaterial({ color: 0x6b4e3a, roughness: 0.9 });
            const leafMat = new THREE.MeshStandardMaterial({ color: 0x2d6a4f, emissive: 0x143023 });
            
            const trunk = new THREE.Mesh(new THREE.BoxGeometry(0.6, 2, 0.6), trunkMat);
            trunk.position.y = 0.5;
            trunk.castShadow = true;
            trunk.receiveShadow = true;
            group.add(trunk);
            
            for (let i = 0; i < 3; i++) {
                const leaf = new THREE.Mesh(new THREE.BoxGeometry(1.8 - i*0.3, 0.8, 1.8 - i*0.3), leafMat);
                leaf.position.y = 1.5 + i * 0.6;
                leaf.castShadow = true;
                leaf.receiveShadow = true;
                group.add(leaf);
            }
            
            group.position.set(x, 0, z);
            scene.add(group);
        }
        
        for (let i = 0; i < 30; i++) {
            let x = (Math.random() - 0.5) * 150;
            let z = (Math.random() - 0.5) * 150;
            if (Math.abs(x) < 40 && Math.abs(z) < 40) continue; // tránh giữa đường
            createTree(x, z);
        }

        // ---------- VẬT CẢN: NÓN, THÙNG, ĐÈN ĐƯỜNG ----------
        function createObstacle(x, z, type) {
            const group = new THREE.Group();
            if (type === 'cone') {
                const cone = new THREE.Mesh(
                    new THREE.ConeGeometry(0.8, 1.2, 8),
                    new THREE.MeshStandardMaterial({ color: 0xff5500, emissive: 0x331100 })
                );
                cone.castShadow = true;
                cone.receiveShadow = true;
                cone.position.y = 0.6;
                group.add(cone);
            } else if (type === 'barrel') {
                const barrel = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.6, 0.6, 1, 8),
                    new THREE.MeshStandardMaterial({ color: 0xcc3333, emissive: 0x331111 })
                );
                barrel.castShadow = true;
                barrel.receiveShadow = true;
                barrel.position.y = 0.5;
                group.add(barrel);
                
                const hoop = new THREE.Mesh(
                    new THREE.TorusGeometry(0.61, 0.1, 4, 20),
                    new THREE.MeshStandardMaterial({ color: 0x666666, roughness: 0.7 })
                );
                hoop.rotation.x = Math.PI/2;
                hoop.position.y = 0.5;
                hoop.castShadow = true;
                group.add(hoop);
            } else if (type === 'block') {
                const block = new THREE.Mesh(
                    new THREE.BoxGeometry(1, 1, 1),
                    new THREE.MeshStandardMaterial({ color: 0xffaa00, emissive: 0x442200 })
                );
                block.castShadow = true;
                block.receiveShadow = true;
                block.position.y = 0.5;
                group.add(block);
            }
            group.position.set(x, 0, z);
            scene.add(group);
            return group;
        }

        const obstacles = [];
        obstacles.push(createObstacle(8, 5, 'cone'));
        obstacles.push(createObstacle(12, -3, 'barrel'));
        obstacles.push(createObstacle(-6, -8, 'block'));
        obstacles.push(createObstacle(-10, 10, 'cone'));
        obstacles.push(createObstacle(15, 15, 'barrel'));
        obstacles.push(createObstacle(-15, -12, 'block'));

        // ---------- XE NGƯỜI CHƠI: ĐẸP, CHI TIẾT ----------
        function createPlayerCar() {
            const group = new THREE.Group();
            
            // Thân chính
            const bodyGeo = new THREE.BoxGeometry(2.2, 0.7, 4.5);
            const bodyMat = new THREE.MeshStandardMaterial({ color: 0x2277cc, roughness: 0.4, metalness: 0.6, emissive: 0x001122 });
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            body.castShadow = true;
            body.receiveShadow = true;
            body.position.y = 0.55;
            group.add(body);
            
            // Mui xe
            const roofGeo = new THREE.BoxGeometry(1.3, 0.5, 1.8);
            const roofMat = new THREE.MeshStandardMaterial({ color: 0x44aaff, roughness: 0.5, metalness: 0.5 });
            const roof = new THREE.Mesh(roofGeo, roofMat);
            roof.castShadow = true;
            roof.receiveShadow = true;
            roof.position.set(0, 1.0, -0.5);
            group.add(roof);
            
            // Kính trước/sau
            const glassMat = new THREE.MeshStandardMaterial({ color: 0x88ccff, emissive: 0x224466, transparent: true, opacity: 0.7 });
            const frontGlass = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.4, 0.3), glassMat);
            frontGlass.position.set(0, 0.9, -1.7);
            frontGlass.castShadow = true;
            group.add(frontGlass);
            
            const rearGlass = frontGlass.clone();
            rearGlass.position.z = 1.7;
            group.add(rearGlass);
            
            // Đèn trước
            const lightMat = new THREE.MeshStandardMaterial({ color: 0xffeedd, emissive: 0xff6600 });
            const headLightL = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.2, 0.2), lightMat);
            headLightL.position.set(-0.8, 0.5, -2.1);
            headLightL.castShadow = true;
            group.add(headLightL);
            const headLightR = headLightL.clone();
            headLightR.position.x = 0.8;
            group.add(headLightR);
            
            // Đèn sau
            const tailLightMat = new THREE.MeshStandardMaterial({ color: 0xff3333, emissive: 0x550000 });
            const tailLightL = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.2, 0.2), tailLightMat);
            tailLightL.position.set(-0.8, 0.5, 2.1);
            tailLightL.castShadow = true;
            group.add(tailLightL);
            const tailLightR = tailLightL.clone();
            tailLightR.position.x = 0.8;
            group.add(tailLightR);
            
            // Bánh xe
            const wheelGeo = new THREE.CylinderGeometry(0.45, 0.45, 0.3, 16);
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.8 });
            const positions = [[-1.1, 0.3, -1.4], [1.1, 0.3, -1.4], [-1.1, 0.3, 1.4], [1.1, 0.3, 1.4]];
            positions.forEach(pos => {
                const wheel = new THREE.Mesh(wheelGeo, wheelMat);
                wheel.rotation.z = Math.PI/2;
                wheel.position.set(pos[0], pos[1], pos[2]);
                wheel.castShadow = true;
                wheel.receiveShadow = true;
                group.add(wheel);
            });
            
            // Viền vàng (player highlight)
            const edges = new THREE.EdgesGeometry(bodyGeo);
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffaa00 }));
            line.position.copy(body.position);
            group.add(line);
            
            return group;
        }

        const playerCar = createPlayerCar();
        playerCar.position.set(0, 0.2, 0);
        scene.add(playerCar);

        // ---------- XE AI: MÀU SẮC, CHI TIẾT, KHÔNG LẮC ----------
        function createAICar(colorHex) {
            const group = new THREE.Group();
            
            const bodyGeo = new THREE.BoxGeometry(2.0, 0.7, 4.2);
            const bodyMat = new THREE.MeshStandardMaterial({ color: colorHex, roughness: 0.5, metalness: 0.4, emissive: 0x221100 });
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            body.castShadow = true;
            body.receiveShadow = true;
            body.position.y = 0.55;
            group.add(body);
            
            const roofGeo = new THREE.BoxGeometry(1.2, 0.4, 1.6);
            const roofMat = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.7 });
            const roof = new THREE.Mesh(roofGeo, roofMat);
            roof.castShadow = true;
            roof.receiveShadow = true;
            roof.position.set(0, 0.95, -0.4);
            group.add(roof);
            
            const glassMat = new THREE.MeshStandardMaterial({ color: 0x88aacc, emissive: 0x224466, transparent: true, opacity: 0.7 });
            const frontGlass = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.3, 0.3), glassMat);
            frontGlass.position.set(0, 0.8, -1.6);
            frontGlass.castShadow = true;
            group.add(frontGlass);
            
            const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.9 });
            const positions = [[-1.0, 0.3, -1.3], [1.0, 0.3, -1.3], [-1.0, 0.3, 1.3], [1.0, 0.3, 1.3]];
            positions.forEach(pos => {
                const wheel = new THREE.Mesh(wheelGeo, wheelMat);
                wheel.rotation.z = Math.PI/2;
                wheel.position.set(pos[0], pos[1], pos[2]);
                wheel.castShadow = true;
                wheel.receiveShadow = true;
                group.add(wheel);
            });
            
            return group;
        }

        // AI cars với target di chuyển mượt
        const aiCars = [];
        const aiColors = [0xff3333, 0x33ff33, 0xffdd33, 0xff9933, 0xaa33aa, 0x33aaff, 0xff44aa, 0x44ffaa];
        for (let i = 0; i < 8; i++) {
            const car = createAICar(aiColors[i % aiColors.length]);
            let x = (Math.random() - 0.5) * 60;
            let z = (Math.random() - 0.5) * 60;
            car.position.set(x, 0.2, z);
            car.rotation.y = Math.random() * Math.PI * 2;
            scene.add(car);
            
            aiCars.push({
                mesh: car,
                vx: 0, vz: 0,
                targetX: (Math.random() - 0.5) * 80,
                targetZ: (Math.random() - 0.5) * 80,
                speed: 0.08 + Math.random() * 0.06,
                color: aiColors[i % aiColors.length],
                health: 100,
                timer: 0
            });
        }

        // ---------- HỆ THỐNG PARTICLE PIXEL (VA CHẠM) ----------
        const particles = [];
        function createCrashParticles(x, y, z, colorHex) {
            for (let i = 0; i < 25; i++) {
                const size = Math.random() * 0.35 + 0.1;
                const cube = new THREE.Mesh(
                    new THREE.BoxGeometry(size, size, size),
                    new THREE.MeshStandardMaterial({ color: colorHex, emissive: 0x553300, emissiveIntensity: 0.3 })
                );
                cube.position.set(x, y, z);
                cube.userData = {
                    vx: (Math.random() - 0.5) * 0.6,
                    vy: Math.random() * 0.5 + 0.2,
                    vz: (Math.random() - 0.5) * 0.6,
                    life: 1.0,
                    size: size
                };
                scene.add(cube);
                particles.push(cube);
            }
        }

        // ---------- VẬT LÝ NGƯỜI CHƠI ----------
        const player = {
            mesh: playerCar,
            vx: 0, vz: 0,
            maxSpeed: 0.4,
            acceleration: 0.018,
            brake: 0.06,
            turnSpeed: 0.035,
            health: 100,
            armor: 1.0
        };

        // ---------- ĐIỀU KHIỂN ----------
        const keys = { up: false, down: false, left: false, right: false, space: false };
        
        function handleKey(e, value) {
            switch(e.key) {
                case 'w': case 'W': case 'ArrowUp': keys.up = value; e.preventDefault(); break;
                case 's': case 'S': case 'ArrowDown': keys.down = value; e.preventDefault(); break;
                case 'a': case 'A': case 'ArrowLeft': keys.left = value; e.preventDefault(); break;
                case 'd': case 'D': case 'ArrowRight': keys.right = value; e.preventDefault(); break;
                case ' ': keys.space = value; e.preventDefault(); break;
            }
        }
        
        canvas.addEventListener('keydown', (e) => handleKey(e, true));
        canvas.addEventListener('keyup', (e) => handleKey(e, false));
        
        // Blur canvas -> hiện hint
        canvas.addEventListener('blur', () => {
            focusHint.style.display = 'block';
        });
        canvas.addEventListener('focus', () => {
            focusHint.style.display = 'none';
        });

        // ---------- GAME STATE ----------
        let score = 0;
        let totalCrashes = 0;
        let gameTime = 0;
        let gameRunning = true;
        
        // Nâng cấp
        let upgrade = { speed: 1, armor: 1, accel: 1 };
        window.upgradeStat = function(stat) {
            const cost = { speed: 50, armor: 30, accel: 40 };
            if (score >= cost[stat]) {
                score -= cost[stat];
                upgrade[stat] += 0.1;
                if (stat === 'speed') player.maxSpeed *= 1.1;
                if (stat === 'accel') player.acceleration *= 1.15;
                if (stat === 'armor') player.armor *= 1.2;
                document.getElementById('upgrade-score').innerText = score;
            }
        };

        // ---------- AI MƯỢT: TARGET + LÁI TỪ TỪ ----------
        function updateAI() {
            aiCars.forEach(ai => {
                ai.timer += 0.01;
                if (ai.timer > 5) {
                    ai.targetX = (Math.random() - 0.5) * 80;
                    ai.targetZ = (Math.random() - 0.5) * 80;
                    ai.timer = 0;
                }
                
                const dx = ai.targetX - ai.mesh.position.x;
                const dz = ai.targetZ - ai.mesh.position.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                
                if (dist > 1) {
                    const angle = Math.atan2(dx, dz);
                    const currentAngle = ai.mesh.rotation.y;
                    let diff = angle - currentAngle;
                    while (diff > Math.PI) diff -= Math.PI*2;
                    while (diff < -Math.PI) diff += Math.PI*2;
                    ai.mesh.rotation.y += diff * 0.03; // lái từ từ
                    
                    ai.vx += Math.sin(ai.mesh.rotation.y) * 0.002;
                    ai.vz += Math.cos(ai.mesh.rotation.y) * 0.002;
                }
                
                // Giới hạn tốc độ
                let speed = Math.sqrt(ai.vx*ai.vx + ai.vz*ai.vz);
                if (speed > ai.speed) {
                    ai.vx = (ai.vx / speed) * ai.speed;
                    ai.vz = (ai.vz / speed) * ai.speed;
                }
                
                ai.mesh.position.x += ai.vx;
                ai.mesh.position.z += ai.vz;
                
                // Ma sát
                ai.vx *= 0.98;
                ai.vz *= 0.98;
                
                // Giới hạn map
                const bound = 70;
                ai.mesh.position.x = Math.max(-bound, Math.min(bound, ai.mesh.position.x));
                ai.mesh.position.z = Math.max(-bound, Math.min(bound, ai.mesh.position.z));
                
                ai.health = Math.min(100, ai.health + 0.02);
            });
        }

        // ---------- VA CHẠM ----------
        function checkCollisions() {
            // Player vs AI
            aiCars.forEach(ai => {
                const dx = player.mesh.position.x - ai.mesh.position.x;
                const dz = player.mesh.position.z - ai.mesh.position.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                if (dist < 2.4) {
                    const speedP = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
                    const speedAI = Math.sqrt(ai.vx*ai.vx + ai.vz*ai.vz);
                    const force = speedP + speedAI;
                    if (force > 0.1) {
                        const damage = force * 15 / player.armor;
                        player.health = Math.max(0, player.health - damage);
                        ai.health = Math.max(0, ai.health - damage * 0.7);
                        totalCrashes++;
                        score += Math.floor(force * 12);
                        createCrashParticles(
                            (player.mesh.position.x + ai.mesh.position.x)/2,
                            0.6,
                            (player.mesh.position.z + ai.mesh.position.z)/2,
                            0xffaa00
                        );
                        // Đẩy
                        if (dist > 0) {
                            const push = force * 0.8;
                            player.mesh.position.x += (dx / dist) * push * 0.1;
                            player.mesh.position.z += (dz / dist) * push * 0.1;
                            ai.mesh.position.x -= (dx / dist) * push * 0.1;
                            ai.mesh.position.z -= (dz / dist) * push * 0.1;
                        }
                    }
                    if (ai.health <= 0) {
                        score += 150;
                        totalCrashes++;
                        createCrashParticles(ai.mesh.position.x, 0.6, ai.mesh.position.z, ai.color);
                        ai.health = 100;
                        ai.mesh.position.x = (Math.random() - 0.5) * 60;
                        ai.mesh.position.z = (Math.random() - 0.5) * 60;
                    }
                }
            });
            
            // Player vs obstacles
            obstacles.forEach(obs => {
                const dx = player.mesh.position.x - obs.position.x;
                const dz = player.mesh.position.z - obs.position.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                if (dist < 1.8) {
                    const speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
                    if (speed > 0.1) {
                        const damage = speed * 12 / player.armor;
                        player.health = Math.max(0, player.health - damage);
                        totalCrashes++;
                        score += Math.floor(speed * 8);
                        createCrashParticles(obs.position.x, 0.5, obs.position.z, 0xff5500);
                        if (dist > 0) {
                            player.mesh.position.x += (dx / dist) * 1.5;
                            player.mesh.position.z += (dz / dist) * 1.5;
                        }
                    }
                }
            });
        }

        // ---------- UPDATE UI ----------
        function updateUI() {
            const speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
            document.getElementById('score').innerText = Math.floor(score);
            document.getElementById('crashes').innerText = totalCrashes;
            document.getElementById('health').innerText = Math.floor(player.health) + '%';
            document.getElementById('health-fill').style.width = player.health + '%';
            document.getElementById('speed').innerText = Math.floor(speed * 200) + ' km/h';
            document.getElementById('ai-count').innerText = aiCars.length;
            document.getElementById('time').innerText = Math.floor(gameTime) + 's';
            document.getElementById('upgrade-score').innerText = score;
        }

        // ---------- ANIMATION LOOP ----------
        function animate() {
            if (!gameRunning) return;
            
            // Điều khiển player
            if (keys.up) {
                player.vx += Math.sin(player.mesh.rotation.y) * player.acceleration * upgrade.accel;
                player.vz += Math.cos(player.mesh.rotation.y) * player.acceleration * upgrade.accel;
            }
            if (keys.down) {
                player.vx -= Math.sin(player.mesh.rotation.y) * player.brake;
                player.vz -= Math.cos(player.mesh.rotation.y) * player.brake;
            }
            if (keys.left) player.mesh.rotation.y += player.turnSpeed * (keys.up ? 1 : 0.6);
            if (keys.right) player.mesh.rotation.y -= player.turnSpeed * (keys.up ? 1 : 0.6);
            if (keys.space) {
                player.vx *= 0.94;
                player.vz *= 0.94;
            }
            
            // Giới hạn tốc độ
            let speed = Math.sqrt(player.vx*player.vx + player.vz*player.vz);
            if (speed > player.maxSpeed * upgrade.speed) {
                player.vx = (player.vx / speed) * (player.maxSpeed * upgrade.speed);
                player.vz = (player.vz / speed) * (player.maxSpeed * upgrade.speed);
            }
            
            player.vx *= 0.985;
            player.vz *= 0.985;
            
            player.mesh.position.x += player.vx;
            player.mesh.position.z += player.vz;
            
            // Biên
            const bound = 70;
            player.mesh.position.x = Math.max(-bound, Math.min(bound, player.mesh.position.x));
            player.mesh.position.z = Math.max(-bound, Math.min(bound, player.mesh.position.z));
            
            // AI
            updateAI();
            
            // Va chạm
            checkCollisions();
            
            // Particles
            particles.forEach((p, idx) => {
                p.userData.life -= 0.012;
                if (p.userData.life <= 0) {
                    scene.remove(p);
                    particles.splice(idx, 1);
                } else {
                    p.position.x += p.userData.vx;
                    p.position.y += p.userData.vy;
                    p.position.z += p.userData.vz;
                    p.userData.vy -= 0.008;
                    p.scale.setScalar(p.userData.life);
                }
            });
            
            // Camera target
            controls.target.copy(player.mesh.position);
            controls.update();
            
            // Time
            gameTime += 1/60;
            
            // UI
            updateUI();
            
            // Game over
            if (player.health <= 0) {
                gameRunning = false;
                setTimeout(() => {
                    alert('💥 GAME OVER! ĐIỂM: ' + Math.floor(score));
                    location.reload();
                }, 100);
            }
            
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }
        
        animate();

        // Resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    </script>
</body>
</html>
"""

st.components.v1.html(game_html, height=1000, scrolling=False)
