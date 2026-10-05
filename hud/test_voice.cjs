const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');
let timers=new Map(),tid=0;
const context={setTimeout(fn){timers.set(++tid,fn);return tid;},clearTimeout(id){timers.delete(id);}};
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/js/voice.js','utf8'),context);
function setup(supported=true){
 const events={texts:[],status:[],spoken:[],listening:[],speaking:[]};let current;
 class Recognition{constructor(){current=this;}start(){this.onstart?.();}stop(){this.stopped=true;}abort(){this.aborted=true;}}
 class Utterance{constructor(text){this.text=text;}}
 const env={SpeechSynthesisUtterance:Utterance,speechSynthesis:{getVoices:()=>[],cancel(){},speak(line){events.spoken.push(line);line.onstart?.();}}};
 if(supported)env.SpeechRecognition=Recognition;
 const voice=context.createDraevenVoice(env,{status:t=>events.status.push(t),listening:v=>events.listening.push(v),speaking:v=>events.speaking.push(v),transcript:t=>events.texts.push(t)});
 return {voice,events,get current(){return current;}};
}
let tests=0;
function test(name,fn){timers.clear();fn();tests++;console.log('PASS '+name);}
function result(text,final=true){const item=[{transcript:text}];item.isFinal=final;return {results:[item]};}
test('one final transcript sends once',()=>{const x=setup();x.voice.listen();const r=x.current;r.onresult(result('My priority?'));const ended=r.onend;ended();ended();assert.deepEqual(x.events.texts,['My priority?']);});
test('interim speech does not submit',()=>{const x=setup();x.voice.listen();x.current.onresult(result('incomplete',false));x.current.onend();assert.equal(x.events.texts.length,0);});
test('stop discards late recognition events',()=>{const x=setup();x.voice.listen();const r=x.current;const ended=r.onend;r.onresult(result('do not send'));x.voice.stop();ended();assert.equal(x.events.texts.length,0);assert.ok(r.aborted);});
test('permission denial cannot submit',()=>{const x=setup();x.voice.listen();const r=x.current;const ended=r.onend;r.onerror({error:'not-allowed'});ended();assert.equal(x.events.texts.length,0);assert.match(x.events.status.at(-1),/denied/);});
test('unsupported recognition explains fallback',()=>{const x=setup(false);x.voice.listen();assert.match(x.events.status.at(-1),/unavailable/);});
test('second click cancels listening',()=>{const x=setup();x.voice.listen();x.voice.listen();assert.equal(x.events.texts.length,0);assert.match(x.events.status.at(-1),/cancelled/);});
test('push to talk release finishes and sends final speech',()=>{const x=setup();x.voice.listen();const r=x.current;r.onresult(result('Check the storefronts'));const ended=r.onend;x.voice.finishListening();assert.ok(r.stopped);ended();assert.deepEqual(x.events.texts,['Check the storefronts']);});
test('speaking clears microphone and stops queued chunks',()=>{const x=setup();x.voice.listen();const r=x.current;x.voice.speak('First sentence. Second sentence.');assert.ok(r.aborted);const ended=x.events.spoken[0].onend;x.voice.stop();ended();assert.equal(x.events.spoken.length,1);});
test('speech error offers manual replay',()=>{const x=setup();x.voice.speak('Hello');x.events.spoken[0].onerror();assert.match(x.events.status.at(-1),/Read last reply/);});
test('listening timeout aborts capture',()=>{const x=setup();x.voice.listen();[...timers.values()][0]();assert.ok(x.current.aborted);assert.equal(x.events.texts.length,0);});
console.log(tests+' voice behavior checks passed');
