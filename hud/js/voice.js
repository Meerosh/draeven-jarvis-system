/* Browser voice controller. Audio recognition may use the browser provider's service. */
function createDraevenVoice(env, hooks) {
  const Recognition = env.SpeechRecognition || env.webkitSpeechRecognition;
  let recognition = null, generation = 0, speechGeneration = 0, utterance = null;
  let listenTimer = null, speechTimer = null;
  let audio=null,audioURL=null,audioRequest=null,lastAudio=null;
  const status = text => hooks.status(text);
  function stopListening() {
    generation++;
    clearTimeout(listenTimer);
    if (recognition) {
      const previous=recognition; recognition=null;
      previous.onstart=previous.onresult=previous.onerror=previous.onend=null;
      try { previous.abort(); } catch {}
    }
    hooks.listening(false);
  }
  function stopSpeaking() {
    speechGeneration++;
    if(audioRequest){audioRequest.abort();audioRequest=null;}
    if(audio){audio.onended=audio.onerror=null;audio.pause();audio.removeAttribute('src');audio.load();audio=null;}
    if(audioURL){env.URL.revokeObjectURL(audioURL);audioURL=null;}
    clearTimeout(speechTimer);
    if(utterance) utterance.onstart=utterance.onend=utterance.onerror=null;
    utterance=null;
    if(env.speechSynthesis) env.speechSynthesis.cancel();
    hooks.speaking(false);
  }
  function stop() { stopListening(); stopSpeaking(); }
  function listen() {
    if(recognition) { stopListening(); status('Listening cancelled. Nothing was sent.'); return; }
    stop();
    if(!Recognition) {status('Speech recognition is unavailable here. Open Draeven in Chrome or Edge, or type your question.');return;}
    const token=++generation;
    let text='', failed=false, sent=false;
    const current=new Recognition(); recognition=current;
    current.lang='en-US'; current.continuous=false; current.interimResults=true; current.maxAlternatives=1;
    hooks.listening(true);
    status('Waiting for microphone permission…');
    current.onstart=()=>{if(token===generation)status('Listening… Speak your question, then pause.');};
    current.onresult=event=>{
      if(token!==generation)return;
      let finalText='',interim='';
      for(let i=0;i<event.results.length;i++){
        if(event.results[i].isFinal)finalText+=event.results[i][0].transcript+' ';
        else interim+=event.results[i][0].transcript+' ';
      }
      text=finalText.trim();
      status((text||interim.trim())?'Heard: '+(text||interim.trim()):'Listening…');
    };
    current.onerror=event=>{
      if(token!==generation)return;
      failed=true;
      const messages={
        'not-allowed':'Microphone access was denied. Allow it in the browser’s site settings and try again.',
        'service-not-allowed':'This browser’s speech service is unavailable. Try Chrome or Edge, or type instead.',
        'audio-capture':'No microphone was available. Check your input device.',
        'network':'The browser speech service could not connect. Try another browser or type your question.',
        'no-speech':'No speech was detected. Click Talk and try again.',
        'aborted':'Listening cancelled. Nothing was sent.'
      };
      stopListening(); status(messages[event.error]||'Speech recognition failed. Please type or try again.');
    };
    current.onend=()=>{
      if(token!==generation)return;
      recognition=null;clearTimeout(listenTimer);hooks.listening(false);
      if(!failed && text && !sent){sent=true;generation++;status('Question captured. Sending to JARVIS…');hooks.transcript(text);}
      else if(!failed)status('No complete speech was captured. Click Talk to try again.');
    };
    listenTimer=setTimeout(()=>{if(token===generation){stopListening();status('Listening timed out. Nothing was sent. Click Talk to try again.');}},30000);
    try{current.start();}catch{stopListening();status('The microphone could not start. Try again or type your question.');}
  }
  async function speakEleven(text,voiceId) {
    const token=++speechGeneration;
    if(!voiceId){status('Choose an ElevenLabs voice first.');return;}
    if(text.length>5000){status('This reply is too long for a single voice request. Ask for a shorter answer.');return;}
    const controller=new env.AbortController();audioRequest=controller;
    const timer=setTimeout(()=>controller.abort(),65000);
    status('Preparing ElevenLabs audio… Stop voice cancels playback; generation may still use credits.');
    try {
      let blob;
      if(lastAudio && lastAudio.text===text && lastAudio.voice===voiceId)blob=lastAudio.blob;
      else {
        const response=await env.fetch('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,voice_id:voiceId}),signal:controller.signal});
        if(!response.ok){const data=await response.json();throw new Error(data.error||'ElevenLabs could not prepare speech.');}
        blob=await response.blob();
        if(!blob.type.startsWith('audio/'))throw new Error('No playable audio was returned.');
        lastAudio={text,voice:voiceId,blob};
      }
      if(token!==speechGeneration)return;
      clearTimeout(timer);audioRequest=null;
      audioURL=env.URL.createObjectURL(blob);audio=new env.Audio(audioURL);
      audio.onended=()=>{if(token!==speechGeneration)return;stopSpeaking();status('Finished speaking. Click Talk for your next question.');};
      audio.onerror=()=>{if(token!==speechGeneration)return;stopSpeaking();status('Playback failed. Use Read last reply to try again.');};
      await audio.play();
      if(token!==speechGeneration)return;
      hooks.speaking(true);status('Draeven is speaking with ElevenLabs. Use Stop voice to interrupt.');
    } catch(error) {
      if(token!==speechGeneration)return;
      stopSpeaking();
      status(error.name==='NotAllowedError'?'Audio is ready. Click Read last reply to allow playback.':error.name==='AbortError'?'Voice request timed out. It may have used credits; no retry was sent.':error.message);
    } finally {clearTimeout(timer);if(token===speechGeneration)audioRequest=null;}
  }
  function speak(text, voiceURI='') {
    stop();
    if(voiceURI.startsWith('eleven:')){speakEleven(String(text).replace(/[*#`]/g,''),voiceURI.slice(7));return;}
    if(!env.speechSynthesis || !env.SpeechSynthesisUtterance){status('Spoken replies are unavailable in this browser. The answer is still on screen.');return;}
    const clean=String(text).replace(/```[\s\S]*?```/g,' Code is shown on screen. ').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*#`]/g,'').trim();
    const chunks=clean.match(/[^.!?\n]+[.!?\n]*|[.!?\n]+/g)||[];
    const queue=chunks.flatMap(part=>part.match(/.{1,220}(?:\s|$)|.{1,220}/g)||[]);
    const token=++speechGeneration;
    const voices=env.speechSynthesis.getVoices();
    const voice=voices.find(v=>v.voiceURI===voiceURI)||voices.find(v=>/^en/i.test(v.lang)&&/David|Daniel|George|James|Guy/i.test(v.name))||voices.find(v=>/^en/i.test(v.lang));
    function next(){
      if(token!==speechGeneration)return;
      const part=queue.shift();
      if(!part){utterance=null;hooks.speaking(false);status('Finished speaking. Click Talk for your next question.');return;}
      const line=new env.SpeechSynthesisUtterance(part);utterance=line;
      line.lang='en-US';line.rate=.94;line.pitch=.8;if(voice)line.voice=voice;
      let started=false;
      line.onstart=()=>{if(token!==speechGeneration)return;started=true;clearTimeout(speechTimer);hooks.speaking(true);status('Draeven is speaking. Use Stop voice to interrupt.');};
      line.onend=()=>{clearTimeout(speechTimer);if(token===speechGeneration)next();};
      line.onerror=()=>{if(token!==speechGeneration)return;stopSpeaking();status('Audio playback was blocked or failed. Click Read last reply to try again.');};
      speechTimer=setTimeout(()=>{if(!started&&token===speechGeneration){stopSpeaking();status('Audio did not start. Click Read last reply to play it.');}},8000);
      env.speechSynthesis.speak(line);
    }
    status('Preparing spoken reply…');next();
  }
  return {listen,speak,stop,recognitionSupported:!!Recognition,speechSupported:!!env.speechSynthesis};
}
