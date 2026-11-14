'use strict';
const $=id=>document.getElementById(id), canvas=$('screen'), ctx=canvas.getContext('2d',{alpha:false});
const spiritNames={sea:'海之轻语',blade:'刀锋之傲',assassin:'绯红刺灵'};
const sceneNames={welcome:'本机入口',battle:'圣杯长廊实时战斗',create:'创建角色',comic0:'开场漫画（一）',comic1:'开场漫画（二）',comic2:'开场漫画（三）',tutorial:'新手场景',home:'我的家',town:'树心广场', 'town-dialog':'初次对话','town-after':'后续对话',splash:'正在进入游戏','loading-role':'正在创建角色'};
const profile={gender:'male',appearance:0,spirit:'sea',name:''};
const state={scene:'welcome',preview:'male0',motion:!matchMedia('(prefers-reduced-motion: reduce)').matches,epoch:performance.now(),ready:false,token:0};
const assets=new Map(),animations=new Map();let manifest,lastFocus,raf=0,saved=null,arena=null,battleBadge='';
const packedNode=document.getElementById('entry-data'),packed=packedNode?JSON.parse(packedNode.textContent):null;
function status(text){$('status').textContent=text;}
function image(name){if(assets.has(name))return Promise.resolve(assets.get(name));return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{assets.set(name,im);resolve(im)};im.onerror=()=>reject(new Error('无法载入画面：'+name));im.src=packed?packed.images[name+'.webp']:name.startsWith('combat/')?'../playable/assets-v6/'+name.slice(7)+'.webp':'assets/'+name+'.webp';});}
function readSaved(){try{const p=JSON.parse(localStorage.getItem('kane-entry-profile-v1'));if(p&&p.version===1&&['male','female'].includes(p.gender)&&Number.isInteger(p.appearance)&&p.appearance>=0&&p.appearance<=2&&p.spirit in spiritNames&&typeof p.name==='string'&&p.name.trim()&&p.name.length<=12)return p;}catch{}return null;}
function save(){saved={version:1,...profile};try{localStorage.setItem('kane-entry-profile-v1',JSON.stringify(saved));$('resume').hidden=false;return true;}catch{return false;}}
function checkpoint(scene){if(!saved||saved.name!==profile.name)return;try{localStorage.setItem('kane-entry-checkpoint-v2',JSON.stringify({name:profile.name,scene}));}catch{}}
function resumeScene(){try{const c=JSON.parse(localStorage.getItem('kane-entry-checkpoint-v2'));if(c?.name===profile.name&&['comic0','comic1','comic2','battle'].includes(c.scene))return c.scene;}catch{}return 'battle';}
function listSpirits(){return state.preview==='blade'?['sea','blade','assassin']:['sea','blade','assassin'].includes(state.preview)?state.preview==='sea'?['blade','sea','assassin']:['sea','assassin','blade']:['assassin','sea','blade'];}
function sync(){
 $('choices').hidden=state.scene!=='create';
 $('comic-controls').hidden=!state.scene.startsWith('comic');$('comic-back').hidden=!['comic1','comic2'].includes(state.scene);
 $('welcome').hidden=state.scene!=='welcome';$('battle-controls').hidden=state.scene!=='battle';$('touch-controls').hidden=state.scene!=='battle';$('skill-controls').hidden=state.scene!=='battle';
 $('continue-journey').hidden=!saved;$('new-journey').disabled=!state.ready;
 canvas.setAttribute('aria-label',(sceneNames[state.scene]||'原版界面')+'画面');
 $('motion').textContent='画面动画：'+(state.motion?'开':'关');$('motion').setAttribute('aria-pressed',String(state.motion));
 for(const sex of ['male','female'])$(sex).setAttribute('aria-pressed',String(profile.gender===sex));
 for(let i=0;i<3;i++){const b=$('appearance'+i);b.setAttribute('aria-pressed',String(profile.appearance===i));b.setAttribute('aria-disabled',String(profile.gender==='female'&&i>0));}
 listSpirits().forEach((s,i)=>{$('spirit'+i).setAttribute('aria-label','选择'+spiritNames[s]);$('spirit'+i).setAttribute('aria-pressed',String(profile.spirit===s));});
 document.querySelectorAll('[data-scene]').forEach(b=>b.setAttribute('aria-current',b.dataset.scene===state.scene?'page':'false'));
 $('primary').disabled=!state.ready||['splash','loading-role'].includes(state.scene);
 $('primary').textContent=['splash','loading-role'].includes(state.scene)?'正在进入游戏':state.scene==='create'?'进入游戏':state.scene.startsWith('comic')?'下一页':state.scene==='town'?'查看初次对话':state.scene==='town-dialog'?'收起对话':state.scene==='tutorial'?'查看我的家':state.scene==='home'?'查看树心广场':'返回创建角色';
 if(state.scene==='welcome')$('primary').textContent='创建角色';
 if(state.scene==='battle'){$('primary').textContent=arena?.s?.outcome==='victory'?'查看我的家':'重新挑战';$('battle-pause').textContent=arena?.s?.paused?'继续战斗':'暂停战斗';}
}
function describe(){
 if(state.scene==='welcome'){status('本机入口已接好；原版登录外观仍待补。'+(saved?'已存角色：'+saved.name+'。':'')+'当前可玩斗灵：海之轻语。');return;}
 if(state.scene==='battle'){status('WASD 走位 · 双击 A/D 冲刺 · J 连击 · H/U/N/I/O 技能 · L 必杀 · Esc 暂停 · R 重试。本场实装海之轻语。');return;}
 if(state.scene==='create'){
   let text=`${profile.gender==='male'?'男':'女'} · 外观 ${profile.appearance+1} · ${spiritNames[profile.spirit]}。点击画面中的头像切换，进入游戏后取名。`;
   if(profile.spirit!=='sea')text+=' 此斗灵目前仅能预览，战斗暂使用海之轻语。';
   const obstruction=manifest?.frames[state.preview]?.obstruction;if(obstruction)text+=' 此预览仍有原录像字幕遮挡。';
   status(text);
 }else status(sceneNames[state.scene]+(profile.name?' · 已保存角色：'+profile.name:'')+(state.scene==='tutorial'?'。此处是界面核对，战斗尚未接入。':['home','town','town-dialog','town-after'].includes(state.scene)?'。目前保留录像中的人物与界面，尚未接入走位。':''));
}
function render(){
 if(state.scene==='battle'&&arena){arena.frame(ctx,performance.now());const s=arena.s;const badge=[s.player.hp,Math.floor(s.player.mp),s.enemies[0].hp,s.combo,s.paused,s.outcome,s.player.cast?.key,...Object.values(s.player.cooldowns).map(Math.ceil)].join('|');if(badge!==battleBadge){battleBadge=badge;$('battle-readout').textContent=`生命 ${s.player.hp}/140 · 法力 ${Math.floor(s.player.mp)}/100 · 守卫 ${s.enemies[0].hp}/410 · 连击 ${s.combo}`+(s.outcome==='victory'?' · 挑战完成':s.outcome==='defeat'?' · 角色倒下':'');sync();for(const b of document.querySelectorAll('[data-skill]')){const k=b.dataset.skill,m=KaneBattle.skills[k],cd=Math.ceil(s.player.cooldowns[k]||0);b.textContent=k.toUpperCase()+' '+m.name+(cd?' · '+cd+'秒':'');b.setAttribute('aria-disabled',String(!!cd||s.player.mp<m.cost||!!s.player.cast));}}canvas.dataset.audioState=arena.audio?.context?.state||'unavailable';canvas.dataset.audioVoices=String(arena.audio?.active.size||0);canvas.dataset.audioReady=String(!!arena.audio?.ready);canvas.dataset.playerX=arena.s.player.x.toFixed(2);canvas.dataset.playerY=arena.s.player.y.toFixed(2);return;}
 const key=['create','loading-role'].includes(state.scene)?state.preview:state.scene==='welcome'?'splash':state.scene, still=assets.get(key);
 if(still)ctx.drawImage(still,0,0,960,560);
 const anim=animations.get(key);
 if(state.scene==='create'&&state.motion&&anim&&document.visibilityState==='visible'&&$('name-dialog').hidden){
   const index=Math.floor((performance.now()-state.epoch)/40)%anim.count;
   ctx.drawImage(anim.sheets[Math.floor(index/10)],index%10%5*960,Math.floor(index%10/5)*560,960,560,0,0,960,560);
 }
}
function tick(){render();raf=requestAnimationFrame(tick);}
function switchPreview(key){state.preview=key;state.epoch=performance.now();sync();describe();render();}
function closeName(){if($('name-dialog').hidden)return;$('name-dialog').hidden=true;$('shade').hidden=true;$('choices').inert=false;document.querySelector('nav').inert=false;$('primary').inert=false;lastFocus?.focus();}
function go(scene){if(scene==='battle')return enterBattle();return showScene(scene);}
async function enterBattle(){showScene('splash');const token=state.token;$('loading').hidden=false;$('progress').value=0;try{let done=0;const needed=['combat/arena',...arena.manifest.layers.map(r=>'combat/'+r.name)];await Promise.all(needed.map(async key=>{const im=await image(key);if(im.decode)await im.decode();if(token===state.token)$('progress').value=++done/needed.length*100;}));await new Promise(r=>setTimeout(r,350));if(token===state.token)showScene('battle');}catch(err){if(token===state.token){showScene('welcome');status('场景载入失败，请重试：'+err.message);}}}
function showScene(scene){++state.token;closeName();if(arena)arena.pause(true);state.scene=scene;state.epoch=performance.now();$('loading').hidden=true;if(scene==='battle'&&arena){arena.start(profile);battleBadge='';canvas.focus();}if(scene.startsWith('comic')||scene==='battle')checkpoint(scene);sync();describe();render();}
function askName(){if(!state.ready||state.scene!=='create')return;lastFocus=document.activeElement;$('name-dialog').hidden=false;$('shade').hidden=false;$('choices').inert=true;document.querySelector('nav').inert=true;$('primary').inert=true;$('nickname').value=profile.name;$('name-error').textContent='';$('nickname').focus();}
for(const gender of ['male','female'])$(gender).onclick=()=>{profile.gender=gender;profile.appearance=0;switchPreview(gender+'0');};
for(let i=0;i<3;i++)$('appearance'+i).onclick=()=>{if(profile.gender==='female'&&i>0){status('这两种女性外观的大图尚未找齐，先保留原版头像，不用其他人物代替。');return;}profile.appearance=i;switchPreview(profile.gender+i);};
for(let i=0;i<3;i++)$('spirit'+i).onclick=()=>{profile.spirit=listSpirits()[i];switchPreview(profile.spirit);};
$('invite').onclick=()=>status('原邀请码功能依赖已关闭的服务器。本地界面不需要邀请码，也不会提交账号信息。');
$('enter').onclick=askName;$('cancel-name').onclick=closeName;
$('random-name').onclick=()=>{$('nickname').value=['光辉旅人','草原来客','风中的约定','归来的斗灵'][Math.floor(Math.random()*4)];$('nickname').focus();$('name-error').textContent='';};
$('name-dialog').onsubmit=async e=>{
 e.preventDefault();const name=$('nickname').value.trim();
 if(!name||!/[\p{L}\p{N}]/u.test(name)||/[<>\x00-\x1f]/.test(name)){$('name-error').textContent='请填写含文字或数字的名字';$('nickname').focus();return;}
 profile.name=name;const persisted=save();closeName();go('loading-role');const token=state.token;$('loading').hidden=false;$('progress').value=0;
 const next=['comic0','comic1','comic2','tutorial','home','town','town-dialog'];
 try{let done=0;await Promise.all(next.map(async key=>{await image(key);if(token===state.token)$('progress').value=++done/next.length*100;}));
   // The loading screen follows actual image readiness, with only a short readable dwell.
   await new Promise(r=>setTimeout(r,450));if(token!==state.token)return;go('comic0');if(!persisted)status('名字已用于本次浏览；浏览器未允许保存，关闭后不会保留。');
 }catch(err){if(token!==state.token)return;$('loading').hidden=true;go('create');status(err.message+'，请刷新后重试。');}
};
$('name-dialog').addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();closeName();}if(e.key==='Tab'){const f=[$('nickname'),$('random-name'),$('confirm-name'),$('cancel-name')];const i=f.indexOf(document.activeElement);if(e.shiftKey&&i===0){e.preventDefault();f.at(-1).focus();}else if(!e.shiftKey&&i===f.length-1){e.preventDefault();f[0].focus();}}});
$('primary').onclick=()=>{if(state.scene==='create')return askName();if(state.scene==='battle')return go(arena.s.outcome==='victory'?'home':'battle');const next={welcome:'create',comic0:'comic1',comic1:'comic2',comic2:'battle',tutorial:'battle',home:'town',town:'town-dialog','town-dialog':'town'};go(next[state.scene]||'create');};
$('comic-skip').onclick=()=>go('battle');$('comic-next').onclick=()=>$('primary').click();$('comic-back').onclick=()=>go(state.scene==='comic2'?'comic1':'comic0');
document.querySelectorAll('[data-scene]').forEach(b=>b.onclick=()=>{if(state.ready)go(b.dataset.scene);});
$('motion').onclick=()=>{state.motion=!state.motion;state.epoch=performance.now();sync();render();};
$('resume').onclick=()=>{saved=readSaved();if(!saved){$('resume').hidden=true;status('没有可用的本地角色记录，请重新取名。');return;}Object.assign(profile,{gender:saved.gender,appearance:saved.appearance,spirit:saved.spirit,name:saved.name});state.preview=profile.gender+profile.appearance;go(resumeScene());};
$('new-journey').onclick=()=>{if(state.ready)go('create');};$('continue-journey').onclick=()=>$('resume').click();
$('battle-restart').onclick=()=>go('battle');$('battle-pause').onclick=()=>{arena.pause(!arena.s.paused);sync();canvas.focus();};
canvas.addEventListener('pointerdown',e=>{if(state.scene!=='battle'||!arena)return;const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*960/r.width,y=(e.clientY-r.top)*560/r.height;if(y>=499&&y<=540&&x>=332&&x<548){const k='huniol'[Math.floor((x-332)/36)];arena.input('Key'+k.toUpperCase(),true);arena.input('Key'+k.toUpperCase(),false);canvas.focus();}});
window.addEventListener('keydown',e=>{if(state.scene!=='battle'||!arena)return;if(e.code==='Escape'){if(!e.repeat){arena.pause(!arena.s.paused);sync();}e.preventDefault();return;}if(e.code==='KeyR'){if(!e.repeat)go('battle');e.preventDefault();return;}if(arena.input(e.code,true,e.repeat))e.preventDefault();});
window.addEventListener('keyup',e=>{if(state.scene==='battle'&&arena&&arena.input(e.code,false))e.preventDefault();});
window.addEventListener('blur',()=>{if(state.scene==='battle'&&arena){arena.pause(true);sync();}});
document.querySelectorAll('[data-key]').forEach(b=>{b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);arena.input(b.dataset.key,true);};b.onpointerup=b.onpointercancel=()=>arena.input(b.dataset.key,false);});
document.addEventListener('visibilitychange',()=>{cancelAnimationFrame(raf);if(document.visibilityState==='hidden'&&state.scene==='battle'&&arena){arena.pause(true);sync();}if(document.visibilityState==='visible'){state.epoch=performance.now();tick();}});
async function loadAnimations(){for(const [key,record] of Object.entries(manifest.animations)){const sheets=[];try{for(const sheet of record.sheets)sheets.push(await image(sheet.file.replace(/\.webp$/,'')));animations.set(key,{sheets,count:record.times.length});}catch{ /* Static original frame remains available. */ }}}
async function init(){try{
 if(packed)manifest=packed.manifest;else{const response=await fetch('assets/manifest.json');if(!response.ok)throw new Error('画面目录载入失败');manifest=await response.json();}
 await image('male0');render();await Promise.all(Object.keys(manifest.frames).map(image));
 const cm=packed?packed.combatManifest:await (await fetch('../playable/assets-v6/manifest.json')).json();await Promise.all(['combat/arena',...cm.layers.map(r=>'combat/'+r.name)].map(image));arena=new KaneArena(cm,assets);arena.audio=null;$('battle-audio').textContent='原版音效待找回';$('battle-audio').disabled=true;
 state.ready=true;saved=readSaved();$('resume').hidden=!saved;sync();describe();tick();loadAnimations();
}catch(err){status(err.message+'。公开源码包不附第三方图片。请先按 docs/ASSETS.md 接入本地素材；无素材可打开 /demo/ 检查战斗逻辑。');}}
init();
