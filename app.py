function handleCollisions() {
    const threshold = 2.0; // ngưỡng vận tốc tương đối để tính va chạm
    
    // Player vs AI
    for (let ai of aiCars) {
        for (let pi of player.points) {
            for (let pj of ai.points) {
                const dx = pi.x - pj.x;
                const dy = pi.y - pj.y;
                const dist = Math.hypot(dx, dy);
                if (dist < 8) { // khoảng cách va chạm
                    // Tính vận tốc tương đối
                    const vRelX = pi.vx - pj.vx;
                    const vRelY = pi.vy - pj.vy;
                    const vRel = Math.hypot(vRelX, vRelY);
                    
                    if (vRel > threshold) {
                        // Tạo phản lực
                        const nx = dx / (dist || 1);
                        const ny = dy / (dist || 1);
                        const force = vRel * 0.5;
                        pi.vx += nx * force;
                        pi.vy += ny * force;
                        pj.vx -= nx * force;
                        pj.vy -= ny * force;
                        
                        totalCrashes++;
                        score += Math.floor(vRel * 5);
                        
                        // Làm hỏng xe (tạm thời giảm máu động cơ)
                        player.damage.engine = Math.max(0, player.damage.engine - vRel * 0.5);
                    }
                }
            }
        }
    }
    
    // Player vs obstacles – tương tự, chỉ tính khi vận tốc lớn
    for (let obs of obstacles) {
        for (let p of player.points) {
            // ... kiểm tra va chạm AABB ...
            if (/* va chạm */) {
                const speed = Math.hypot(p.vx, p.vy);
                if (speed > threshold) {
                    // xử lý va chạm, cộng điểm
                }
            }
        }
    }
}
