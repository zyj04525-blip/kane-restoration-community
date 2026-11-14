'use strict';
const canvas=document.getElementById('screen'),g=canvas.getContext('2d');
const arena=new KaneArena({layers:[],animations:{}},new Map());
arena.start({name:'贡献者'});
function text(value,x,y,color='#dce7ee',size=16){g.fillStyle=color;g.font=`${size}px system-ui`;g.textAlign='left';g.fillText(value,x,y);}
arena.draw=function(g){
 const s=this.s,p=s.player;g.fillStyle='#172330';g.fillRect(0,0,960,560);
 g.strokeStyle='#2d4152';g.lineWidth=1;
 for(let y=337;y<=440;y+=26){g.beginPath();g.moveTo(45,y);g.lineTo(915,y);g.stroke();}
 for(let x=55;x<930;x+=85){g.beginPath();g.moveTo(x,337);g.lineTo(x,440);g.stroke();}
 for(const f of s.fx){
  if(f.skill){const m=KaneBattle.skills[f.key],a=f.x+m.near*f.face,b=f.x+m.far*f.face;g.fillStyle='#6fbad319';g.fillRect(Math.min(a,b),f.y-m.lane,Math.abs(b-a),m.lane*2);g.strokeStyle='#6fbad3';g.strokeRect(Math.min(a,b),f.y-m.lane,Math.abs(b-a),m.lane*2);text(f.key.toUpperCase(),Math.min(a,b)+4,f.y-m.lane-5,'#8ed5ed');}
  if(f.kind==='damage')text(String(f.amount),f.x,f.y-f.t*45,f.hurt?'#ff9687':'#ffe4a0',22);
 }
 if(p.attack){const m=KaneBattle.moves[p.attack.move];g.strokeStyle='#83d8ff';g.strokeRect(p.face>0?p.x:p.x-m.range,p.y-29,m.range,58);}
 for(const actor of [p,...s.enemies].sort((a,b)=>a.y-b.y)){
  if(actor.hp<=0&&actor.dead===0)continue;
  const player=actor===p;g.fillStyle=player?'#75c6f2':'#dfba72';g.fillRect(actor.x-14,actor.y-56-(actor.z||0),28,56);
  text(actor.face>0?'→':'←',actor.x-9,actor.y-64-(actor.z||0),player?'#75c6f2':'#dfba72',22);
  text(player?'玩家':'敌人',actor.x-18,actor.y+24);
  if(actor.windup>0)text('攻击准备',actor.x-34,actor.y-100,'#ff9687');
 }
 text('逻辑调试视图 · 非原版美术 / 非原版数值',24,35,'#9cb2c2');
 text(`生命 ${p.hp}/${p.maxHp}     法力 ${Math.floor(p.mp)}/${p.maxMp}     连击 ${s.combo}`,24,75);
 if(s.noticeTTL>0)text(s.notice,24,112,'#8ed5ed');
 if(s.paused||s.outcome){g.fillStyle='#09121cc9';g.fillRect(250,200,470,90);text(s.paused?'已暂停':s.outcome==='victory'?'逻辑演示：胜利':'逻辑演示：失败',300,250,'#fff',26);}
};
const skillButtons=[];
for(const [key,skill] of Object.entries(KaneBattle.skills)){
 const button=document.createElement('button');button.textContent=`${key.toUpperCase()} ${skill.name}`;button.dataset.key='Key'+key.toUpperCase();button.dataset.skill=key;document.getElementById('skills').append(button);skillButtons.push(button);
}
function togglePause(){arena.pause(!arena.s.paused);sync();}
function reset(){arena.start({name:'贡献者'});sync();canvas.focus();}
function sync(){
 const s=arena.s;document.getElementById('readout').textContent=`玩家生命 ${s.player.hp} · 法力 ${Math.floor(s.player.mp)} · 敌人生命 ${s.enemies[0].hp} · ${s.paused?'已暂停':s.outcome||'运行中'}`;
 document.getElementById('pause').textContent=s.paused?'继续':'暂停';
 for(const b of skillButtons){const k=b.dataset.skill,m=KaneBattle.skills[k],cd=Math.ceil(s.player.cooldowns[k]||0);b.textContent=`${k.toUpperCase()} ${m.name}${cd?' · '+cd+'s':''}`;b.setAttribute('aria-disabled',String(!!cd||s.paused||!!s.outcome||s.player.mp<m.cost));}
}
document.getElementById('pause').onclick=togglePause;document.getElementById('restart').onclick=reset;
for(const b of document.querySelectorAll('[data-key]')){
 b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);arena.input(b.dataset.key,true);});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(event,()=>arena.input(b.dataset.key,false));
 b.addEventListener('click',e=>{if(e.detail===0){arena.input(b.dataset.key,true);arena.input(b.dataset.key,false);}});
}
window.addEventListener('keydown',e=>{
 if(e.code==='Escape'){if(!e.repeat)togglePause();e.preventDefault();}
 else if(e.code==='KeyR'){if(!e.repeat)reset();e.preventDefault();}
 else if(arena.input(e.code,true,e.repeat))e.preventDefault();
});
window.addEventListener('keyup',e=>{if(arena.input(e.code,false))e.preventDefault();});
window.addEventListener('blur',()=>{arena.pause(true);sync();});
document.addEventListener('visibilitychange',()=>{if(document.hidden){arena.pause(true);sync();}});
let readoutAt=0;
function frame(now){arena.frame(g,now);if(now-readoutAt>100){sync();readoutAt=now;}requestAnimationFrame(frame);}
sync();requestAnimationFrame(frame);
