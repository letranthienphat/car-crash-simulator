import streamlit as st

st.set_page_config(page_title="Voxel Car Crash Simulator", layout="wide", initial_sidebar_state="collapsed")

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
<title>Voxel Crash Simulator</title>
<style>
body{margin:0;overflow:hidden;background:black;}
canvas{width:100vw;height:100vh;image-rendering:pixelated;}
#ui{
position:absolute;top:10px;left:10px;color:#0ff;
font-family:monospace;background:rgba(0,0,0,0.7);
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
scene.background = new THREE.Color(0x050010);

const camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight,0.1,1000);

// lights
scene.add(new THREE.AmbientLight(0x404040));
const sun = new THREE.DirectionalLight(0xffffff,1.5);
sun.position.set(20,30,10);
sun.castShadow=true;
scene.add(sun);

// ground
const ground = new THREE.Mesh(
 new THREE.PlaneGeometry(500,500),
 new THREE.MeshStandardMaterial({color:0x111122})
);
ground.rotation.x=-Math.PI/2;
scene.add(ground);

// ====== VOXEL CAR BUILDER ======
const car = new THREE.Group();
scene.add(car);

const voxels=[];

function addVoxel(x,y,z,color){
 const m = new THREE.Mesh(
  new THREE.BoxGeometry(1,1,1),
  new THREE.MeshStandardMaterial({color})
 );
 m.position.set(x,y,z);
 m.castShadow=true;
 car.add(m);
 voxels.push(m);
}

// body
for(let x=-3;x<=3;x++)
for(let z=-6;z<=6;z++)
for(let y=0;y<=1;y++)
 addVoxel(x,y,z,0x2277ff);

// roof
for(let x=-2;x<=2;x++)
for(let z=-2;z<=2;z++)
 addVoxel(x,2,z,0x3399ff);

// windows
for(let x=-2;x<=2;x++){
 addVoxel(x,2,3,0x88ffff);
 addVoxel(x,2,-3,0x88ffff);
}

// neon bottom
for(let x=-3;x<=3;x++)
 addVoxel(x,-1,-6,0xff00ff);

// wheels (simple)
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

// ====== PLAYER PHYSICS ======
let vx=0,vz=0,angle=0;
let speed=0;
let crashes=0;

// camera shake
let shake=0;

// ====== KEY INPUT ======
const keys={};
onkeydown=e=>keys[e.key]=true;
onkeyup=e=>keys[e.key]=false;

// ====== BREAK VOXELS ======
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

// ====== OBSTACLE ======
const obs = new THREE.Mesh(
 new THREE.BoxGeometry(10,5,10),
 new THREE.MeshStandardMaterial({color:0xff3300})
);
obs.position.set(20,2.5,0);
scene.add(obs);

// ====== LOOP ======
function loop(){
 requestAnimationFrame(loop);

 // drive
 if(keys["w"]){vx+=Math.sin(angle)*0.02;vz+=Math.cos(angle)*0.02;}
 if(keys["s"]){vx-=Math.sin(angle)*0.01;vz-=Math.cos(angle)*0.01;}
 if(keys["a"]) angle+=0.03;
 if(keys["d"]) angle-=0.03;

 vx*=0.98; vz*=0.98;
 speed=Math.sqrt(vx*vx+vz*vz);
 car.position.x+=vx;
 car.position.z+=vz;
 car.rotation.y=angle;

 // wheels spin
 wheels.forEach(w=>w.rotation.x-=speed);

 // CAMERA FOLLOW SMOOTH
 const targetCam = new THREE.Vector3(
  car.position.x,
  car.position.y+8,
  car.position.z+18
 );
 camera.position.lerp(targetCam,0.1);
 camera.lookAt(car.position);

 // SHAKE
 if(shake>0){
  camera.position.x+=(Math.random()-0.5)*shake;
  camera.position.y+=(Math.random()-0.5)*shake;
  shake*=0.9;
 }

 // COLLISION WITH OBSTACLE
 const dx=car.position.x-obs.position.x;
 const dz=car.position.z-obs.position.z;
 const dist=Math.sqrt(dx*dx+dz*dz);

 if(dist<8 && speed>0.1){
  crashes++;
  shake=0.5;
  // break voxels
  for(let i=0;i<5;i++){
   let v = voxels[Math.floor(Math.random()*voxels.length)];
   if(v) breakVoxel(v,0.3);
  }
  vx*=-0.4; vz*=-0.4;
 }

 // broken voxel physics
 broken.forEach((v,i)=>{
  v.userData.vy-=0.01;
  v.position.x+=v.userData.vx;
  v.position.y+=v.userData.vy;
  v.position.z+=v.userData.vz;
  v.userData.life-=0.01;
  if(v.userData.life<=0){
   scene.remove(v);
   broken.splice(i,1);
  }
 });

 // UI
 document.getElementById("spd").innerText=Math.floor(speed*100);
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
