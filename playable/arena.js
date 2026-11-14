(function(root){'use strict';
 class Arena{
  constructor(manifest,images){this.manifest=manifest;this.images=images;this.groups={};for(const r of manifest.layers)(this.groups[r.kind]??=[]).push(r);this.keys={};this.s=null;this.previous=0;this.accumulator=0;this.name='光辉旅人';}
  start(profile){this.audio?.stop();this.audio?.pause(false);this.name=profile.name||'光辉旅人';this.s=KaneBattle.create();this.keys={};this.previous=0;this.accumulator=0;}
  input(code,down,repeat=false){const map={KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',KeyW:'up',ArrowUp:'up',KeyS:'down',ArrowDown:'down',KeyJ:'attack',KeyH:'skill:h',KeyU:'skill:u',KeyN:'skill:n',KeyI:'skill:i',KeyO:'skill:o',KeyL:'skill:l'};const key=map[code];if(!key)return false;this.keys[key]=down;if(down&&!repeat){this.audio?.unlock();const previousCast=this.s.player.cast;KaneBattle.command(this.s,key);if(key.startsWith('skill:')&&this.s.player.cast&&this.s.player.cast!==previousCast)this.audio?.play(key.slice(6));}return true;}
  pause(value){if(this.s){this.s.paused=value;this.keys={};this.previous=0;this.accumulator=0;this.audio?.pause(value);}}
  frame(g,now){if(!this.s)return;const elapsed=this.previous?Math.min((now-this.previous)/1000,.1):0;this.previous=now;this.accumulator+=elapsed;
   while(this.accumulator>=1/120){KaneBattle.step(this.s,this.keys,1/120);this.audio?.events(this.s.events);if(this.s.outcome)this.audio?.stop();this.accumulator-=1/120;}this.draw(g);
  }
  sprite(g,kind,index,x,y,face=1,alpha=1){const list=this.groups[kind];if(!list?.length)return;const r=list[Math.max(0,Math.min(list.length-1,index))],im=this.images.get('combat/'+r.name);if(!im)return;
   g.save();g.translate(Math.round(x),Math.round(y));g.scale(face,1);g.globalAlpha=alpha;g.drawImage(im,-r.anchor[0],-r.anchor[1]);g.restore();
  }
  sample(kind,time){const list=this.groups[kind];if(!list?.length)return 0;const clip=this.manifest.animations[kind];let ms=Math.max(0,time*1000);if(clip?.loop)ms%=clip.duration_ms;let i=0;while(i+1<list.length&&list[i+1].at_ms<=ms+1e-6)i++;return i;}
  label(g,text,x,y,size=15,color='#ffe77f'){g.font=`bold ${size}px SimSun,serif`;g.textAlign='center';g.lineWidth=3;g.strokeStyle='#182017';g.strokeText(text,x,y);g.fillStyle=color;g.fillText(text,x,y);}
  draw(g){const s=this.s,p=s.player;g.drawImage(this.images.get('combat/arena'),0,0,960,560);
   const ultimate=s.fx.find(f=>f.key==='l');
   if(ultimate){g.fillStyle=`rgba(1,8,17,${Math.min(.88,ultimate.t*2,(ultimate.duration-ultimate.t)*2)})`;g.fillRect(0,0,960,478);}
   // Persistent ground fields are behind actors; airborne bursts overlay them.
   for(const f of s.fx)if(f.key==='i')this.sprite(g,f.kind,this.sample(f.kind,f.t),f.x,f.y,f.face);
   const actors=[{kind:'player',y:p.y},...s.enemies.map(e=>({kind:'guard',y:e.y,e}))].sort((a,b)=>a.y-b.y);
   for(const a of actors){if(a.kind==='player'){
     const alpha=p.invuln>0&&Math.floor(s.time*18)%2?.55:1;
     if(p.cast){const kind='cast-'+p.cast.key;this.sprite(g,kind,this.sample(kind,p.cast.time),p.x,p.y,p.face,alpha);}
     else if(p.attack){const kind='attack'+p.attack.move;this.sprite(g,kind,this.sample(kind,p.attack.time),p.x,p.y,p.face,alpha);}
     else{const kind=p.moving?'walk':'idle';this.sprite(g,kind,this.sample(kind,p.moving?p.stride:s.time),p.x,p.y,p.face,alpha);}
     this.label(g,this.name+' · 海之轻语',p.x,p.y+28,12,'#a9eb73');
    }else{const e=a.e;if(e.hp===0&&e.dead===0)continue;
     if(e.windup>0){g.save();g.strokeStyle='#ffae55';g.lineWidth=3;g.beginPath();g.ellipse(e.x+e.face*25,e.y+3,55,13,0,0,Math.PI*2);g.stroke();g.restore();}
     this.sprite(g,'guard',0,e.x,e.y-e.z,e.face===-1?1:-1,e.hp>0?1:e.dead/.65);
     if(e.hp>0){g.fillStyle='#15212be6';g.fillRect(e.x-43,e.y-e.z-171,86,7);g.fillStyle='#e3ad31';g.fillRect(e.x-42,e.y-e.z-170,84*e.hp/e.maxHp,5);}
    }}
   for(const f of s.fx){if(f.kind.startsWith('water')||(f.skill&&f.key!=='i'))this.sprite(g,f.kind,this.sample(f.kind,f.t),f.x,f.y,f.face);
    if(f.kind==='damage')this.label(g,String(f.amount),f.x,f.y-f.t*47,22,f.hurt?'#ff6c55':'#ffe95a');}
   // Dynamic values cover the digits in the recovered HUD without changing its outer layout.
   g.fillStyle='#7c1416';g.fillRect(276,503,40,18);this.label(g,String(p.hp),296,516,13,'#fff1b5');
   g.fillStyle='#243d70';g.fillRect(653,504,38,18);this.label(g,String(Math.floor(p.mp)),672,517,13,'#e9faff');
   Object.entries(KaneBattle.skills).forEach(([k,m],i)=>{const x=332+i*36,icon=this.images.get('combat/icon-'+k);g.fillStyle='#122332';g.fillRect(x,501,33,35);if(icon)g.drawImage(icon,x,501,33,34);else this.label(g,'必杀',x+16,517,11,'#c8f1ff');const cd=p.cooldowns[k]||0;if(cd>0||p.mp<m.cost){g.fillStyle='#08111bc4';g.fillRect(x,501,33,35);}if(cd>0)this.label(g,String(Math.ceil(cd)),x+16,520,18,'#fff1b0');this.label(g,k.toUpperCase(),x+26,534,11,'#ffe9a6');});
   g.fillStyle='#17222be8';g.fillRect(792,445,168,115);g.textAlign='left';g.font='13px Microsoft YaHei';g.fillStyle='#f3e8c8';g.fillText('WASD 走位 · J 连击',802,468);g.fillText('H U N I O 技能 · L 必杀',802,490);g.fillText('Esc 暂停 · R 重试',802,512);g.font='11px Microsoft YaHei';g.fillStyle='#aac1c6';g.fillText('录像复原 · 数值待校准',802,540);
   if(s.noticeTTL>0)this.label(g,s.notice,480,80,19,'#b4ecff');
   if(s.combo>1)this.label(g,s.combo+' 连击',235,140,31,'#6ecbff');
   g.fillStyle='#15232cd9';g.fillRect(10,13,280,38);this.label(g,'圣杯长廊 · 击败圣杯守卫',150,38,17,'#f5d88a');
   if(s.paused||s.outcome){g.fillStyle='#07131aa3';g.fillRect(0,0,960,560);this.label(g,s.paused?'已暂停':s.outcome==='victory'?'挑战完成':'再试一次',480,245,40);this.label(g,s.paused?'点击下方继续战斗':s.outcome==='victory'?'圣杯守卫已击败 · 可以重试或查看后续界面':'按 R 重新开始',480,290,16,'#f7f1df');}
  }
 }
 root.KaneArena=Arena;
})(globalThis);
