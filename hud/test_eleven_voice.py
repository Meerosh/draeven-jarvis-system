import json,unittest,urllib.error
from unittest.mock import patch
import eleven_voice as voice
class ElevenTests(unittest.TestCase):
 def test_windows_encryption_roundtrip(self):
  sample=b'non-secret-test-value';encrypted=voice.protect(sample)
  self.assertNotIn(sample,encrypted);self.assertEqual(voice.protect(encrypted,True),sample)
 def test_missing_key_no_network(self):
  with patch.object(voice,'get_key',return_value=''),patch.object(voice.CLIENT,'open') as send:
   with self.assertRaises(voice.VoiceError):voice.call('/v2/voices')
   send.assert_not_called()
 def test_invalid_speech_does_not_generate(self):
  with patch.object(voice,'call') as send:
   for text,identifier in [('', 'abc'),('x'*5001,'abc'),('hello','../voice'),('hello','')]:
    with self.assertRaises(voice.VoiceError):voice.synthesize(text,identifier)
   send.assert_not_called()
 def test_speech_request_contract(self):
  with patch.object(voice,'call',return_value=(b'mp3-test','audio/mpeg')) as send:
   self.assertEqual(voice.synthesize('hello','voice123'),b'mp3-test')
   path,payload=send.call_args.args;self.assertEqual(path,'/v1/text-to-speech/voice123?output_format=mp3_44100_128');self.assertEqual(payload['model_id'],'eleven_multilingual_v2')
 def test_provider_error_redacted_and_no_retry(self):
  secret='dummy-secret-not-real'
  with patch.object(voice.CLIENT,'open',side_effect=urllib.error.HTTPError('https://api.elevenlabs.io',401,secret,{},None)) as send:
   with self.assertRaises(voice.VoiceError) as error:voice.call('/v2/voices',key=secret)
   self.assertNotIn(secret,str(error.exception));self.assertEqual(send.call_count,1)
 def test_voice_sort_favors_requested_direction(self):
  data={'voices':[{'voice_id':'a','name':'Bright','labels':{'gender':'female'}},{'voice_id':'b','name':'Calm baritone','labels':{'gender':'male'},'description':'deep and warm'}]}
  with patch.object(voice,'call',return_value=(json.dumps(data).encode(),'application/json')):
   self.assertEqual(voice.voices()['voices'][0]['id'],'b')
 def test_non_audio_rejected_and_lock_released(self):
  with patch.object(voice,'call',return_value=(b'error','application/json')):
   with self.assertRaises(voice.VoiceError):voice.synthesize('hello','voice123')
  self.assertFalse(voice.LOCK.locked())
if __name__=='__main__':unittest.main()
