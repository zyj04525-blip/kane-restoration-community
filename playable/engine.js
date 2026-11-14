(function(root){
 'use strict';
 // Pose durations follow the observed 103.40–104.72s three-hit chain at 25fps.
 // Contact, damage, reach and knockback remain reconstruction estimates.
 const moves=[{duration:.40,contact:.12,damage:33,push:24,range:240,effect:.40},{duration:.40,contact:.12,damage:33,push:30,range:260,effect:.40},{duration:.52,contact:.20,damage:34,push:52,range:270,effect:.92}];
 // Observed order, pose/effect durations and qualitative behaviour come from the
 // official recordings/article. Costs, hit pulses, reach and damage are estimates.
 const skills={
  h:{name:'冰霜拳',cast:.56,duration:1.60,cooldown:5,cost:20,ticks:[.32,.60,.84,1.08],damage:18,near:70,far:380,lane:48,push:10,launch:260},
  u:{name:'水幕天华',cast:.72,duration:.88,cooldown:7,cost:20,ticks:[.20,.36,.52,.68],damage:17,near:90,far:410,lane:48,push:0},
  n:{name:'冰河时代',cast:.68,duration:2.88,cooldown:5,cost:30,ticks:[.88,1.12,1.36,1.60,1.84,2.08],damage:20,near:45,far:470,lane:88,push:2,launch:220},
  i:{name:'绝对零度',cast:.40,duration:3.28,cooldown:6,cost:20,ticks:[.28,.78,1.28,1.78,2.28,2.78],damage:6,near:-150,far:265,lane:60,push:0,freeze:.36,slow:1.1},
  o:{name:'冰晶爆裂',cast:.64,duration:1.72,cooldown:8,cost:30,ticks:[.36,.64,.96,1.28],damage:24,near:50,far:350,lane:54,push:8,launch:180},
  l:{name:'究级波浪',cast:4.76,duration:4.76,cooldown:20,cost:50,ticks:[1.48,1.76,2.04,2.32,2.60,2.88,3.16,3.44,3.72,4.08,4.36],damage:15,near:-340,far:340,lane:105,push:0,launch:170,pull:true}
 };
 const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
 function create(){return {time:0,outcome:null,paused:false,combo:0,comboTTL:0,sequence:0,chainTTL:0,queued:false,fx:[],events:[],kills:0,
  player:{x:170,y:403,z:0,vz:0,face:1,hp:140,maxHp:140,mp:100,maxMp:100,cooldowns:{},cast:null,attack:null,stun:0,invuln:0,stride:0,moving:false,dash:0},
  enemies:[{id:1,x:740,y:400,z:0,vz:0,face:-1,hp:410,maxHp:410,stun:0,windup:0,cooldown:1.1,dead:0}],
  lastTap:{left:-10,right:-10}};}
 function command(s,type){if(s.paused||s.outcome)return;
  if(type.startsWith('skill:')){const key=type.slice(6),m=skills[key],p=s.player;if(!m)return;
   if(p.cast||p.attack||p.stun>0){s.notice='动作尚未结束';s.noticeTTL=.8;return;}
   if((p.cooldowns[key]||0)>0){s.notice=m.name+' 正在冷却';s.noticeTTL=.8;return;}
   if(p.mp<m.cost){s.notice='法力不足';s.noticeTTL=1;return;}
   p.mp-=m.cost;p.cooldowns[key]=m.cooldown;p.cast={key,time:0};p.moving=false;s.queued=false;s.chainTTL=0;
   s.fx.push({kind:'skillfx-'+key,key,x:p.x,y:p.y,face:p.face,t:0,duration:m.duration,tick:0,skill:true});
   s.notice=m.name;s.noticeTTL=1;return;
  }
  if(type==='attack')s.queued=true;
  if(type==='left'||type==='right'){if(s.time-s.lastTap[type]<.24)s.player.dash=.65;s.lastTap[type]=s.time;}
 }
 function hit(s,e,move){e.hp=Math.max(0,e.hp-move.damage);e.x=clamp(e.x+(move.face||s.player.face)*move.push,45,915);e.stun=.31;e.windup=0;
  if(move.launch||(!move.skill&&s.sequence===2)){e.vz=move.launch||280;e.stun=.66;}s.combo++;s.comboTTL=2.2;
  s.fx.push({kind:'damage',x:e.x,y:e.y-150,amount:move.damage,t:0,duration:.72});
  s.events.push({type:'hit',target:e.id,damage:move.damage});
  if(e.hp===0){e.dead=.65;s.kills++;s.events.push({type:'kill',target:e.id});}
 }
 function step(s,input,dt){
  if(!Number.isFinite(dt)||dt<=0||dt>.05)throw new Error('invalid fixed simulation step');
  s.events=[];if(s.paused||s.outcome)return;s.time+=dt;const p=s.player;
  s.noticeTTL=Math.max(0,(s.noticeTTL||0)-dt);p.mp=Math.min(p.maxMp,p.mp+3*dt);
  for(const k of Object.keys(p.cooldowns))p.cooldowns[k]=Math.max(0,p.cooldowns[k]-dt);
  if(p.cast){p.cast.time+=dt;if(p.cast.time>=skills[p.cast.key].cast)p.cast=null;}
  s.comboTTL=Math.max(0,s.comboTTL-dt);if(!s.comboTTL)s.combo=0;
  s.chainTTL=Math.max(0,s.chainTTL-dt);p.stun=Math.max(0,p.stun-dt);p.invuln=Math.max(0,p.invuln-dt);p.dash=Math.max(0,p.dash-dt);
  if(!p.attack&&!p.cast&&input.attack&&p.stun<=0)s.queued=true;
  if(!p.attack&&!p.cast&&s.queued&&p.stun<=0){
   s.sequence=s.chainTTL>0?(s.sequence+1)%3:0;p.attack={time:0,hit:false,move:s.sequence};s.queued=false;p.moving=false;
   s.fx.push({kind:'water'+s.sequence,x:p.x,y:p.y,t:0,duration:moves[s.sequence].effect,face:p.face});
   s.events.push({type:'attack',move:s.sequence});
  }
  if(p.attack){const a=p.attack,m=moves[a.move];a.time+=dt;
   if(!a.hit&&a.time>=m.contact){a.hit=true;
    for(const e of s.enemies){const forward=(e.x-p.x)*p.face;if(e.hp>0&&forward>0&&forward<m.range&&Math.abs(e.y-p.y)<29&&e.z<85)hit(s,e,m);}
   }
   if(a.time>=m.duration){p.attack=null;s.chainTTL=.32;if(input.attack)s.queued=true;}
  }
  const wasMoving=p.moving;p.moving=false;
  if(!p.attack&&!p.cast&&p.stun<=0){let dx=(input.right?1:0)-(input.left?1:0),dy=(input.down?1:0)-(input.up?1:0);
   if(dx||dy){const normal=dx&&dy?Math.SQRT1_2:1;const speed=p.dash>0?365:215;p.x=clamp(p.x+dx*normal*speed*dt,55,905);p.y=clamp(p.y+dy*normal*speed*.52*dt,337,440);if(dx)p.face=dx;p.stride=wasMoving?p.stride+dt:0;p.moving=true;}
  }
  // Each cast owns a fixed world origin and its own pulse cursor. Walking away
  // cannot drag a placed field; multiple simulation steps cannot double-hit it.
  for(const f of s.fx.filter(f=>f.skill)){
   const m=skills[f.key];
   while(f.tick<m.ticks.length&&f.t+dt>=m.ticks[f.tick]){f.tick++;
    for(const e of s.enemies){const forward=(e.x-f.x)*f.face;
     if(e.hp<=0||forward<m.near||forward>m.far||Math.abs(e.y-f.y)>m.lane||e.z>360)continue;
     hit(s,e,{...m,face:f.face,skill:true});
     if(m.freeze)e.frozen=m.freeze;if(m.slow)e.slow=m.slow;
     if(m.pull)e.x=clamp(e.x+(f.x-e.x)*.12,45,915);
    }
   }
  }
  for(const e of s.enemies){
   e.frozen=Math.max(0,(e.frozen||0)-dt);e.slow=Math.max(0,(e.slow||0)-dt);
   if(e.z>0||e.vz>0){e.z=Math.max(0,e.z+e.vz*dt);e.vz-=880*dt;if(!e.z&&e.vz<0)e.vz=0;}
   if(e.hp<=0){e.dead=Math.max(0,e.dead-dt);continue;}
   e.face=p.x<e.x?-1:1;e.stun=Math.max(0,e.stun-dt);e.cooldown=Math.max(0,e.cooldown-dt);
   if(e.stun>0||e.z>0||e.frozen>0)continue;
   if(e.windup>0){e.windup-=dt;if(e.windup<=0){e.cooldown=1.0;
     if(Math.abs(e.x-p.x)<78&&Math.abs(e.y-p.y)<28&&p.invuln===0){p.hp=Math.max(0,p.hp-14);p.invuln=.65;p.stun=.18;p.attack=null;p.x=clamp(p.x+e.face*24,55,905);s.combo=0;s.comboTTL=0;
      s.fx.push({kind:'hurt',x:p.x,y:p.y-110,t:0,duration:.3});s.fx.push({kind:'damage',x:p.x,y:p.y-150,amount:14,t:0,duration:.65,hurt:true});s.events.push({type:'hurt',damage:14});}
    }continue;}
   const dx=p.x-e.x,dy=p.y-e.y;
   const slow=e.slow>0?.42:1;
   if(Math.abs(dx)>64)e.x=clamp(e.x+Math.sign(dx)*70*slow*dt,45,915);
   if(Math.abs(dy)>8)e.y+=Math.sign(dy)*40*slow*dt;
   if(Math.abs(dx)<73&&Math.abs(dy)<25&&e.cooldown===0)e.windup=.55;
  }
  for(const fx of s.fx)fx.t+=dt;s.fx=s.fx.filter(f=>f.t<f.duration);
  if(p.hp===0){s.outcome='defeat';s.events.push({type:'defeat'});}
  else if(s.enemies.every(e=>e.hp===0&&e.dead===0)){s.outcome='victory';s.events.push({type:'victory'});}
 }
 const api={create,command,step,moves,skills};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.KaneBattle=api;
})(typeof globalThis!=='undefined'?globalThis:this);
