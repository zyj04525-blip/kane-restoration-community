const assert=require('node:assert/strict');
const E=require('./engine.js');
const advance=(s,n,input={},dt=1/120)=>{for(let i=0;i<n;i++)E.step(s,input,dt);};
const cases=[];
function test(name,fn){fn();cases.push(name);}
test('movement is simulated, frame-rate independent and bounded',()=>{
 const a=E.create(),b=E.create();advance(a,120,{right:true});advance(b,60,{right:true},1/60);
 assert.ok(Math.abs(a.player.x-385)<.00001);assert.ok(Math.abs(a.player.x-b.player.x)<.00001);
 advance(a,2400,{left:true});assert.equal(a.player.x,55);
});
test('distant and different-lane attacks do not damage targets',()=>{
 const a=E.create();E.command(a,'attack');advance(a,48);assert.equal(a.enemies[0].hp,410);
 const b=E.create();b.enemies[0].x=245;b.enemies[0].y=337;b.player.y=440;E.command(b,'attack');advance(b,36);assert.equal(b.enemies[0].hp,410);
});
test('one swing hits once, damages and knocks the guard back',()=>{
 const s=E.create();s.enemies[0].x=245;E.command(s,'attack');advance(s,54);
 assert.equal(s.enemies[0].hp,377);assert.equal(s.combo,1);assert.ok(s.enemies[0].x>245);
});
test('turning away prevents a hit behind the player',()=>{
 const s=E.create();s.enemies[0].x=245;s.player.face=-1;E.command(s,'attack');advance(s,54);assert.equal(s.enemies[0].hp,410);
});
test('pause prevents all game time, movement and damage',()=>{
 const s=E.create();s.paused=true;const before=JSON.stringify(s);E.command(s,'attack');advance(s,120,{right:true,attack:true});assert.equal(JSON.stringify(s),before);
});
test('double tapping direction starts a faster dash',()=>{
 const s=E.create();E.command(s,'right');advance(s,12);E.command(s,'right');const x=s.player.x;advance(s,12,{right:true});assert.ok(s.player.x-x>35);
});
test('guard windup can be avoided by moving away',()=>{
 const s=E.create();s.enemies[0].x=230;s.enemies[0].cooldown=0;advance(s,2);assert.ok(s.enemies[0].windup>0);advance(s,90,{left:true});assert.equal(s.player.hp,140);
});
test('guard can hit an idle player and cause defeat',()=>{
 const s=E.create();s.enemies[0].x=230;s.enemies[0].cooldown=0;advance(s,180);assert.ok(s.player.hp<140);advance(s,120*60);assert.equal(s.outcome,'defeat');
});
test('a controllable combat loop can reach victory',()=>{
 const s=E.create();
 for(let i=0;i<120*90&&!s.outcome;i++){
  const e=s.enemies[0],dx=e.x-s.player.x,dy=e.y-s.player.y;
  E.step(s,{right:dx>86,left:dx<-86,up:dy<-10,down:dy>10,attack:Math.abs(dx)<=105&&Math.abs(dy)<25},1/120);
 }
 assert.equal(s.outcome,'victory');assert.equal(s.kills,1);assert.ok(s.player.hp>0);
 const hp=s.player.hp;advance(s,600,{attack:true});assert.equal(s.player.hp,hp);
});
test('three gestures keep distinct source durations and the final splash can outlive the pose',()=>{
 const s=E.create();s.enemies[0].x=905;
 const started=[];let last=-1;
 for(let i=0;i<165;i++){
  E.step(s,{attack:true},1/120);
  if(s.player.attack&&s.player.attack.move!==last){last=s.player.attack.move;started.push({move:last,time:s.time});}
 }
 assert.deepEqual(started.slice(0,3).map(x=>x.move),[0,1,2]);
 assert.ok(Math.abs((started[1].time-started[0].time)-.4)<.025);
 assert.ok(Math.abs((started[2].time-started[1].time)-.40)<.025);
 assert.ok(s.fx.some(f=>f.kind==='water2'));
 assert.ok(s.fx.every(f=>f.x===170&&f.y===403));
});
test('water starts with the gesture, and damage waits for contact',()=>{
 const s=E.create();s.enemies[0].x=350;s.enemies[0].cooldown=10;
 E.command(s,'attack');E.step(s,{},1/120);
 assert.equal(s.fx[0].kind,'water0');assert.equal(s.enemies[0].hp,410);
 advance(s,20);assert.equal(s.enemies[0].hp,377);
});
test('all six skills spend mana once and cannot be spammed during a cast',()=>{
 for(const k of Object.keys(E.skills)){const s=E.create(),m=E.skills[k];E.command(s,'skill:'+k);assert.equal(s.player.cast.key,k);assert.equal(s.player.mp,100-m.cost);E.command(s,'skill:'+k);assert.equal(s.player.mp,100-m.cost);assert.equal(s.fx.filter(f=>f.skill).length,1);}
});
test('insufficient mana and paused state do not start or spend a skill',()=>{
 const s=E.create();s.player.mp=0;E.command(s,'skill:l');assert.equal(s.player.cast,null);assert.equal(s.fx.length,0);s.player.mp=100;s.paused=true;E.command(s,'skill:h');assert.equal(s.player.mp,100);assert.equal(s.player.cast,null);
});
test('skills have distinct delayed pulses and respect direction and lane',()=>{
 for(const k of ['h','u','n','o']){const s=E.create();s.enemies[0].x=350;s.enemies[0].cooldown=100;E.command(s,'skill:'+k);advance(s,10);assert.equal(s.enemies[0].hp,410);advance(s,350);assert.ok(s.enemies[0].hp<410,k);}
 const s=E.create();s.player.face=-1;s.enemies[0].x=350;E.command(s,'skill:h');advance(s,190);assert.equal(s.enemies[0].hp,410);
 const b=E.create();b.player.y=440;b.enemies[0].y=337;b.enemies[0].x=350;b.enemies[0].stun=10;E.command(b,'skill:u');advance(b,110);assert.equal(b.enemies[0].hp,410);
});
test('freeze field stays at its cast origin when the player moves away',()=>{
 const s=E.create();s.enemies[0].x=350;E.command(s,'skill:i');const f=s.fx[0];advance(s,60);const x=s.player.x;advance(s,90,{left:true});assert.ok(s.player.x<x);assert.equal(f.x,170);assert.equal(f.y,403);assert.ok(s.enemies[0].slow>0);
});
test('skill simulation is frame-rate independent and pause freezes cooldowns',()=>{
 const a=E.create(),b=E.create();for(const s of [a,b]){s.enemies[0].x=350;s.enemies[0].cooldown=100;E.command(s,'skill:u');}advance(a,120);advance(b,60,{},1/60);assert.equal(a.enemies[0].hp,b.enemies[0].hp);assert.ok(Math.abs(a.player.mp-b.player.mp)<.001);a.paused=true;const before=JSON.stringify(a);advance(a,120);assert.equal(JSON.stringify(a),before);
});
test('ultimate pulls targets and completes its full effect envelope',()=>{
 const s=E.create();s.enemies[0].x=450;s.enemies[0].cooldown=100;E.command(s,'skill:l');advance(s,210);assert.ok(s.enemies[0].x<450);assert.ok(s.player.cast);advance(s,380);assert.equal(s.player.cast,null);assert.ok(!s.fx.some(f=>f.key==='l'));assert.ok(s.enemies[0].hp<410);
});
test('cooldown prevents a second cast after recovery and ends in simulation time',()=>{
 const s=E.create();E.command(s,'skill:h');advance(s,90);const spent=s.player.mp;E.command(s,'skill:h');assert.equal(s.player.cast,null);assert.equal(s.player.mp,spent);advance(s,540);E.command(s,'skill:h');assert.equal(s.player.cast.key,'h');
});
console.log(JSON.stringify({passed:cases.length,cases},null,2));
