import cluepoints
import unittest
from pymongo import MongoClient
from bson.json_util import dumps, loads

class CluePointsTestCase(unittest.TestCase):

    def setUp(self):
        # re-configurating the app to use the test database
        cluepoints.app.config['DATABASE'] = 'test_database'
        cluepoints.app.config['DATABASE_URI'] = 'localhost'
        cluepoints.app.config['DATABASE_PORT'] = '27017'
        cluepoints.app.config['TESTING'] = True # tells flask not to stop on errors
        self.app = cluepoints.app.test_client()
        self.client = MongoClient()
        # insert a test user
        self.client.test_database.customers.insert({"cust_address": "Karrenberg 35, 1170 Watermael-Boitsfort", "balance": 250, "cust_name": "De Keyser", "number": "234234324324424", "cust_firstname": "Michael", "cust_dob": "17/05/1989", "type": "CE"})

    def tearDown(self):
        # drop the test database after each test
        self.client.drop_database(cluepoints.app.config['DATABASE'])
        self.client.close()
    
    def test_init_db(self):
        # test in tests -> make sure our initial setUp works
        resp = list(self.client[cluepoints.app.config['DATABASE']][cluepoints.app.config['CUSTOMERS_COLLECTION']].find())
        assert len(resp) == 1
    
    def test_add(self):
        # simple add with no errors expected
        response = self.app.post('/accounts',
                                data='{"cust_address": "Test address", "balance": 999, "cust_name": "Test", "number": "99999999-9999999", "cust_firstname": "Test", "cust_dob": "17/05/1989", "type": "CE"}',
                                headers={'content-type':'application/json'})
        assert 'cust_id' in response.data
    
    def test_delete(self):
        # simple delete with no errors expected
        self.app.delete('/accounts/234234324324424',
                                data='',
                                headers={'content-type':'application/json'})
        resp = list(self.client[cluepoints.app.config['DATABASE']][cluepoints.app.config['CUSTOMERS_COLLECTION']].find())
        assert len(resp) == 0
    
    def test_update(self):
        # simple update with no errors expected
        response = self.app.put('/accounts/234234324324424',
                                data='{"cust_address": "This is a new address", "balance": 0}',
                                headers={'content-type':'application/json'})
        resp = list(self.client[cluepoints.app.config['DATABASE']][cluepoints.app.config['CUSTOMERS_COLLECTION']].find({"cust_address": "This is a new address"}))
        assert len(resp) == 1 and resp[0]['balance'] == 0
    
    def test_get(self):
        # simple get with no errors expected
        resp = self.app.get('/accounts/234234324324424')
        customer = loads(resp.data)
        assert customer['number'] == '234234324324424'
    
    def test_add_missing_arg(self):
        # try creating an account/customer without providing all args (type is missing)
        response = self.app.post('/accounts',
                                data='{"cust_address": "Test address", "balance": 999, "cust_name": "Test", "number": "99999999-9999999", "cust_firstname": "Test", "cust_dob": "17/05/1989"}',
                                headers={'content-type':'application/json'})
        assert 'Attribute type missing' in response.data
    
    def test_add_empty_arg(self):
        # try creating an account/customer without providing all args (type is empty)
        response = self.app.post('/accounts',
                                data='{"cust_address": "Test address", "balance": 999, "cust_name": "Test", "number": "99999999-9999999", "cust_firstname": "Test", "cust_dob": "17/05/1989", "type": ""}',
                                headers={'content-type':'application/json'})
        assert 'Attribute type empty' in response.data
    
    def test_add_invalid_type(self):
        # try creating an account/customer providing a wrong type argument
        response = self.app.post('/accounts',
                                data='{"cust_address": "Test address", "balance": 999, "cust_name": "Test", "number": "99999999-9999999", "cust_firstname": "Test", "cust_dob": "17/05/1989", "type": "WRONG"}',
                                headers={'content-type':'application/json'})
        assert 'Attribute type must be one of CR, CE, CV' in response.data
    
    def test_add_invalid_balance(self):
        # try creating an account/customer providing a wrong balance (balance must be a float)
        response = self.app.post('/accounts',
                                data='{"cust_address": "Test address", "balance": "not a number", "cust_name": "Test", "number": "99999999-9999999", "cust_firstname": "Test", "cust_dob": "17/05/1989", "type": "CE"}',
                                headers={'content-type':'application/json'})
        assert 'Attribute balance must be a float' in response.data

if __name__ == '__main__':
    unittest.main()
