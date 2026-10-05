"""Local adapter checks; provider calls are replaced with controlled responses."""
import importlib.util, json, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('hud_server',Path(__file__).with_name('serve.py'))
hud=importlib.util.module_from_spec(spec);spec.loader.exec_module(hud)

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=hud.Server(('127.0.0.1',0),hud.Handler)
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
        hud.HOSTS.add(cls.base.split('//')[1])
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close()
    def request(self,path,body=None,headers=None,method=None):
        data=None if body is None else json.dumps(body).encode()
        req=urllib.request.Request(self.base+path,data,{'Content-Type':'application/json',**(headers or {})},method=method)
        try:
            response=urllib.request.urlopen(req,timeout=3)
        except urllib.error.HTTPError as error:
            response=error
        with response:
            return response.status,response.read()
    def test_maps_answer_and_strips_client_overrides(self):
        with patch.object(hud,'upstream',return_value={'answer':'Vault answer','route':'claude (status files)','confirm_id':'pending'}) as upstream:
            status,raw=self.request('/api/chat',{'message':'My priority?','reflex':{'stakes':0},'confirm':True})
            self.assertEqual(status,200)
            result=json.loads(raw)
            self.assertEqual(result['reply'],'Vault answer')
            self.assertTrue(result['approval_required'])
            self.assertEqual(result['mode'],'approval-gated')
            upstream.assert_called_once_with('/ask',{'text':'My priority?','agent':None},timeout=720)
    def test_shopify_catalog_question_uses_live_connector_instead_of_draft_model(self):
        summary={'verified':True,'active_products':18,'active_greeting_cards':17,
                 'card_titles':['Example'],
                 'digital_inventory_note':'Digital products do not use physical inventory.'}
        with patch.object(hud.service_connections,'shopify_catalog_summary',return_value=summary), \
             patch.object(hud,'upstream') as upstream:
            status,raw=self.request('/api/chat',{'message':'How many cards are available in Shopify?'})
        result=json.loads(raw)
        self.assertEqual(status,200)
        self.assertIn('17 active greeting-card listings',result['reply'])
        self.assertEqual(result['provider'],'Shopify live read')
        self.assertTrue(result['receipt']['verified'])
        upstream.assert_not_called()
    def test_offline_is_failure(self):
        with patch.object(hud,'upstream',side_effect=ConnectionRefusedError):
            self.assertEqual(self.request('/api/chat',{'message':'hello'})[0],502)
            self.assertEqual(self.request('/api/health')[0],503)
    def test_empty_or_malformed_message(self):
        for body in ({'message':''},{'message':[]},[],{'message':'x'*16001}):
            self.assertEqual(self.request('/api/chat',body)[0],400)
    def test_foreign_origin_and_host_rejected(self):
        self.assertEqual(self.request('/api/chat',{'message':'hello'},{'Origin':'https://example.com'})[0],403)
        self.assertEqual(self.request('/',headers={'Host':'attacker.example'})[0],403)
    def test_private_files_and_actions_not_exposed(self):
        for path in ('/serve.py','/launch.pyw','/.env','/preview-server.log','/JSIndexServeBackup/js/main.js','/assets/../serve.py'):
            self.assertEqual(self.request(path)[0],404)
            self.assertEqual(self.request(path,method='HEAD')[0],404)
        status, raw = self.request('/api/confirm',{'confirm_id':''})
        result = json.loads(raw)
        self.assertEqual(status,400)
        self.assertIn('error',result)
    def test_simultaneous_request_is_rejected(self):
        with hud.CHAT_LOCK:
            self.assertEqual(self.request('/api/chat',{'message':'hello'})[0],409)
    def test_empty_provider_answer_is_failure(self):
        with patch.object(hud,'upstream',return_value={'answer':''}):
            self.assertEqual(self.request('/api/chat',{'message':'hello'})[0],502)
    def test_health_is_not_model_verification(self):
        with patch.object(hud,'upstream',return_value={'ok':True,'notes_indexed':321}):
            status,raw=self.request('/api/health')
            self.assertEqual(status,200)
            self.assertFalse(json.loads(raw)['model_verified'])
    def test_wright_token_is_generated_locally_and_never_served_by_get(self):
        with patch.object(hud,'save_wright_token') as save:
            status,raw=self.request('/api/connections/wright',{})
        result=json.loads(raw)
        self.assertEqual(status,200)
        self.assertTrue(result['configured'])
        self.assertEqual(result['header'],'X-Draeven-Tool-Token')
        self.assertGreater(len(result['token']),30)
        save.assert_called_once_with(result['token'])
        with patch.object(hud,'wright_token_is_configured',return_value=True):
            status,raw=self.request('/api/connections/wright')
        self.assertEqual(json.loads(raw),{'configured':True})
    def test_etsy_authorization_starts_with_provider_url(self):
        with patch.object(hud.service_connections,'begin_etsy_oauth',return_value=(
                'https://www.etsy.com/oauth/connect?state=safe',
                {'state':'safe','verifier':'private','created_at':'9999999999'})):
            status,raw=self.request('/api/connections/etsy/authorize',{})
        self.assertEqual(status,200)
        result=json.loads(raw)
        self.assertEqual(result['url'],'https://www.etsy.com/oauth/connect?state=safe')
        self.assertNotIn('verifier',result)
    def test_etsy_callback_requires_matching_state(self):
        status,raw=self.request('/api/connections/etsy/callback?code=unused&state=wrong')
        self.assertEqual(status,400)
        self.assertIn(b'authorization request expired',raw)

if __name__=='__main__':unittest.main()
