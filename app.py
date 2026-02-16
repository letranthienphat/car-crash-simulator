import streamlit as st

st.set_page_config(page_title="Voxel City Crash Simulator", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header {display:none;}
.stApp {background:black; padding:0;}
.block-container {padding:0 !important; max-width:100% !important;}
</style>
""", unsafe_allow_html=True)

GAME_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Voxel City Crash Simulator</title>
<style>
body{margin:0;overflow:hidden;background:black;}
canvas{width:100vw;height:100vh;image-rendering:pixelated;}
#ui{
position:absolute;top:10px;left:10px;
color:#00ffff;font-family:monospace;
background:rgba(0,0,0,0.6);
padding:10px;border:2px solid cyan;border-radius:10px;
}
</style>
</head>
<body>

<div id="ui">SPEED: <span id="spd">0</span> | CRASH: <span id="cr">0</span></div>
<canvas id="c"></canvas>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const canvas = document.getElementById("c");
const renderer = new THREE.WebGLRenderer({canvas, antialias:false});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio,2));

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050015);

const camera = new THREE.PerspectiveCamera(65, innerWidth/innerHeight,0.1,2000);

// LIGHTS
scene.add(new THREE.AmbientLight(0x404060));
const sun = new THREE.DirectionalLight(0xffffff,1.4);
sun.position.set(50,80,50);
sun.castShadow=true;
scene.add(sun);

// ===== GROUND =====
const ground = new THREE.Mesh(
 new THREE.PlaneGeometry(1000,1000),
 new THREE.MeshStandardMaterial({color:0x0c0c12})
);
ground.rotation.x=-Math.PI/2;
scene.add(ground);

// ===== ROADS =====
const roadMat = new THREE.MeshStandardMaterial({color:0x202020});
for(let i=-400;i<=400;i+=80){
 let r1 = new THREE.Mesh(new THREE.PlaneGeometry(800,20),roadMat);
 r1.rotation.x=-Math.PI/2;
 r1.position.z=i;
 scene.add(r1);

 let r2 = new THREE.Mesh(new THREE.PlaneGeometry(20,800),roadMat);
 r2.rotation.x=-Math.PI/2;
 r2.position.x=i;
 scene.add(r2);
}

// ===== CITY BUILDINGS =====
function building(x,z,w,h,d,c){
 let b = new THREE.Mesh(
  new THREE.BoxGeometry(w,h,d),
  new THREE.MeshStandardMaterial({color:c})
 );
 b.position.set(x,h/2,z);
 b.castShadow=true;
 b.receiveShadow=true;
 scene.add(b);
}
for(let i=0;i<120;i++){
 building(
  (Math.random()-0.5)*800,
  (Math.random()-0.5)*800,
  10+Math.random()*30,
  20+Math.random()*200,
  10+Math.random()*30,
  0x111122 + Math.random()*0x333333
 );
}

// ===== PLAYER VOXEL CAR =====
const car = new THREE.Group();
scene.add(car);
const voxels=[];

function voxel(x,y,z,color){
 let m = new THREE.Mesh(
  new THREE.BoxGeometry(1,1,1),
  new THREE.MeshStandardMaterial({color})
 );
 m.position.set(x,y,z);
 m.castShadow=true;
 car.add(m);
 voxels.push(m);
}

// chassis
for(let x=-3;x<=3;x++)
for(let z=-6;z<=6;z++)
for(let y=0;y<=1;y++)
 voxel(x,y,z,0x0044ff);

// hood slope
for(let x=-2;x<=2;x++)
for(let z=-6;z<=-4;z++)
 voxel(x,2,z,0x0055ff);

// cabin
for(let x=-2;x<=2;x++)
for(let z=-2;z<=2;z++)
for(let y=2;y<=4;y++)
 voxel(x,y,z,0x0066ff);

// roof
for(let x=-1;x<=1;x++)
for(let z=-1;z<=1;z++)
 voxel(x,5,z,0x0088ff);

// windows
for(let x=-2;x<=2;x++){
 voxel(x,3,3,0x88ffff);
 voxel(x,3,-3,0x88ffff);
}

// lights
voxel(-2,2,-7,0xffffaa);
voxel(2,2,-7,0xffffaa);
voxel(-2,2,7,0xff0000);
voxel(2,2,7,0xff0000);

// wheels
const wheelGeo = new THREE.CylinderGeometry(0.7,0.7,1,8);
const wheelMat = new THREE.MeshStandardMaterial({color:0x000000});
const wheels=[];
[[ -3,0,-5],[3,0,-5],[-3,0,5],[3,0,5]].forEach(p=>{
 let w=new THREE.Mesh(wheelGeo,wheelMat);
 w.rotation.z=Math.PI/2;
 w.position.set(p[0],p[1],p[2]);
 car.add(w);
 wheels.push(w);
});

// ===== AI CARS =====
const aiCars=[];
function createAICar(x,z,color){
 let g=new THREE.Group();
 for(let i=0;i<25;i++){
  let p=new THREE.Mesh(
   new THREE.BoxGeometry(1,1,1),
   new THREE.MeshStandardMaterial({color})
  );
  p.position.set((Math.random()-0.5)*4,0,(Math.random()-0.5)*8);
  g.add(p);
 }
 g.position.set(x,1,z);
 scene.add(g);
 aiCars.push({mesh:g,vx:0,vz:0});
}
for(let i=0;i<20;i++){
 createAICar((Math.random()-0.5)*600,(Math.random()-0.5)*600,0xff3333);
}

// ===== BREAKABLE VOXELS =====
const broken=[];
function breakVoxel(v,force){
 car.remove(v);
 scene.add(v);
 v.userData={
  vx:(Math.random()-0.5)*force,
  vy:Math.random()*force,
  vz:(Math.random()-0.5)*force,
  life:1
 };
 broken.push(v);
}

// ===== PHYSICS =====
let vx=0,vz=0,angle=0;
let speed=0;
let crashes=0;
let shake=0;

// input
const keys={};
onkeydown=e=>keys[e.key]=true;
onkeyup=e=>keys[e.key]=false;

// ===== CAMERA SYSTEM =====
const camTarget = new THREE.Vector3();
function updateCamera(){
 camTarget.set(
  car.position.x - Math.sin(angle)*25,
  car.position.y + 12,
  car.position.z - Math.cos(angle)*25
 );
 camera.position.lerp(camTarget,0.05);
 camera.lookAt(car.position.x,car.position.y+3,car.position.z);

 if(shake>0){
  camera.position.x+=(Math.random()-0.5)*shake;
  camera.position.y+=(Math.random()-0.5)*shake;
  shake*=0.9;
 }
}

// ===== LOOP =====
function loop(){
 requestAnimationFrame(loop);

 // driving
 if(keys["w"]){vx+=Math.sin(angle)*0.03; vz+=Math.cos(angle)*0.03;}
 if(keys["s"]){vx-=Math.sin(angle)*0.015; vz-=Math.cos(angle)*0.015;}
 if(keys["a"]) angle+=0.035;
 if(keys["d"]) angle-=0.035;

 vx*=0.98; vz*=0.98;
 speed=Math.sqrt(vx*vx+vz*vz);

 car.position.x+=vx;
 car.position.z+=vz;
 car.rotation.y=angle;

 wheels.forEach(w=>w.rotation.x-=speed);

 // AI driving
 aiCars.forEach(ai=>{
  let dx=car.position.x-ai.mesh.position.x;
  let dz=car.position.z-ai.mesh.position.z;
  let d=Math.sqrt(dx*dx+dz*dz);

  if(d<40){
   ai.vx -= dx/d*0.01;
   ai.vz -= dz/d*0.01;
  } else {
   ai.vx += (Math.random()-0.5)*0.002;
   ai.vz += (Math.random()-0.5)*0.002;
  }

  let sp=Math.sqrt(ai.vx*ai.vx+ai.vz*ai.vz);
  if(sp>0.25){ai.vx*=0.9; ai.vz*=0.9;}

  ai.mesh.position.x+=ai.vx;
  ai.mesh.position.z+=ai.vz;
  ai.mesh.rotation.y=Math.atan2(ai.vx,ai.vz);
 });

 // collision AI
 aiCars.forEach(ai=>{
  let dx=car.position.x-ai.mesh.position.x;
  let dz=car.position.z-ai.mesh.position.z;
  let d=Math.sqrt(dx*dx+dz*dz);
  if(d<6 && speed>0.2){
   crashes++;
   shake=0.6;
   for(let i=0;i<10;i++){
    let v=voxels[Math.floor(Math.random()*voxels.length)];
    if(v) breakVoxel(v,0.4);
   }
   vx*=-0.5; vz*=-0.5;
  }
 });

 // broken voxel physics
 broken.forEach((v,i)=>{
  v.userData.vy-=0.02;
  v.position.x+=v.userData.vx;
  v.position.y+=v.userData.vy;
  v.position.z+=v.userData.vz;
  v.userData.life-=0.01;
  if(v.userData.life<=0){
   scene.remove(v);
   broken.splice(i,1);
  }
 });

 updateCamera();

 // UI
 document.getElementById("spd").innerText=Math.floor(speed*120);
 document.getElementById("cr").innerText=crashes;

 renderer.render(scene,camera);
}
loop();

onresize=()=>{
 camera.aspect=innerWidth/innerHeight;
 camera.updateProjectionMatrix();
 renderer.setSize(innerWidth,innerHeight);
};
</script>
</body>
</html>
"""

st.components.v1.html(GAME_HTML, height=1000, scrolling=False)
