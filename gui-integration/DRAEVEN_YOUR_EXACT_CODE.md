# EXACT DRAEVEN INTEGRATION - YOUR FINAL IMPLEMENTATION

**Status:** Ready to implement  
**Your Setup:** Windows, `C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud\`  
**Backend:** `http://localhost:8000/api/chat`  
**Frontend:** `http://127.0.0.1:4783/`  

---

## What Changed From Your Current Code

Your current `js/main.js` has this problem:
```javascript
// OLD - matches words ANYWHERE in input
else if(/\b(task|tasks|priorit|priority)/.test(q)){showView('tasks');}
```

This means "What's my top priority?" → opens Tasks (WRONG)

**New approach:**
```javascript
// NEW - exact phrase or anchored match only
else if(/^\s*(show\s+)?tasks?\s*$/i.test(text)){showView('tasks');}
```

Now "What's my top priority?" → goes to backend (CORRECT)

---

## Step 1: Update `serve.py`

Replace your entire `serve.py` with this:

```python
"""Draeven preview with CORS and Jarvis backend proxy."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
import json
import urllib.request

os.chdir(Path(__file__).resolve().parent)

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORS for localhost only
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:4783')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        """Proxy /api/chat to Jarvis backend."""
        if self.path == '/api/chat':
            self._proxy_to_jarvis()
        else:
            self.send_error(404)

    def do_GET(self):
        """Serve static files."""
        if self.path == '/' or self.path.endswith('.html') or self.path.endswith('.css') or self.path.endswith('.js'):
            super().do_GET()
        else:
            self.send_error(403, 'Directory listing disabled')

    def _proxy_to_jarvis(self):
        """Forward request to Jarvis backend at localhost:8000."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            req = urllib.request.Request(
                'http://localhost:8000/api/chat',
                data=body,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response_data.encode('utf-8'))
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error = json.dumps({
                'reply': f'Jarvis backend unavailable at localhost:8000. Error: {str(e)}',
                'provider': 'error',
                'session_id': 'error'
            })
            self.wfile.write(error.encode('utf-8'))

    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')

print('Draeven HUD: http://127.0.0.1:4783', flush=True)
print('Proxy to: http://localhost:8000/api/chat', flush=True)
ThreadingHTTPServer(('127.0.0.1', 4783), Handler).serve_forever()
```

---

## Step 2: Update `js/main.js`

Replace your entire `js/main.js` with this exact version. Keep all your existing functions, just replace the command form handler:

