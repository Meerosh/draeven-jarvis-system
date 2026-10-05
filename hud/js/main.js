'use strict';
// Voice cast chosen by Semaj; IDs verified against the connected account.
const approvedVoiceCast={"lucien": {"name": "Callum", "id": "N2lVS1w4EtoT3dr4eOWO"}, "garrick": {"name": "Chris", "id": "iP95p4xoKVk53GoZ742B"}, "azrath": {"name": "George", "id": "JBFqnCBsd6RMkjVDRZzb"}, "vaelis": {"name": "Charlie", "id": "IKne3meq5aSn9XLyUdCD"}, "draeven": {"name": "Liam", "id": "TX3LPaxmHKxFdv7VOQHJ"}};
let characterSpeechId=null;
let activeCouncilAgent=null;
let healthState={};
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const snapshot = window.DRAEVEN_SNAPSHOT || {tasks: [], source: 'Unavailable', capturedAt: null};
const tasks = snapshot.tasks || [];
const escapeHTML = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateText = s => s ? new Date(s).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}) : 'Unavailable';
const council = [
{id:'lucien',name:'Lucien Voss',purpose:'Strategy & foresight',species:'Vampire',room:'The Candlelit Archive',position:0,quote:'Clarity before commitment.',description:'Lucien weighs opportunities, tests assumptions, and turns ambition into a considered plan. His domain is business direction, research, and the decisions that deserve your attention.',duties:['Business strategy and opportunity assessment','Research synthesis and decision preparation','Priorities, tradeoffs, and commercial focus']},
{id:'garrick',name:'Garrick Thorne',purpose:'Operations & delivery',species:'Werewolf',room:'The War Room',position:33.333,quote:'A promise deserves a finished task.',description:'Garrick keeps the work moving. He watches dependencies, brings blockers into the light, and keeps delivery grounded in what has actually been done.',duties:['Task coordination and dependencies','Production progress and blocker escalation','Delivery checks and follow-through']},
{id:'vaelis',name:'Vaelis Nightweave',purpose:'Creative & storytelling',species:'Dark fae',room:'The Moonlit Atelier',position:66.667,quote:'Make it unmistakably yours.',description:'Vaelis shapes the expression of your ideas: imagery, story, and language with a distinctive point of view. Your voice and approved creative direction remain his guide.',duties:['Visual concepts and advertising creative','Brand voice and storytelling','Creative review against approved source material']},
{id:'azrath',name:'Azrath Veyr',purpose:'Systems & automation',species:'Demon',room:'The Ember Forge',position:100,quote:'Strength is a system that holds.',description:'Azrath tends the machinery beneath the Citadel. He examines connections, automation, and failures, insisting that a working system be demonstrated rather than merely declared.',duties:['Integration health and diagnostics','Automation design and maintenance','Execution evidence and failure recovery']}
];
const businesses = [
{name:'Out & Legendary',icon:'♜',summary:'Product readiness & digital gifting',detail:'Your product work and launch preparation, drawn from saved priorities.',filter:'Out & Legendary'},
{name:'Wright Connector',icon:'◇',summary:'Reception & business communications',detail:'Receptionist workflows and service development. Call operation and provider health have not been verified by this preview.',filter:'Wright'},
{name:'SoulSmith',icon:'♟',summary:'Characters & production planning',detail:'Character production, print preparation, and business-model validation.',filter:'SoulSmith'},
{name:'Narrative Platform',icon:'▤',summary:'Stories & platform development',detail:'Platform planning and creative publishing preparation.',filter:'Narrative Platform'}
];
const viewInfo={overview:['AT YOUR COMMAND','The Citadel awaits, Semaj.','A clear view of your work. A council at your side.'],businesses:['YOUR ENTERPRISES','Build a realm that endures.','The next moves across your businesses.'],council:['THE INNER CIRCLE','Meet your Council.','Four distinct identities, each with a purpose.'],tasks:['YOUR PRIORITIES','Give the next move your attention.','Open items from the vault. A dated snapshot, not a live task service.'],messages:['CORRESPONDENCE','Know what deserves a reply.','Your future priority inbox, with honest connection status.'],vault:['THE ARCHIVE','Memory is part of the foundation.','A visible source for what this interface knows.']};
function showView(name){if(!viewInfo[name])name='overview'; $$('.view').forEach(e=>e.classList.toggle('active',e.id===name)); $$('[data-view]').forEach(e=>{e.classList.toggle('selected',e.dataset.view===name); if(e.dataset.view===name)e.setAttribute('aria-current','page');else e.removeAttribute('aria-current');});const info=viewInfo[name];if($('#eyebrow'))$('#eyebrow').textContent=info[0];if($('#page-title'))$('#page-title').textContent=info[1];if($('#page-subtitle'))$('#page-subtitle').textContent=info[2];if(location.hash!==`#${name}`)history.replaceState(null,'',`#${name}`);window.scrollTo({top:0,behavior:'instant'});}
function showDialog(html){$('#dialog-content').innerHTML=html; if(!$('#detail-dialog').open)$('#detail-dialog').showModal();}
function toast(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').classList.remove('visible'),6500);}
function card(a,index){return `<button class="agent-card" data-agent="${a.id}" aria-label="Meet ${a.name}, ${a.purpose}" style="--position:${a.position}%"><div class="agent-art" aria-hidden="true"></div><span class="agent-number">0${index+1} / THE COUNCIL</span><div class="agent-content"><h3>${a.name}</h3><p class="agent-purpose">${a.purpose}</p><div class="agent-status"><span>Connected to routing</span><span>↗</span></div></div></button>`;}
function openAgent(id){
 stopActivity();
 const a=council.find(a=>a.id===id);if(!a)return;
 const v=characterVoices[id];
 showDialog(`<div class="dialog-portrait" style="--position:${a.position}%" role="img" aria-label="Complete ${a.species} portrait of ${a.name}"></div><p class="eyebrow">${a.room}</p><h2>${a.name}</h2><p class="agent-purpose">${a.purpose}</p><p><em>“${a.quote}”</em></p><p>${a.description}</p><ul>${a.duties.map(d=>`<li>${d}</li>`).join('')}</ul><div class="dialog-controls"><button class="bronze-button" id="character-route">Work with ${a.name.split(' ')[0]}</button></div><section class="voice-controls"><p class="eyebrow">CHARACTER VOICE PREVIEW</p><p>${v.direction}</p><label for="character-voice">Available voice</label><select id="character-voice"></select><div class="dialog-controls"><button class="bronze-button" id="character-speak">Hear ${a.name.split(' ')[0]}</button><button class="bronze-button" id="character-stop">Stop voice</button></div><p id="character-voice-status" class="voice-status" role="status">ElevenLabs · ${approvedVoiceCast[id].name} · plays only when requested.</p><p class="muted">Your assigned ElevenLabs voice reads this scripted introduction. Playing it uses ElevenLabs credits.</p></section><div class="connection-row"><span>Council routing</span><span class="tag">CONNECTED</span></div>`);
 populateCharacterVoices(id);

 $('#character-speak').onclick=()=>speakCharacter(id);
 $('#character-stop').onclick=()=>{stopActivity();voiceStatus('Voice stopped.');};
 $('#character-route').onclick=()=>{activeCouncilAgent=id;$('#detail-dialog').close();$('#command-input').placeholder=`Ask ${a.name}…`;$('#command-input').focus();toast(`${a.name} will handle your next request.`);};
}
function renderTasks(){const search=$('#task-search').value.toLowerCase();const filter=$('#task-filter').value;const list=tasks.filter(t=>(!filter||t.business===filter)&&(`${t.text} ${t.business}`.toLowerCase().includes(search)));$('#task-list').innerHTML=list.length?list.map(t=>`<article class="task-card"><span class="task-symbol" aria-hidden="true">◇</span><div><small>${escapeHTML(t.business)} · OPEN IN SAVED NOTE</small><h3>${escapeHTML(t.text)}</h3></div></article>`).join(''):'<div class=\"panel spacious\"><h2>No matching priorities</h2><p>Try a different search or business filter.</p></div>';}
function showSources(){showDialog(`<p class="eyebrow">SOURCE & FRESHNESS</p><h2>A snapshot of your priorities.</h2><p>Source: <strong>${escapeHTML(snapshot.source)}</strong></p><p>Snapshot captured: ${dateText(snapshot.capturedAt)}<br>Source file modified: ${dateText(snapshot.sourceModifiedAt)}</p><p>${tasks.length} open task records were exported. Historical statements inside those notes are not independently verified live status.</p><p>This interface does not change the source note. Revenue, inbox, approval queue, and agent activity are not connected.</p>`);}
async function connections(){
 await checkConnection();
 const services=healthState.services||{};const providers=healthState.providers||{};
 const ready=value=>value?.ready?'READY':'OFFLINE';
 showDialog('<p class="eyebrow">CONNECTIONS</p><h2>What is connected</h2>'+
 [['JARVIS Front Door',ready(services.frontdoor)],['Vault memory',ready(services.vault)],['Hermes / Laya',ready(services.laya)],['Wright local tools',ready(services.wright)],['Wright public tunnel',services.wright?.public_tunnel?'READY':'OFFLINE'],['Wright ElevenLabs tools',services.wright?.elevenlabs_tools?'READY':'SETUP REQUIRED'],['Council routing',services.frontdoor?.ready?'READY':'OFFLINE'],['ElevenLabs voice',ready(services.voice)],['OpenAI Images',providers.openai_images?.enabled?'READY':'DISABLED'],['Claude',providers.claude?.enabled?'READY':'DISABLED'],['Codex',providers.codex?.enabled?'READY':'DISABLED'],['Midjourney','MANUAL']].map(([name,status])=>`<div class="connection-row"><span>${escapeHTML(name)}</span><span>${escapeHTML(status)}</span></div>`).join('')+
 '<form id="openai-key-form" class="connection-setup"><p class="eyebrow">PRIVATE OPENAI CONNECTION</p><label for="openai-api-key">OpenAI secret API key</label><div class="connection-key-row"><input id="openai-api-key" name="api_key" type="password" autocomplete="new-password" spellcheck="false" placeholder="sk-…" required><button class="bronze-button" type="submit">SAVE PRIVATELY</button></div><p id="openai-key-status" class="connection-key-status" role="status">Checking secure storage…</p><p class="connection-key-help">The key is sent only to Draeven on this computer, stored by Windows Credential Manager, and never displayed again.</p></form>'+
 '<section class="connection-setup"><p class="eyebrow">WRIGHT TOOL AUTHENTICATION</p><p id="wright-token-status" class="connection-key-status" role="status">Checking secure storage…</p><button class="bronze-button" id="wright-token-generate" type="button">GENERATE PRIVATE TOOL TOKEN</button><div id="wright-token-once" hidden><label for="wright-token-value">Copy this token into ElevenLabs once</label><div class="connection-key-row"><input id="wright-token-value" type="password" readonly><button class="bronze-button" id="wright-token-copy" type="button">COPY</button></div><p class="connection-key-help">Header name: <strong>X-Draeven-Tool-Token</strong>. This value disappears when the window closes.</p></div></section>'+
 '<form class="connection-setup service-form" data-service="twilio"><p class="eyebrow">TWILIO PHONE ROUTING</p><p class="connection-key-status" data-service-status>Checking…</p><input name="account_sid" type="text" autocomplete="off" placeholder="Account SID" required><input name="auth_token" type="password" autocomplete="new-password" placeholder="Auth token" required><input name="from_number" type="tel" autocomplete="off" placeholder="Wright phone number, including country code" required><input name="owner_number" type="tel" autocomplete="off" placeholder="Private owner alert number (optional)"><button class="bronze-button" type="submit">VERIFY AND REPAIR ROUTE</button><p class="connection-key-help">Saved privately in Windows. Verification repairs this number to the ElevenLabs inbound route when needed.</p></form>'+
 '<form class="connection-setup service-form" data-service="shopify"><p class="eyebrow">SHOPIFY · OUT & LEGENDARY</p><p class="connection-key-status" data-service-status>Checking…</p><input name="store" type="text" autocomplete="off" value="0yku90-ad.myshopify.com" required><input name="client_id" type="text" autocomplete="off" placeholder="Integration app Client ID" required><input name="client_secret" type="password" autocomplete="new-password" placeholder="Integration app Client secret" required><button class="bronze-button" type="submit">SAVE AND VERIFY READ ACCESS</button><p class="connection-key-help">This verifies the store and product catalog without changing listings.</p></form>'+
 '<form class="connection-setup service-form" data-service="etsy"><p class="eyebrow">ETSY · OUTANDLEGENDARY</p><p class="connection-key-status" data-service-status>Checking…</p><input name="keystring" type="text" autocomplete="off" placeholder="App Keystring" required><input name="shared_secret" type="password" autocomplete="new-password" placeholder="Shared Secret" required><input name="shop_id" type="text" autocomplete="off" value="43843040" placeholder="Shop ID" required><button class="bronze-button" type="submit">SAVE AND VERIFY SHOP</button><p class="connection-key-help">This verifies the Etsy app and shop.</p></form>'+
 '<section class="connection-setup"><p class="eyebrow">ETSY PRIVATE AUTHORIZATION</p><p id="etsy-oauth-status" class="connection-key-status" role="status">Checking…</p><button class="bronze-button" id="etsy-oauth-start" type="button">AUTHORIZE ETSY SHOP</button><p class="connection-key-help">Etsy will open in a secure browser tab so you can approve Draeven for listings, shop settings, and order reading.</p></section>'+
 '<p>Draeven routes work through one provider at a time. Sending, publishing, purchasing, deletion, and locked decisions remain approval-gated.</p>');
 const form=document.getElementById('openai-key-form');
 const field=document.getElementById('openai-api-key');
 const status=document.getElementById('openai-key-status');
 const button=form?.querySelector('button[type="submit"]');
 fetch('/api/connections/openai',{cache:'no-store'}).then(r=>r.json()).then(data=>{status.textContent=data.configured?'OPENAI KEY · SAVED PRIVATELY':'OPENAI KEY · NOT CONFIGURED';}).catch(()=>{status.textContent='OPENAI KEY · STATUS UNAVAILABLE';});
 form?.addEventListener('submit',async event=>{
  event.preventDefault();
  const apiKey=field.value.trim();
  field.value='';
  button.disabled=true;
  status.textContent='Saving securely…';
  try{
   const response=await fetch('/api/connections/openai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:apiKey})});
   const data=await response.json();
   status.textContent=response.ok&&data.configured?'OPENAI KEY · SAVED PRIVATELY':(data.error||'The key could not be saved.');
  }catch(_error){status.textContent='Draeven could not reach secure storage.';}
  finally{button.disabled=false;}
 });
 const wrightStatus=document.getElementById('wright-token-status');
 const wrightGenerate=document.getElementById('wright-token-generate');
 fetch('/api/connections/wright',{cache:'no-store'}).then(r=>r.json()).then(data=>{wrightStatus.textContent=data.configured?'WRIGHT TOKEN · SAVED PRIVATELY':'WRIGHT TOKEN · NOT CONFIGURED';}).catch(()=>{wrightStatus.textContent='WRIGHT TOKEN · STATUS UNAVAILABLE';});
 wrightGenerate.onclick=async()=>{
  wrightGenerate.disabled=true;wrightStatus.textContent='Generating securely…';
  try{const response=await fetch('/api/connections/wright',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const data=await response.json();if(!response.ok)throw new Error(data.error||'Token generation failed.');document.getElementById('wright-token-value').value=data.token;document.getElementById('wright-token-once').hidden=false;wrightStatus.textContent='WRIGHT TOKEN · SAVED PRIVATELY';document.getElementById('wright-token-copy').onclick=async()=>{await navigator.clipboard.writeText(data.token);toast('Wright token copied.');};}catch(error){wrightStatus.textContent=error.message;wrightGenerate.disabled=false;}
 };
 const serviceForms=[...document.querySelectorAll('.service-form')];
 const refreshServices=()=>fetch('/api/connections/services',{cache:'no-store'}).then(r=>r.json()).then(data=>{
   serviceForms.forEach(form=>{const s=data[form.dataset.service]||{};const el=form.querySelector('[data-service-status]');el.textContent=s.verified?(form.dataset.service==='twilio'?(s.phone_route?'VERIFIED · ELEVENLABS ROUTE READY':'VERIFIED · PHONE ROUTE NEEDS REPAIR'):'VERIFIED · READ ACCESS READY'):(s.configured?'SAVED · VERIFICATION FAILED':'NOT CONFIGURED');});
 }).catch(()=>serviceForms.forEach(form=>form.querySelector('[data-service-status]').textContent='STATUS UNAVAILABLE'));
 refreshServices();
 const etsyOauthStatus=document.getElementById('etsy-oauth-status');
 const etsyOauthStart=document.getElementById('etsy-oauth-start');
 const refreshEtsyOauth=()=>fetch('/api/connections/services',{cache:'no-store'}).then(r=>r.json()).then(data=>{const etsy=data.etsy||{};etsyOauthStatus.textContent=etsy.private_access?'ETSY PRIVATE ACCESS · CONNECTED':(etsy.verified?'ETSY APP · READY FOR AUTHORIZATION':'SAVE AND VERIFY ETSY FIRST');});
 refreshEtsyOauth();
 etsyOauthStart.onclick=async()=>{
   etsyOauthStart.disabled=true;etsyOauthStatus.textContent='PREPARING ETSY AUTHORIZATION…';
   const popup=window.open('about:blank','draeven-etsy-oauth');
   try{const response=await fetch('/api/connections/etsy/authorize',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const data=await response.json();if(!response.ok)throw new Error(data.error||'Etsy authorization could not start.');if(popup)popup.location=data.url;else window.location.href=data.url;etsyOauthStatus.textContent='WAITING FOR ETSY APPROVAL…';let checks=0;const timer=setInterval(async()=>{checks++;await refreshEtsyOauth();const latest=await fetch('/api/connections/services',{cache:'no-store'}).then(r=>r.json()).catch(()=>({}));if(latest.etsy?.private_access||checks>=150){clearInterval(timer);etsyOauthStart.disabled=false;if(latest.etsy?.private_access)toast('Etsy private access connected.');}},2000);}
   catch(error){if(popup)popup.close();etsyOauthStatus.textContent=error.message;etsyOauthStart.disabled=false;}
 };
 serviceForms.forEach(form=>form.onsubmit=async event=>{
   event.preventDefault();const statusEl=form.querySelector('[data-service-status]');const button=form.querySelector('button[type="submit"]');button.disabled=true;statusEl.textContent='VERIFYING…';
   const values=Object.fromEntries(new FormData(form).entries());
   try{const response=await fetch('/api/connections/service',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({service:form.dataset.service,values}),signal:AbortSignal.timeout(30000)});const data=await response.json();if(!response.ok)throw new Error(data.error||'Connection failed.');form.reset();statusEl.textContent=form.dataset.service==='twilio'?'VERIFIED · ELEVENLABS ROUTE READY':'VERIFIED · READ ACCESS READY';if(form.dataset.service==='etsy')refreshEtsyOauth();toast(`${form.dataset.service.toUpperCase()} connection verified.`);}
   catch(error){statusEl.textContent=error.message;}
   finally{button.disabled=false;}
 });
}
$('#business-list').innerHTML=businesses.map((b,i)=>`<button class=\"business-row\" data-business="${i}"><span class=\"business-icon\">${b.icon}</span><div><h3>${b.name}</h3><small>${b.summary}</small></div><span class=\"arrow\">›</span></button>`).join('');
$('#business-detail-grid').innerHTML=businesses.map((b,i)=>`<article class=\"panel\"><p class=\"eyebrow\">${b.icon} YOUR ENTERPRISE</p><h2>${b.name}</h2><p>${b.detail}</p><div class=\"connection-row\"><span>Live business metrics</span><span class=\"tag\">NOT CONNECTED</span></div><button class=\"bronze-button\" data-business=\"${i}\">See saved priorities →</button></article>`).join('');
$('#council-grid').innerHTML=council.map(card).join('');$('#council-large').innerHTML=council.map(card).join('');
$('#task-count').textContent=window.DRAEVEN_SNAPSHOT?tasks.length:'—';if($('#task-nav-count'))$('#task-nav-count').textContent=tasks.length||'';
$('#focus-list').innerHTML=tasks.slice(0,2).map((t,i)=>`<button class=\"focus-item\" data-task="${i}"><small>${escapeHTML(t.business)}</small><strong>${escapeHTML(t.text.split(' — ')[0].split('. ')[0].slice(0,110))}${t.text.length>110?'…':''}</strong></button>`).join('')||'<p class=\"empty-title\">Task snapshot unavailable.</p>';
[...new Set(tasks.map(t=>t.business))].forEach(b=>{const o=document.createElement('option');o.value=b;o.textContent=b;$('#task-filter').appendChild(o);});
$('#task-source').textContent=`${tasks.length} open items · Snapshot captured ${dateText(snapshot.capturedAt)}`;
$('#snapshot-details').innerHTML=`<div class=\"connection-row\"><span>Source</span><span>${escapeHTML(snapshot.source)}</span></div><div class=\"connection-row\"><span>Captured</span><span>${dateText(snapshot.capturedAt)}</span></div><div class=\"connection-row\"><span>Open records</span><span>${tasks.length}</span></div>`;
if($('#footer-date'))$('#footer-date').textContent=`VAULT SNAPSHOT · ${snapshot.capturedAt?new Date(snapshot.capturedAt).toLocaleDateString():'UNAVAILABLE'}`;
$('#task-search').addEventListener('input',renderTasks);$('#task-filter').addEventListener('change',renderTasks);renderTasks();
document.addEventListener('click',e=>{const view=e.target.closest('[data-view],[data-go]');if(view)showView(view.dataset.view||view.dataset.go);const agent=e.target.closest('[data-agent]');if(agent)openAgent(agent.dataset.agent);const business=e.target.closest('[data-business]');if(business){const b=businesses[Number(business.dataset.business)];$('#task-filter').value='';$('#task-search').value=b.filter;renderTasks();showView('tasks');}const task=e.target.closest('[data-task]');if(task){const t=tasks[Number(task.dataset.task)];showDialog(`<p class=\"eyebrow\">SAVED PRIORITY · ${escapeHTML(t.business)}</p><h2>From your vault</h2><p>${escapeHTML(t.text)}</p><p>Source: ${escapeHTML(snapshot.source)}. No action has been executed.</p>`);}});
$('#dialog-close').onclick=()=>$('#detail-dialog').close();$('#detail-dialog').addEventListener('click',e=>{if(e.target===$('#detail-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
$('#connections-button').onclick=connections;if($('#source-button'))$('#source-button').onclick=showSources;
$('#download-snapshot').onclick=()=>{const blob=new Blob([JSON.stringify(snapshot,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='draeven-task-snapshot.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function clock(){if($('#clock'))$('#clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}clock();setInterval(clock,30000);
let reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;try{reduced=reduced||localStorage.getItem('draeven-reduced-motion')==='true';}catch{}function applyMotion(){document.body.classList.toggle('reduced-motion',reduced);const toggle=$('#motion-toggle');if(toggle){toggle.setAttribute('aria-pressed',String(reduced));toggle.textContent=reduced?'◌ Motion reduced':'◌ Reduce motion';}}applyMotion();if($('#motion-toggle'))$('#motion-toggle').onclick=()=>{reduced=!reduced;applyMotion();try{localStorage.setItem('draeven-reduced-motion',String(reduced));}catch{}};
let micStream=null,audioContext=null,raf=null,previewTimer=null,micRequest=0;
let voiceController=null, voiceEpoch=0, voiceListening=false, voiceSpeaking=false, lastReply='';
function setState(state,label,note){const presence=$('.presence');presence.classList.remove('state-listening','state-thinking','state-speaking');if(state!=='idle')presence.classList.add(`state-${state}`);$('#orb-stage').dataset.state=state;$('#state-label').textContent=label;$('#presence-note').textContent=note;}
let activeCharacterLine=null;
function stopActivity(){voiceEpoch++;if(voiceController)voiceController.stop();characterSpeechId=null;if(activeCharacterLine){activeCharacterLine.onstart=null;activeCharacterLine.onend=null;activeCharacterLine.onerror=null;activeCharacterLine=null;}$$('.agent-card.speaking').forEach(e=>e.classList.remove('speaking'));micRequest++;clearTimeout(previewTimer);if(window.speechSynthesis)window.speechSynthesis.cancel();if(micStream)micStream.getTracks().forEach(t=>t.stop());micStream=null;if(audioContext)audioContext.close().catch(()=>{});audioContext=null;cancelAnimationFrame(raf);$('#mic-button').classList.remove('active');$('#mic-button').setAttribute('aria-label','Talk to Draeven');$('#orb-stage').style.setProperty('--level',0);$$('.wave i').forEach(e=>e.style.height='');restorePresence();}
function preview(){showDialog('<p class=\"eyebrow\">INTERACTION PREVIEW</p><h2>Give Draeven a voice.</h2><p>Explore the visual states. The speaking sample uses a voice supplied by your browser; it is not Draeven’s final voice or a live AI reply.</p><div class=\"dialog-controls\"><button class=\"bronze-button\" id=\"preview-listen\">Listening animation</button><button class=\"bronze-button\" id=\"preview-think\">Thinking animation</button><button class=\"bronze-button\" id=\"preview-speak\">Speak a sample</button><button class=\"bronze-button\" id=\"preview-stop\">Stop</button></div><p>Use Talk in the command bar for speech recognition. Your browser may process speech online.</p>');$('#preview-listen').onclick=()=>{stopActivity();$('#detail-dialog').close();setState('listening','LISTENING · VISUAL PREVIEW','Demonstration state. The microphone is not active.');previewTimer=setTimeout(stopActivity,6000);};$('#preview-think').onclick=()=>{stopActivity();$('#detail-dialog').close();setState('thinking','THINKING · VISUAL PREVIEW','Demonstration state. No AI request is running.');previewTimer=setTimeout(stopActivity,6000);};$('#preview-speak').onclick=()=>{stopActivity();$('#detail-dialog').close();if(!window.speechSynthesis){toast('Browser speech is unavailable.');return;}const utterance=new SpeechSynthesisUtterance('Welcome to the Citadel, Semaj. Your priorities are gathered. Your council awaits. What would you have me do?');utterance.rate=.87;utterance.pitch=.8;const voices=speechSynthesis.getVoices();const voice=voices.find(v=>/David|Daniel|George|James/i.test(v.name)&&/^en/i.test(v.lang))||voices.find(v=>/^en/i.test(v.lang));if(voice)utterance.voice=voice;utterance.onstart=()=>setState('speaking','SPEAKING · BROWSER PREVIEW','Visual rhythm follows playback state, not audio amplitude.');utterance.onend=()=>stopActivity();utterance.onerror=()=>{stopActivity();toast('Speech playback ended or was unavailable.');};speechSynthesis.speak(utterance);};$('#preview-stop').onclick=()=>{stopActivity();$('#detail-dialog').close();};}
if($('#preview-button'))$('#preview-button').onclick=preview;

// JARVIS Front Door connection. Each question is independent; no fake session ID.
let isJarvisRequestPending = false;
let backendStatus = 'Checking JARVIS…';
const conversationContainer = $('#conversation-display');
const conversationPanel = $('.conversation-section');
const conversationToggle = $('#conversation-toggle');
function openConversation(){conversationPanel.classList.add('open');conversationPanel.setAttribute('aria-hidden','false');conversationToggle.textContent='Hide conversation';}
conversationToggle.onclick=()=>{const open=conversationPanel.classList.toggle('open');conversationPanel.setAttribute('aria-hidden',String(!open));conversationToggle.textContent=open?'Hide conversation':'Conversation';};
$('#conversation-close').onclick=()=>{conversationPanel.classList.remove('open');conversationPanel.setAttribute('aria-hidden','true');conversationToggle.textContent='Conversation';};
function displayMessage(role, text, provider = null) {
  const entry = document.createElement('div');
  entry.className = `conversation-entry role-${role}`;
  const label = document.createElement('div');
  label.className = 'message-label';
  label.textContent = role === 'user' ? 'You' : 'Draeven';
  if (provider && role === 'assistant') label.textContent += ` · ${provider}`;
  const body = document.createElement('div');
  body.className = 'message-body';
  body.textContent = text;
  entry.append(label, body);
  conversationContainer.appendChild(entry);
  conversationContainer.hidden = false;
  conversationContainer.scrollTop = conversationContainer.scrollHeight;
  openConversation();
}
function restorePresence() {
  if(voiceListening){setState('listening','LISTENING','Speak your question, then pause.');return;}
  if(voiceSpeaking){setState('speaking','DRAEVEN IS SPEAKING','Use Stop voice to interrupt.');return;}
  if (isJarvisRequestPending) {
    setState('thinking','CONSULTING JARVIS','Reading and preparing your answer. This can take a minute.');
  } else {
    setState('idle','AT REST',backendStatus);
  }
}
async function checkConnection() {
  try {
    const response = await fetch('/api/health', {signal:AbortSignal.timeout(8000)});
    const data = await response.json();
    healthState=data;
    const councilReady=Boolean(response.ok&&data.ok&&data.services?.frontdoor?.ready);
    if($('#council-connection'))$('#council-connection').textContent=councilReady?'Connected':'Offline';
    if($('#council-connection-note'))$('#council-connection-note').textContent=councilReady?'Four identities · provider routes ready':'Council routing unavailable';
    $('#council-routing-note').textContent=councilReady?'Council routing is connected. Lucien, Garrick, Vaelis, and Azrath each use their assigned provider route. Their work remains advice or drafts until you approve a real action.':'Council routing is currently unavailable.';
    backendStatus = response.ok && data.ok
      ? 'JARVIS service reachable · answers and drafts. Ask a question to verify a response.'
      : (data.error || 'JARVIS is offline. Open Draeven again to start it.');
  } catch {
    backendStatus = 'JARVIS is unreachable. Open Draeven again to start its services.';
  }
  $('#connection-status').textContent = backendStatus;
  if (!isJarvisRequestPending && $('#orb-stage').dataset.state === 'idle') restorePresence();
}
async function confirmAction(confirmId,button){
  button.disabled=true;button.textContent='Recording approval…';
  try{
    const response=await fetch('/api/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirm_id:confirmId}),signal:AbortSignal.timeout(735000)});
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||`Approval failed (${response.status}).`);
    displayMessage('assistant',data.reply,data.provider);
    const receipt=data.receipt;
    if(receipt)displayMessage('assistant',`Receipt ${receipt.id}: ${receipt.status}. Executed: ${receipt.executed?'yes':'no'}.`,'Evidence receipt');
    button.textContent='Approval recorded';
  }catch(error){button.disabled=false;button.textContent='Try confirmation again';toast(error.message);}
}
async function askJarvis(userInput) {
  if (isJarvisRequestPending) {toast('JARVIS is still answering. Please wait.');return;}
  stopActivity();
  const requestVoiceEpoch=voiceEpoch;
  let spokenAnswer=null;
  isJarvisRequestPending = true;
  $('#voice-status').textContent='JARVIS is preparing your answer. Voice will start when the text reply is ready.';
  $('.send-button').disabled = true;
  conversationContainer.setAttribute('aria-busy','true');
  restorePresence();
  const waitNotice=setTimeout(()=>{if(isJarvisRequestPending)toast('Still waiting for JARVIS. Your question is in progress.');},45000);
  try {
    displayMessage('user',userInput);
    const response=await fetch('/api/chat',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:userInput,agent:activeCouncilAgent}),signal:AbortSignal.timeout(735000)
    });
    const data=await response.json();
    if(!response.ok)throw new Error(data.error || `Request failed (${response.status}).`);
    if(typeof data.reply!=='string'||!data.reply.trim())throw new Error('JARVIS returned an empty answer.');
    displayMessage('assistant',data.reply,data.provider);
    if(activeCouncilAgent){activeCouncilAgent=null;$('#command-input').placeholder='Ask Draeven anything…';}
    lastReply=data.reply;$('#read-reply').disabled=false;spokenAnswer=data.reply;
    if(data.approval_required&&data.confirm_id){
      const entry=document.createElement('div');entry.className='conversation-entry role-assistant';
      entry.innerHTML='<div class="message-label">Approval optional</div><div class="message-body">Nothing will happen unless you confirm. You can clarify or revise your request without approving it.</div>';
      const controls=document.createElement('div');controls.className='dialog-controls';
      const approve=document.createElement('button');approve.className='bronze-button';approve.textContent='Confirm this action';approve.onclick=()=>confirmAction(data.confirm_id,approve);
      const clarify=document.createElement('button');clarify.className='bronze-button';clarify.textContent='Clarify or revise';clarify.onclick=()=>{stopActivity();entry.remove();const input=$('#command-input');input.placeholder='Clarify or revise your request…';input.focus();toast('No approval was given. Add the missing detail and send again.');};
      const dismiss=document.createElement('button');dismiss.className='bronze-button';dismiss.textContent='Cancel request';dismiss.onclick=()=>{entry.remove();toast('Request cancelled. Nothing was approved.');};
      controls.append(approve,clarify,dismiss);entry.appendChild(controls);conversationContainer.appendChild(entry);
    }
    backendStatus='JARVIS replied · answers and drafts. Each question is independent.';
    $('#connection-status').textContent=backendStatus;
  } catch(error) {
    const message=error.name==='TimeoutError'?'JARVIS timed out. It may still be finishing; check before retrying.':error.message;
    const stillWorking=/still answering|still preparing|please wait/i.test(message);
    displayMessage('assistant',message,stillWorking?'Still working':'Connection problem');
    backendStatus=stillWorking?'JARVIS is still preparing the current answer.':'The last request failed. Check Connections before retrying.';
    $('#connection-status').textContent=backendStatus;
  } finally {
    clearTimeout(waitNotice);
    isJarvisRequestPending=false;
    $('.send-button').disabled=false;
    conversationContainer.setAttribute('aria-busy','false');
    restorePresence();
    if(spokenAnswer && requestVoiceEpoch===voiceEpoch){
      if($('#speak-replies').checked && !document.hidden){
        voiceController.speak(spokenAnswer,$('#reply-voice').value);
      }else if(!$('#speak-replies').checked){
        $('#voice-status').textContent='Text reply ready. Enable Speak replies or click Read last reply.';
      }else{
        $('#voice-status').textContent='Text reply ready. Return to Draeven and click Read last reply.';
      }
    }
  }
}
checkConnection();

// CRITICAL FIX: explicit local command matching only
$('#command-form').addEventListener('submit', async e => {
  e.preventDefault();
  const input = $('#command-input');
  const text = input.value.trim();

  if (!text) return;
  if (isJarvisRequestPending) { toast('JARVIS is still answering. Your next question stays here.'); return; }
  input.value = '';

  // explicit local commands only
  if (/^\s*(stop|silence|cancel)\s*$/i.test(text)) {
    stopActivity();
    toast('Voice activity stopped.');
  } else if (/^\s*(show\s+)?tasks?\s*$/i.test(text)) {
    showView('tasks');
  } else if (/^\s*(show\s+|open\s+)council\s*$/i.test(text)) {
    showView('council');
  } else if (/^\s*(show\s+)?agents?\s*$/i.test(text)) {
    showView('council');
  } else if (/^\s*(show\s+)?businesses?\s*$/i.test(text)) {
    showView('businesses');
  } else if (/^\s*(show\s+)?(messages?|emails?|inbox)\s*$/i.test(text)) {
    showView('messages');
  } else if (/^\s*(show\s+)?(vault|archive)\s*$/i.test(text)) {
    showView('vault');
  } else if (/^\s*(show\s+)?(home|overview)\s*$/i.test(text)) {
    showView('overview');
  } else if (/^\s*(show\s+)?(connection|health|connections)\s*$/i.test(text)) {
    connections();
  } else if (/^\s*(show\s+)?(voice|preview)\s*$/i.test(text)) {
    preview();
  } else {
    const lowerText = text.toLowerCase();
    const agent = council.find(a => lowerText === a.name.split(' ')[0].toLowerCase());
    if (agent) {
      openAgent(agent.id);
    } else {
      await askJarvis(text);
    }
  }
});

document.addEventListener('visibilitychange',()=>{document.body.classList.toggle('page-hidden',document.hidden);if(document.hidden)stopActivity();});window.addEventListener('pagehide',stopActivity);window.addEventListener('hashchange',()=>showView(location.hash.slice(1)));showView(location.hash.slice(1)||'overview');

const characterVoices={
 lucien:{rate:.84,pitch:.72,direction:'Vampire · a measured, aristocratic baritone. Calm precision, with room between the words.',preferred:/George|Daniel|Ryan|David/i,text:'I am Lucien Voss. Before we commit your time or your resources, we will understand the opportunity. Bring me the decision. I will bring you clarity.'},
 garrick:{rate:.93,pitch:.55,direction:'Werewolf · grounded, deep, and direct. A rugged delivery with purposeful momentum.',preferred:/David|Guy|Mark|James/i,text:'Garrick Thorne. Give me the objective, and we will get the work moving. Every blocker brought into the light. Every promise followed through.'},
 vaelis:{rate:.88,pitch:.98,direction:'Elven dark fae · smooth, lyrical, and deliberate. Lighter resonance without losing masculine presence.',preferred:/Ryan|Daniel|Christopher|George/i,text:'I am Vaelis Nightweave. Your ideas deserve a voice and a shape that belong to you alone. Let us make something unmistakably yours.'},
 azrath:{rate:.77,pitch:.4,direction:'Demon · a low, deliberate bass. Weight and restraint rather than shouting or distortion.',preferred:/David|George|Guy|Mark/i,text:'Azrath Veyr. I tend the forge beneath the Citadel. We will know what is connected, what has failed, and what has truly been done.'}
};
function voiceStatus(text){const el=$('#character-voice-status');if(el)el.textContent=text;}
function populateCharacterVoices(id){
 const el=$('#character-voice');if(!el)return;
 const assigned=approvedVoiceCast[id];
 el.replaceChildren(new Option('ElevenLabs · '+assigned.name,'eleven:'+assigned.id,true,true));
 el.disabled=true;
}
function speakCharacter(id){
 stopActivity();
 characterSpeechId=id;
 voiceStatus('Preparing '+approvedVoiceCast[id].name+' through ElevenLabs…');
 voiceController.speak(characterVoices[id].text,'eleven:'+approvedVoiceCast[id].id);
}
$('#detail-dialog').addEventListener('close',()=>{if(characterSpeechId||activeCharacterLine)stopActivity();});
// Click-to-talk and spoken responses share the same tested text request path.
voiceController=createDraevenVoice(window,{
 status:text=>{$('#voice-status').textContent=text;if(characterSpeechId)voiceStatus(text);},
 listening:active=>{voiceListening=active;$('#mic-button').classList.toggle('active',active);$('#mic-button').textContent=active?'Cancel':'Talk';$('#mic-button').setAttribute('aria-label',active?'Cancel listening':'Talk to Draeven');restorePresence();},
 speaking:active=>{voiceSpeaking=active;$$('.agent-card.speaking').forEach(e=>e.classList.remove('speaking'));if(active&&characterSpeechId)$$('[data-agent="'+characterSpeechId+'"]').forEach(e=>e.classList.add('speaking'));restorePresence();},
 transcript:text=>{if(isJarvisRequestPending){$('#voice-status').textContent='JARVIS is busy. Please try again after the reply.';return;}$('#command-input').value=text;$('#command-form').requestSubmit();}
});
$('#mic-button').onclick=()=>{
 if(isJarvisRequestPending){toast('JARVIS is still answering. Please wait.');return;}
 if(!voiceListening && $('#command-input').value.trim()){toast('Send or clear your typed question before using Talk.');return;}
 if(voiceListening){voiceController.listen();return;}
 openConversation();stopActivity();voiceController.listen();
};
let pushToTalkHeld=false;
const typingTarget=target=>target?.matches?.('input, textarea, select, button, [contenteditable="true"]');
document.addEventListener('keydown',event=>{
 if(event.code!=='Space'||event.repeat||typingTarget(event.target)||document.querySelector('dialog[open]'))return;
 event.preventDefault();
 if(pushToTalkHeld||isJarvisRequestPending||voiceSpeaking)return;
 if($('#command-input').value.trim()){toast('Send or clear your typed question before using push to talk.');return;}
 pushToTalkHeld=true;openConversation();stopActivity();voiceController.listen();
});
document.addEventListener('keyup',event=>{
 if(event.code!=='Space'||!pushToTalkHeld)return;
 event.preventDefault();pushToTalkHeld=false;voiceController.finishListening();
});
window.addEventListener('blur',()=>{if(pushToTalkHeld){pushToTalkHeld=false;voiceController.stop();}});
$('#stop-voice').onclick=()=>{stopActivity();$('#voice-status').textContent=isJarvisRequestPending?'Voice stopped. JARVIS is still preparing the text answer.':'Voice stopped. Click Talk when ready.';};
$('#read-reply').onclick=()=>{if(lastReply){stopActivity();voiceController.speak(lastReply,$('#reply-voice').value);}};
try{const saved=localStorage.getItem('draeven-speak-replies');$('#speak-replies').checked=saved===null?true:saved==='true';}catch{$('#speak-replies').checked=true;}
$('#speak-replies').onchange=()=>{
 const enabled=$('#speak-replies').checked;
 try{localStorage.setItem('draeven-speak-replies',String(enabled));}catch{}
 if(!enabled){
   stopActivity();
   $('#voice-status').textContent='Automatic speech is off. Click Read last reply to hear a response.';
 }else{
   $('#voice-status').textContent='Automatic speech is on. Draeven will speak the next reply.';
 }
};
let voiceListGeneration=0;
async function populateReplyVoices(){
 const generation=++voiceListGeneration;
 const select=$('#reply-voice');const provider=$('#voice-provider').value;
 let previous=provider==='eleven'?'eleven:'+approvedVoiceCast.draeven.id:'';try{previous=localStorage.getItem('draeven-reply-voice-'+provider)||previous;}catch{}
 select.replaceChildren(new Option(provider==='eleven'?'Choose an ElevenLabs voice':'Browser default',provider==='eleven'?'eleven:':''));
 if(provider==='eleven'){
   $('#voice-status').textContent='Loading ElevenLabs voices…';
   try{
     const response=await fetch('/api/voice/voices',{signal:AbortSignal.timeout(65000)});const data=await response.json();
     if(generation!==voiceListGeneration)return;
     if(!response.ok)throw new Error(data.error||'Could not load voices.');
     data.voices.forEach(v=>{const labels=Object.values(v.labels||{}).join(', ');select.add(new Option(v.name+(labels?' · '+labels:''),'eleven:'+v.id));});
     $('#voice-status').textContent='Voices matching deep, calm and masculine descriptions appear first. Choose one, then click Test voice (uses credits).'+(data.has_more?' Showing the first 100 account voices.':'');
   }catch(error){if(generation===voiceListGeneration)$('#voice-status').textContent=error.message;}
 }else{
   const voices=window.speechSynthesis?speechSynthesis.getVoices().filter(v=>/^en/i.test(v.lang)):[];
   voices.forEach(v=>select.add(new Option(v.name,v.voiceURI)));
 }
 if(generation===voiceListGeneration && [...select.options].some(o=>o.value===previous))select.value=previous;
}
$('#voice-provider').onchange=()=>{stopActivity();try{localStorage.setItem('draeven-voice-provider',$('#voice-provider').value);}catch{}populateReplyVoices();};
$('#reply-voice').onchange=()=>{stopActivity();try{localStorage.setItem('draeven-reply-voice-'+$('#voice-provider').value,$('#reply-voice').value);}catch{}};
$('#test-reply-voice').onclick=()=>{stopActivity();voiceController.speak('Semaj, I am Draeven. I am here, and ready when you are.',$('#reply-voice').value);};
// Apply the approved casting once per browser; subsequent deliberate changes persist.
$('#voice-provider').value='eleven';
try{
 if(localStorage.getItem('draeven-cast-version')!=='2026-10-03-five-voices'){
   localStorage.setItem('draeven-voice-provider','eleven');
   localStorage.setItem('draeven-reply-voice-eleven','eleven:'+approvedVoiceCast.draeven.id);
   localStorage.setItem('draeven-cast-version','2026-10-03-five-voices');
 }
 $('#voice-provider').value=localStorage.getItem('draeven-voice-provider')||'eleven';
}catch{}
populateReplyVoices();
if(window.speechSynthesis)speechSynthesis.addEventListener('voiceschanged',()=>{if($('#voice-provider').value==='browser')populateReplyVoices();});
if(!voiceController.recognitionSupported)$('#voice-status').textContent='Speech recognition is unavailable here. Open Draeven in Chrome or Edge, or type your question.';
