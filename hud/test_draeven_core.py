import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from draeven_core import DraevenCore

EXACT = "OK.  I would like for you to produce a card that I can put up on Etsy and Shopify making sure to follow the O&L vibe.  The card is a halloween card for my best gay friend (gender neutral).  I want it to be spooky yet have a funny twist."

class RoutingTests(unittest.TestCase):
    def test_creative_requests_reach_model_without_commerce_calls(self):
        for text in [EXACT, 'Draft an Etsy listing for my Halloween card', 'Make a draft card for Shopify', 'Write Shopify product descriptions', 'Design a card for Etsy']:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                core=DraevenCore(Path(tmp)/'history.json')
                with patch('service_connections.shopify_products') as products, patch('service_connections.shopify_catalog_summary') as shopify, patch('service_connections.etsy_listing_summary') as etsy:
                    calls=[]
                    def upstream(path, body, timeout):
                        calls.append(body); return {'answer':'Halloween card concept', 'route':'creative model'}
                    reply=core.respond(text,None,upstream)
                    self.assertEqual(reply.route,'creative model');self.assertEqual(calls[0]['text'],text)
                    products.assert_not_called();shopify.assert_not_called();etsy.assert_not_called()
    def test_explicit_inventory_requests(self):
        for text in ['How many Shopify cards are active?', 'Show my Shopify products', 'Check Shopify inventory']:
            self.assertTrue(DraevenCore._shopify_request(text),text)
        for text in ['How many Etsy listings are active?', 'List Etsy drafts', 'Check Etsy listings']:
            self.assertTrue(DraevenCore._etsy_request(text),text)
    def test_existing_status_change_still_requires_approval(self):
        with tempfile.TemporaryDirectory() as tmp, patch('service_connections.shopify_products',return_value={'products':[{'id':'1','title':'Moon Dance','handle':'moon-dance','status':'DRAFT'}]}):
            reply=DraevenCore(Path(tmp)/'history.json').respond('Make Shopify Moon Dance active',None,None)
            self.assertEqual(reply.mode,'approval-required')

if __name__=='__main__':unittest.main()
