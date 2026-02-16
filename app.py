import streamlit as st

st.set_page_config(page_title="Voxel BeamNG Web", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header {display:none;}
.stApp {background:black;padding:0;}
.block-container {padding:0!important;max-width:100%!important;}
</style>
""", unsafe_allow_html=True)

GAME = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>Voxel Crash City</title>
<style>
body{margin:0;overflow:hidden;background:black;}
canvas{width:100vw;height:100vh;image-rendering:pixelated;}
#hud{position:absolute;top:10px;left:10px;color:#0ff;font-family:monospace;background:rgba(0,0,0,.6);padding:10px;border:2px solid cyan;}
</style>
</head>
<body>
<div id="hud">SPD:<span id="spd">0</span> | CRASH:<span id="cr">0</span></div>
<canvas id="c"></canvas>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>

// ===== BASIC ENGINE =====
const c=document.getElementById("c");
const r=new THREE.WebGLRenderer({canvas:c,antialias:false});
r.setSize(innerWidth,innerHeight);
r.setPixelRatio(Math.min(devicePixelRatio,2));

const scene=new THREE.Scene();
scene.background=new THREE.Color(0x020008);

const cam=new THREE.PerspectiveCamera(65,innerWidth/innerHeight,0.1,5000);

// lights
scene.add(new THREE.AmbientLight(0x505070));
const sun=new THREE.DirectionalLight(0xffffff,1.5);
sun.position.set(100,200,100);
sun.castShadow=true;
scene.add(sun);

// ===== GROUND =====
const ground=new THREE.Mesh(new THREE.PlaneGeometry(3000,3000),
 new THREE.MeshStandardMaterial({color:0x05050c})
);
ground.rotation.x=-Math.PI/2;
scene.add(ground);

// ===== ROAD GRID (no buildings here) =====
const roadMat=new THREE.MeshStandardMaterial({color:0x202020});
const ROAD_STEP=120;
for(let i=-1200;i<=1200;i+=ROAD_STEP){
 let r1=new THREE.Mesh(new THREE.PlaneGeometry(2400,20),roadMat);
 r1.rotation.x=-Math.PI/2;
 r1.position.z=i;
 scene.add(r1);

 let r2=new THREE.Mesh(new THREE.PlaneGeometry(20,2400),roadMat);
 r2.rotation.x=-Math.PI/2;
 r2.position.x=i;
 scene.add(r2);
}

// ===== CITY BLOCKS (NO ROAD ZONE BUILDING) =====
function rand(a,b){return a+Math.random()*(b-a);}
function building(x,z){
 let w=rand(20,60), d=rand(20,60), h=rand(40,300);
 let color=0x111111+Math.random()*0x444444;
 let b=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),
  new THREE.MeshStandardMaterial({color})
 );
 b.position.set(x,h/2,z);
 b.castShadow=true;
 scene.add(b);
}

// place buildings only between roads
for(let x=-1100;x<=1100;x+=ROAD_STEP){
 for(let z=-1100;z<=1100;z+=ROAD_STEP){
  if(Math.random()<0.6){
   let bx=x+rand(30,ROAD_STEP-30);
   let bz=z+rand(30,ROAD_STEP-30);
   building(bx,bz);
  }
 }
}

// ===== PLAYER CAR VOXEL (REAL SEDAN SHAPE) =====
const car=new THREE.Group();
scene.add(car);
const voxels=[];

function v(x,y,z,c){
 let m=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),
  new THREE.MeshStandardMaterial({color:c})
 );
 m.position.set(x,y,z);
 m.castShadow=true;
 car.add(m);
 voxels.push(m);
}

// chassis
for(let x=-3;x<=3;x++)
for(let z=-7;z<=7;z++)
for(let y=0;y<=1;y++)
 v(x,y,z,0x0033ff);

// hood slope
for(let x=-2;x<=2;x++)
for(let z=-7;z<=-4;z++)
 v(x,2,z,0x0044ff);

// cabin
for(let x=-2;x<=2;x++)
for(let z=-2;z<=2;z++)
for(let y=2;y<=4;y++)
 v(x,y,z,0x0055ff);

// roof
for(let x=-1;x<=1;x++)
for(let z=-1;z<=1;z++)
 v(x,5,z,0x0077ff);

// windows
for(let x=-2;x<=2;x++){
 v(x,3,3,0x88ffff);
 v(x,3,-3,0x88ffff);
}

// lights
v(-2,2,-8,0xffffaa); v(2,2,-8,0xffffaa);
v(-2,2,8,0xff0000); v(2,2,8,0xff0000);

// wheels
const wg=new THREE.CylinderGeometry(0.7,0.7,1,8);
const wm=new THREE.MeshStandardMaterial({color:0});
const wheels=[];
[[-3,0,-5],[3,0,-5],[-3,0,5],[3,0,5]].forEach(p=>{
 let w=new THREE.Mesh(wg,wm);
 w.rotation.z=Math.PI/2;
 w.position.set(...p);
 car.add(w); wheels.push(w);
});

// ===== AI CARS =====
const aiCars=[];
function aiCar(x,z){
 let g=new THREE.Group();
 for(let i=0;i<40;i++){
  let p=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),
   new THREE.MeshStandardMaterial({color:0xff2222})
  );
  p.position.set((Math.random()-0.5)*4,0,(Math.random()-0.5)*8);
  g.add(p);
 }
 g.position.set(x,1,z);
 scene.add(g);
 aiCars.push({mesh:g,vx:0,vz:0});
}
for(let i=0;i<30;i++) aiCar(rand(-1000,1000),rand(-1000,1000));

// ===== PHYSICS =====
let vx=0,vz=0,ang=0,crash=0;
const keys={};
onkeydown=e=>keys[e.key]=1;
onkeyup=e=>keys[e.key]=0;

// ===== BREAKABLE PIXELS (CONTACT POINT) =====
const debris=[];
function breakAt(x,y,z,force){
 for(let i=0;i<20;i++){
  let p=new THREE.Mesh(new THREE.BoxGeometry(0.8,0.8,0.8),
   new THREE.MeshStandardMaterial({color:0xffaa00})
  );
  p.position.set(x,y,z);
  p.userData={
   vx:(Math.random()-0.5)*force,
   vy:Math.random()*force,
   vz:(Math.random()-0.5)*force,
   life:1
  };
  scene.add(p);
  debris.push(p);
 }
}

// ===== CAMERA SPRING =====
const camVel=new THREE.Vector3();
function camUpdate(){
 let target=new THREE.Vector3(
  car.position.x-Math.sin(ang)*25,
  car.position.y+12,
  car.position.z-Math.cos(ang)*25
 );
 camVel.lerp(target.sub(cam.position),0.05);
 cam.position.add(camVel.multiplyScalar(0.1));
 cam.lookAt(car.position.x,car.position.y+3,car.position.z);
}

// ===== LOOP =====
function loop(){
 requestAnimationFrame(loop);

 if(keys["w"]) {vx+=Math.sin(ang)*0.03; vz+=Math.cos(ang)*0.03;}
 if(keys["s"]) {vx-=Math.sin(ang)*0.02; vz-=Math.cos(ang)*0.02;}
 if(keys["a"]) ang+=0.04;
 if(keys["d"]) ang-=0.04;

 vx*=0.98; vz*=0.98;
 let sp=Math.sqrt(vx*vx+vz*vz);

 car.position.x+=vx;
 car.position.z+=vz;
 car.rotation.y=ang;
 wheels.forEach(w=>w.rotation.x-=sp);

 // AI move
 aiCars.forEach(ai=>{
  ai.vx+=(Math.random()-0.5)*0.002;
  ai.vz+=(Math.random()-0.5)*0.002;
  ai.mesh.position.x+=ai.vx;
  ai.mesh.position.z+=ai.vz;
 });

 // collision with AI (contact point!)
 aiCars.forEach(ai=>{
  let dx=ai.mesh.position.x-car.position.x;
  let dz=ai.mesh.position.z-car.position.z;
  let d=Math.sqrt(dx*dx+dz*dz);
  if(d<6 && sp>0.2){
   crash++;
   let cx=car.position.x+dx*0.5;
   let cz=car.position.z+dz*0.5;
   breakAt(cx,2,cz,0.5);
   vx*=-0.5; vz*=-0.5;
  }
 });

 // debris physics
 debris.forEach((p,i)=>{
  p.userData.vy-=0.02;
  p.position.x+=p.userData.vx;
  p.position.y+=p.userData.vy;
  p.position.z+=p.userData.vz;
  p.userData.life-=0.01;
  if(p.userData.life<=0){
   scene.remove(p);
   debris.splice(i,1);
  }
 });

 camUpdate();
 document.getElementById("spd").innerText=Math.floor(sp*140);
 document.getElementById("cr").innerText=crash;

 r.render(scene,cam);
}
loop();

onresize=()=>{
 cam.aspect=innerWidth/innerHeight;
 cam.updateProjectionMatrix();
 r.setSize(innerWidth,innerHeight);
};

</script>
</body>
</html>
"""

st.components.v1.html(GAME, height=1000, scrolling=False)