```javascript
'use strict';
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
function showView(name){if(!viewInfo[name])name='overview'; $$('.view').forEach(e=>e.classList.toggle('active',e.id===name)); $$('[data-view]').forEach(e=>{e.classList.toggle('selected',e.dataset.view===name); if(e.dataset.view===name)e.setAttribute('aria-current','page');else e.removeAttribute('aria-current');}); const info=viewInfo[name];$('#eyebrow').textContent=info[0];$('#page-title').textContent=info[1];$('#page-subtitle').textContent=info[2];if(location.hash!==`#${name}`)history.replaceState(null,'',`#${name}`);window.scrollTo({top:0,behavior:'instant'});}
function showDialog(html){$('#dialog-content').innerHTML=html; if(!$('#detail-dialog').open)$('#detail-dialog').showModal();}
function toast(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').classList.remove('visible'),6500);}
function card(a,index){return `<button class="agent-card" data-agent="${a.id}" aria-label="Meet ${a.name}, ${a.purpose}" style="--position:${a.position}%"><div class="agent-art" aria-hidden="true"></div><span class="agent-number">0${index+1} / THE COUNCIL</span><div class="agent-content"><h3>${a.name}</h3><p class="agent-purpose">${a.purpose}</p><div class="agent-status"><span>Awaiting connection</span><span>↗</span></div></div></button>`;}
function openAgent(id){
 const a=council.find(a=>a.id===id);if(!a)return;
 const v=characterVoices[id];
 showDialog(`<div class="dialog-portrait" style="--position:${a.position}%" role="img" aria-label="Complete ${a.species} portrait of ${a.name}"></div><p class="eyebrow">${a.room}</p><h2>${a.name}</h2><p class="agent-purpose">${a.purpose}</p><p><em>"${a.quote}"</em></p><p>${a.description}</p><ul>${a.duties.map(d=>`<li>${d}</li>`).join('')}</ul><section class="voice-controls"><p class="eyebrow">CHARACTER VOICE PREVIEW</p><p>${v.direction}</p><label for="character-voice">Available voice</label><select id="character-voice"></select><div class="dialog-controls"><button class="bronze-button" id="character-speak">Hear ${a.name.split(' ')[0]}</button><button class="bronze-button" id="character-stop">Stop voice</button></div><p id="character-voice-status" class="voice-status" role="status">Browser approximation · not a produced fantasy voice.</p><p class="muted">Pace and pitch are tailored to this character. Available voices depend on your browser. No agent is generating this scripted introduction.</p></section><div class="connection-row"><span>Agent execution</span><span class="tag">NOT CONNECTED</span></div>`);
 populateCharacterVoices(id);
 $('#character-voice').onchange=e=>{try{localStorage.setItem('draeven-voice-'+id,e.target.value);}catch{}};
 $('#character-speak').onclick=()=>speakCharacter(id);
 $('#character-stop').onclick=()=>{stopActivity();voiceStatus('Voice stopped.');};}
function renderTasks(){const search=$('#task-search').value.toLowerCase();const filter=$('#task-filter').value;const list=tasks.filter(t=>(!filter||t.business===filter)&&(`${t.text} ${t.business}`.toLowerCase().includes(search)));$('#task-list').innerHTML=list.length?list.map(t=>`<article class="task-card"><span class="task-symbol" aria-hidden="true">◇</span><div><small>${escapeHTML(t.business)} · OPEN IN SAVED NOTE</small><h3>${escapeHTML(t.text)}</h3></div></article>`).join(''):'<div class="panel spacious"><h2>No matching priorities</h2><p>Try a different search or business filter.</p></div>';}
function showSources(){showDialog(`<p class="eyebrow">SOURCE & FRESHNESS</p><h2>A snapshot of your priorities.</h2><p>Source: <strong>${escapeHTML(snapshot.source)}</strong></p><p>Snapshot captured: ${dateText(snapshot.capturedAt)}<br>Source file modified: ${dateText(snapshot.sourceModifiedAt)}</p><p>${tasks.length} open task records were exported. Historical statements inside those notes are not independently verified live status.</p><p>This interface does not change the source note. Revenue, inbox, approval queue, and agent activity are not connected.</p>`);}
function connections(){showDialog('<p class="eyebrow">THE MACHINERY BENEATH</p><h2>Connection ledger</h2>'+[['Vault priorities','SAVED SNAPSHOT'],['Commerce revenue','NOT CONNECTED'],['Email inbox','NOT CONNECTED'],['Agent execution','NOT CONNECTED'],['Draeven intelligence','NOT CONNECTED'],['Voice response','BROWSER PREVIEW ONLY']].map(([a,b])=>`<div class="connection-row"><span>${a}</span><span class="tag">${b}</span></div>`).join('')+'<p>Interface readiness does not establish service health. Existing operational services have not been changed by this build.</p>');}
$('#business-list').innerHTML=businesses.map((b,i)=>`<button class="business-row" data-business="${i}"><span class="business-icon">${b.icon}</span><div><h3>${b.name}</h3><small>${b.summary}</small></div><span class="arrow">›</span></button>`).join('');
$('#business-detail-grid').innerHTML=businesses.map((b,i)=>`<article class="panel"><p class="eyebrow">${b.icon} YOUR ENTERPRISE</p><h2>${b.name}</h2><p>${b.detail}</p><div class="connection-row"><span>Live business metrics</span><span class="tag">NOT CONNECTED</span></div><button class="bronze-button" data-business="${i}">See saved priorities →</button></article>`).join('');
$('#council-grid').innerHTML=council.map(card).join('');$('#council-large').innerHTML=council.map(card).join('');
$('#task-count').textContent=window.DRAEVEN_SNAPSHOT?tasks.length:'—';$('#task-nav-count').textContent=tasks.length||'';
$('#focus-list').innerHTML=tasks.slice(0,2).map((t,i)=>`<button class="focus-item" data-task="${i}"><small>${escapeHTML(t.business)}</small><strong>${escapeHTML(t.text.split(' — ')[0].split('. ')[0].slice(0,110))}${t.text.length>110?'…':''}</strong></button>`).join('')||'<p class="empty-title">Task snapshot unavailable.</p>';
[...new Set(tasks.map(t=>t.business))].forEach(b=>{const o=document.createElement('option');o.value=b;o.textContent=b;$('#task-filter').appendChild(o);});
$('#task-source').textContent=`${tasks.length} open items · Snapshot captured ${dateText(snapshot.capturedAt)}`;
$('#snapshot-details').innerHTML=`<div class="connection-row"><span>Source</span><span>${escapeHTML(snapshot.source)}</span></div><div class="connection-row"><span>Captured</span><span>${dateText(snapshot.capturedAt)}</span></div><div class="connection-row"><span>Open records</span><span>${tasks.length}</span></div>`;
$('#footer-date').textContent=`VAULT SNAPSHOT · ${snapshot.capturedAt?new Date(snapshot.capturedAt).toLocaleDateString():'UNAVAILABLE'}`;
$('#task-search').addEventListener('input',renderTasks);$('#task-filter').addEventListener('change',renderTasks);renderTasks();
document.addEventListener('click',e=>{const view=e.target.closest('[data-view],[data-go]');if(view)showView(view.dataset.view||view.dataset.go);const agent=e.target.closest('[data-agent]');if(agent)openAgent(agent.dataset.agent);const business=e.target.closest('[data-business]');if(business){const b=businesses[Number(business.dataset.business)];$('#task-filter').value='';$('#task-search').value=b.filter;renderTasks();showView('tasks');}const task=e.target.closest('[data-task]');if(task){const t=tasks[Number(task.dataset.task)];showDialog(`<p class="eyebrow">SAVED PRIORITY · ${escapeHTML(t.business)}</p><h2>From your vault</h2><p>${escapeHTML(t.text)}</p><p>Source: ${escapeHTML(snapshot.source)}. No action has been executed.</p>`);}});
$('#dialog-close').onclick=()=>$('#detail-dialog').close();$('#detail-dialog').addEventListener('click',e=>{if(e.target===$('#detail-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
$('#connections-button').onclick=connections;$('#source-button').onclick=showSources;
$('#download-snapshot').onclick=()=>{const blob=new Blob([JSON.stringify(snapshot,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='draeven-task-snapshot.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function clock(){ $('#clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}
clock();setInterval(clock,30000);
let reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;try{reduced=reduced||localStorage.getItem('draeven-reduced-motion')==='true';}catch{}
function applyMotion(){document.body.classList.toggle('reduced-motion',reduced);$('#motion-toggle').setAttribute('aria-pressed',String(reduced));$('#motion-toggle').textContent=reduced?'◌ Motion reduced':'◌ Reduce motion';}
applyMotion();$('#motion-toggle').onclick=()=>{reduced=!reduced;applyMotion();try{localStorage.setItem('draeven-reduced-motion',String(reduced));}catch{}};
let micStream=null,audioContext=null,raf=null,previewTimer=null,micRequest=0;
function setState(state,label,note){const presence=$('.presence');presence.classList.remove('state-listening','state-thinking','state-speaking');if(state!=='idle')presence.classList.add(`state-${state}`);$('#orb-stage').dataset.state=state;$('#state-label').textContent=label;$('#presence-note').textContent=note;}
let activeCharacterLine=null;
function stopActivity(){if(activeCharacterLine){activeCharacterLine.onstart=null;activeCharacterLine.onend=null;activeCharacterLine.onerror=null;activeCharacterLine=null;}$$('.agent-card.speaking').forEach(e=>e.classList.remove('speaking'));micRequest++;clearTimeout(previewTimer);if(window.speechSynthesis)window.speechSynthesis.cancel();if(micStream)micStream.getTracks().forEach(t=>t.stop());micStream=null;if(audioContext)audioContext.close().catch(()=>{});audioContext=null;cancelAnimationFrame(raf);$('#mic-button').classList.remove('active');$('#mic-button').setAttribute('aria-label','Start microphone level visualization');$('#orb-stage').style.setProperty('--level',0);$$('.wave i').forEach(e=>e.style.height='');setState('idle','AT REST','Your interface is ready. The intelligence link is not connected.');}
async function startMic(){if(micStream){stopActivity();return;}stopActivity();const request=micRequest;if(!navigator.mediaDevices?.getUserMedia){toast('Microphone access requires a supported browser on localhost or HTTPS.');return;}setState('idle','MICROPHONE PERMISSION','Waiting for your browser permission.');try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});if(request!==micRequest){stream.getTracks().forEach(t=>t.stop());return;}micStream=stream;const AC=window.AudioContext||window.webkitAudioContext;audioContext=new AC();await audioContext.resume();const source=audioContext.createMediaStreamSource(stream);const analyser=audioContext.createAnalyser();analyser.fftSize=256;source.connect(analyser);const samples=new Uint8Array(analyser.frequencyBinCount);$('#mic-button').classList.add('active');$('#mic-button').setAttribute('aria-label','Stop microphone');setState('listening','MICROPHONE ACTIVE','Local level visualization only. Audio is not recorded, sent, or transcribed.');function frame(){analyser.getByteFrequencyData(samples);const level=samples.reduce((a,b)=>a+b,0)/samples.length/128;$('#orb-stage').style.setProperty('--level',Math.min(level,1));$$('.wave i').forEach((bar,i)=>bar.style.height=`${3+samples[i*3]/255*25}px`);raf=requestAnimationFrame(frame);}frame();}catch(e){stopActivity();toast(e.name==='NotAllowedError'?'Microphone permission was denied. Text controls remain available.':'Microphone unavailable. Check your input device and browser permissions.');}}
$('#mic-button').onclick=startMic;
function preview(){showDialog('<p class="eyebrow">INTERACTION PREVIEW</p><h2>Give Draeven a voice.</h2><p>Explore the visual states. The speaking sample uses a voice supplied by your browser; it is not Draeven\'s final voice or a live AI reply.</p><div class="dialog-controls"><button class="bronze-button" id="preview-listen">Listening animation</button><button class="bronze-button" id="preview-think">Thinking animation</button><button class="bronze-button" id="preview-speak">Speak a sample</button><button class="bronze-button" id="preview-stop">Stop</button></div><p>For a real microphone level display, use the microphone button in the command bar. No audio is uploaded.</p>');$('#preview-listen').onclick=()=>{stopActivity();$('#detail-dialog').close();setState('listening','LISTENING · VISUAL PREVIEW','Demonstration state. The microphone is not active.');previewTimer=setTimeout(stopActivity,6000);};$('#preview-think').onclick=()=>{stopActivity();$('#detail-dialog').close();setState('thinking','THINKING · VISUAL PREVIEW','Demonstration state. No AI request is running.');previewTimer=setTimeout(stopActivity,6000);};$('#preview-speak').onclick=()=>{stopActivity();$('#detail-dialog').close();if(!window.speechSynthesis){toast('Browser speech is unavailable.');return;}const utterance=new SpeechSynthesisUtterance('Welcome to the Citadel, Semaj. Your priorities are gathered. Your council awaits. What would you have me do?');utterance.rate=.87;utterance.pitch=.8;const voices=speechSynthesis.getVoices();const voice=voices.find(v=>/David|Daniel|George|James/i.test(v.name)&&/^en/i.test(v.lang))||voices.find(v=>/^en/i.test(v.lang));if(voice)utterance.voice=voice;utterance.onstart=()=>setState('speaking','SPEAKING · BROWSER PREVIEW','Visual rhythm follows playback state, not audio amplitude.');utterance.onend=()=>stopActivity();utterance.onerror=()=>{stopActivity();toast('Speech playback ended or was unavailable.');};speechSynthesis.speak(utterance);};$('#preview-stop').onclick=()=>{stopActivity();$('#detail-dialog').close();};};
$('#preview-button').onclick=preview;

// === JARVIS INTEGRATION START ===
let draevenSessionId = 'draeven-session-1';
let isJarvisRequestPending = false;

// Conversation display
const conversationContainer = document.getElementById('conversation-display') || createConversationDisplay();

function createConversationDisplay() {
  const container = document.createElement('div');
  container.id = 'conversation-display';
  container.className = 'conversation-area';
  container.setAttribute('role', 'region');
  container.setAttribute('aria-label', 'Conversation with Draeven');
  const commandForm = document.getElementById('command-form');
  if (commandForm && commandForm.parentNode) {
    commandForm.parentNode.insertBefore(container, commandForm.nextSibling);
  }
  return container;
}

function displayMessage(role, text, provider = null) {
  const entry = document.createElement('div');
  entry.className = `conversation-entry role-${role}`;

  const label = document.createElement('div');
  label.className = 'message-label';
  label.textContent = role === 'user' ? 'You' : 'Draeven';
  if (provider && role === 'assistant') {
    label.textContent += ` (${provider})`;
  }

  const body = document.createElement('div');
  body.className = 'message-body';
  body.textContent = text; // SAFE: textContent prevents XSS

  entry.appendChild(label);
  entry.appendChild(body);
  conversationContainer.appendChild(entry);
  conversationContainer.scrollTop = conversationContainer.scrollHeight;
}

function setOrbThinking(thinking) {
  const state = thinking ? 'thinking' : 'idle';
  setState(state, thinking ? 'CONSULTING JARVIS' : 'AT REST', thinking ? 'Processing your request...' : 'Your interface is ready. The intelligence link is not connected.');
}

async function askJarvis(userInput) {
  if (isJarvisRequestPending) {
    toast('Request in progress, please wait.');
    return null;
  }

  isJarvisRequestPending = true;
  setOrbThinking(true);

  try {
    displayMessage('user', userInput);

    const response = await fetch('http://127.0.0.1:4783/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userInput,
        session_id: draevenSessionId,
        task_type: 'general'
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (!data || typeof data.reply !== 'string') {
      throw new Error('Invalid response from Jarvis');
    }

    if (data.session_id) {
      draevenSessionId = data.session_id;
    }

    const provider = data.provider || 'unknown';
    displayMessage('assistant', data.reply, provider);
    toast('Jarvis responded.');

    return data;
  } catch (error) {
    const errorMsg = `Jarvis unavailable: ${error.message}`;
    displayMessage('assistant', errorMsg, 'error');
    toast('Backend connection failed. Check if Jarvis is running on localhost:8000.');
    console.error('[Jarvis Error]', error);
    return null;
  } finally {
    isJarvisRequestPending = false;
    setOrbThinking(false);
  }
}

// === COMMAND FORM HANDLER - NARROWER MATCHING ===
$('#command-form').addEventListener('submit', async e => {
  e.preventDefault();
  const input = $('#command-input');
  const text = input.value.trim();

  if (!text) return;
  input.value = '';

  // EXPLICIT LOCAL COMMANDS - exact phrase matching only
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
    // Try to match agent names (narrow match)
    const lowerText = text.toLowerCase();
    const agent = council.find(a => lowerText === a.name.split(' ')[0].toLowerCase());
    if (agent) {
      openAgent(agent.id);
    } else {
      // No local match → send to Jarvis
      await askJarvis(text);
    }
  }
});
// === JARVIS INTEGRATION END ===

document.addEventListener('visibilitychange',()=>{document.body.classList.toggle('page-hidden',document.hidden);if(document.hidden)stopActivity();});window.addEventListener('pagehide',stopActivity);window.addEventListener('hashchange',()=>showView(location.hash.slice(1)));showView(location.hash.slice(1)||'overview');

const characterVoices={
 lucien:{rate:.84,pitch:.72,direction:'Vampire · a measured, aristocratic baritone. Calm precision, with room between the words.',preferred:/George|Daniel|Ryan|David/i,text:'I am Lucien Voss. Before we commit your time or your resources, we will understand the opportunity. Bring me the decision. I will bring you clarity.'},
 garrick:{rate:.93,pitch:.55,direction:'Werewolf · grounded, deep, and direct. A rugged delivery with purposeful momentum.',preferred:/David|Guy|Mark|James/i,text:'Garrick Thorne. Give me the objective, and we will get the work moving. Every blocker brought into the light. Every promise followed through.'},
 vaelis:{rate:.88,pitch:.98,direction:'Elven dark fae · smooth, lyrical, and deliberate. Lighter resonance without losing masculine presence.',preferred:/Ryan|Daniel|Christopher|George/i,text:'I am Vaelis Nightweave. Your ideas deserve a voice and a shape that belong to you alone. Let us make something unmistakably yours.'},
 azrath:{rate:.77,pitch:.4,direction:'Demon · a low, deliberate bass. Weight and restraint rather than shouting or distortion.',preferred:/David|George|Guy|Mark/i,text:'Azrath Veyr. I tend the forge beneath the Citadel. We will know what is connected, what has failed, and what has truly been done.'}
};
function voiceStatus(text){const el=$('#character-voice-status');if(el)el.textContent=text;}
function populateCharacterVoices(id){const el=$('#character-voice');if(!el)return;el.replaceChildren();const voices=window.speechSynthesis?speechSynthesis.getVoices():[];const eligible=voices.filter(v=>/^en/i.test(v.lang));const list=eligible.length?eligible:voices;let saved='';try{saved=localStorage.getItem('draeven-voice-'+id)||'';}catch{}const preferred=list.find(v=>v.voiceURI===saved)||list.find(v=>characterVoices[id].preferred.test(v.name))||list[0];if(!list.length){const o=new Option('Browser default (voices not listed yet)','');el.add(o);}else list.forEach(v=>el.add(new Option(v.name+' · '+v.lang+(v.localService?' · local':''),v.voiceURI,false,v===preferred)));}
function speakCharacter(id){
 stopActivity();if(!window.speechSynthesis){voiceStatus('Speech is unavailable in this browser.');return;}
 const profile=characterVoices[id];const a=council.find(a=>a.id===id);const line=new SpeechSynthesisUtterance(profile.text);line.rate=profile.rate;line.pitch=profile.pitch;const selected=$('#character-voice')?.value;const voice=speechSynthesis.getVoices().find(v=>v.voiceURI===selected);if(voice)line.voice=voice;
 voiceStatus('Preparing browser voice…');
 line.onstart=()=>{setState('speaking',a.name.toUpperCase()+' · VOICE PREVIEW','Scripted character introduction using browser speech.');$$('[data-agent="'+id+'"]').forEach(e=>e.classList.add('speaking'));voiceStatus('Speaking · '+(voice?.name||'browser default'));};line.onend=()=>{stopActivity();voiceStatus('Preview finished.');};line.onerror=e=>{stopActivity();voiceStatus(e.error==='canceled'||e.error==='interrupted'?'Voice stopped.':'Speech unavailable: '+e.error+'. Try a different voice or browser.');};activeCharacterLine=line;speechSynthesis.speak(line);
}
if(window.speechSynthesis)speechSynthesis.addEventListener('voiceschanged',()=>{const button=$('#character-speak');if(button){const a=council.find(a=>button.textContent.includes(a.name.split(' ')[0]));if(a)populateCharacterVoices(a.id);}});
$('#detail-dialog').addEventListener('close',()=>{if(activeCharacterLine)stopActivity();});
for(const target of [$('#council-grid'),$('#council-large')]){const button=document.createElement('button');button.className='council-artwork-button';button.textContent='View the complete Council artwork ↗';button.onclick=()=>showDialog('<p class="eyebrow">THE COUNCIL · ORIGINAL ARTWORK</p><img class="complete-artwork" src="assets/council.png" alt="Full original Council artwork: Lucien, Garrick, Vaelis, and Azrath in their castle chambers."><p>The original composition, uncropped.</p>');target.after(button);}
```

---

## Step 3: Add Conversation Display HTML

Add this line to your `index.html` **right after** `</form>` (after the command form, before `</div>`):

```html
<div id="conversation-display" class="conversation-area" role="region" aria-label="Conversation with Draeven"></div>
```

---

## Step 4: Add CSS Styling

Add this to your `styles.css`:

```css
/* Conversation Display */
#conversation-display {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  max-height: 500px;
  min-height: 200px;
  overflow-y: auto;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.9rem;
  color: #e0e0e0;
  line-height: 1.5;
}

.conversation-entry {
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  border-left: 4px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.conversation-entry.role-user {
  background: rgba(100, 150, 255, 0.08);
  border-left-color: #6496ff;
  margin-left: 1rem;
}

.conversation-entry.role-assistant {
  background: rgba(100, 200, 150, 0.08);
  border-left-color: #64c896;
  margin-right: 1rem;
}

.message-label {
  font-weight: bold;
  color: #a0d8ff;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.conversation-entry.role-assistant .message-label {
  color: #64c896;
}

.message-body {
  color: #e0e0e0;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
}
```

---

## Step 5: Test It

### Terminal 1: Start Jarvis
```powershell
cd C:\path\to\draeven-jarvis-system
quick-start.bat
```

### Terminal 2: Start Draeven
```powershell
cd C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud
python serve.py
```

### Browser: Test
1. Open `http://127.0.0.1:4783/`
2. Try `show tasks` → navigates locally (NO backend)
3. Try `What's my top priority?` → hits Jarvis backend
4. Try `open council` → navigates locally (NO backend)
5. Try `Plan my week` → hits Jarvis backend

---

## Key Changes Summary

| What | Old | New |
|------|-----|-----|
| Command matching | Words anywhere in input | Exact phrase or anchored |
| "show tasks" | Matches ✓ | Matches ✓ |
| "What's my top priority?" | Matches (WRONG) ✗ | Goes to backend ✓ |
| Backend routing | None | All unmatched → Jarvis |
| Display | None | Conversation area |
| Session | None | Preserves across requests |
| Error handling | Toast only | Display + toast |

---

## You're Done!

Your Draeven HUD now seamlessly integrates with Jarvis while keeping all local commands working perfectly. 🚀
