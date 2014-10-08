# all the imports
from flask import Flask, request, session, g, redirect, url_for, \
     abort, jsonify
from bson.json_util import dumps
from pymongo import MongoClient

# create our little application :)
app = Flask(__name__)

# Load default config
app.config.update(dict(
    DATABASE = 'cluepointspoc',
    DATABASE_URI = 'cluepointspoc:cluepointspoc@ds039950.mongolab.com',
    DATABASE_PORT = '39950',
    CUSTOMERS_COLLECTION = 'customers',
    DEBUG = True, #DISABLE IN PROD
    SECRET_KEY = 'very_secure_dev_key'
))

def get_db():
    '''
        I am using MongoLab.com as a cloud mongoDB service.
        They offer a sandbox for free but I have almost no rights and
        I am only allowed to use one database which isn't nice for testing.
        So the testing database is local while the "prod" database is on mongolab.com
    '''
    if not hasattr(g, 'cluepoints_db'):
        client = MongoClient('mongodb://{db_uri}:{db_port}/{db_name}'.format(db_uri=app.config['DATABASE_URI'], db_port=app.config['DATABASE_PORT'], db_name=app.config['DATABASE']))
        g.mongoclient = client # for easier closing at the end
        g.cluepoints_db = client[app.config['DATABASE']] #save DB as if we were to use many collections and not just one
    return g.cluepoints_db

def validate_customer(customer):
    # perform data validation here
    possible_keys = ['type', 'balance', 'cust_name', 'cust_firstname', 'cust_address', 'cust_dob', 'number'] # these are all the keys we need and accept
    for key in possible_keys:
        if key not in customer:
            return 'Attribute %s missing' % (key) # return error if anything is missing
        elif isinstance(customer[key], basestring) and (customer[key] == '' or customer[key].isspace()):
            return 'Attribute %s empty' % (key) # return error if anything is empty
    
    available_types = ['CR', 'CE', 'CV'] # totally made up values
    if customer['type'] not in available_types:
        return 'Attribute type must be one of ' + ', '.join(available_types)
    
    try:
        float(customer['balance']) #balance must be a float in order to be meaningful
    except ValueError:
        return 'Attribute balance must be a float'
    
    # if here -> success
    return 'success'

@app.before_request
def before_request():
    get_db()

@app.teardown_request
def teardown_request(exception):
    mongoclient = getattr(g, 'mongoclient', None)
    if mongoclient is not None:
        mongoclient.close()

@app.route('/accounts', methods=['POST'])
def add_entry():
    data = request.get_json() # retrieve the json sent by the requester
    result = validate_customer(data) # perform data validation
    if result != 'success':
        return '{"status": "failure", "error": %s}' % (result)
    # now that the data are validated we can go on with our processing
    customer = {"type": data['type'],
                "number": data['number'],
                "balance": data['balance'],
                "cust_name": data['cust_name'],
                "cust_firstname": data['cust_firstname'],
                "cust_address": data['cust_address'],
                "cust_dob": data['cust_dob']}
    # retrieve customers collection
    customers = g.cluepoints_db[app.config['CUSTOMERS_COLLECTION']]
    # insert new customer
    cust_id = customers.insert(customer)
    
    # return the newly created id for the account created
    resp = {"cust_id": cust_id}
    return dumps(resp)

@app.route('/accounts/<account_number>', methods=['GET'])
def get_entry(account_number):
    # retrieve customers collection
    customers = g.cluepoints_db[app.config['CUSTOMERS_COLLECTION']]
    # insert new customer
    customer = customers.find_one({"number": account_number})
    return dumps(customer)

@app.route('/accounts/<account_number>', methods=['DELETE'])
def delete_entry(account_number):
    # retrieve customers collection
    customers = g.cluepoints_db[app.config['CUSTOMERS_COLLECTION']]
    # delete customer
    resp = customers.remove({"number": account_number})
    return dumps(resp)

@app.route('/accounts/<account_number>', methods=['PUT'])
def update_entry(account_number):
    data = request.get_json()
    # performing a check to see if we're not being provided with wrong data
    #   retrieve customers collection
    customers = g.cluepoints_db[app.config['CUSTOMERS_COLLECTION']]
    customer = customers.find_one({"number": account_number}) # first we retrieve the account concerned by this update
    
    # if we couldn't find any customer
    if customer is None:
        return '{"status": "failure", "error": "No account was found with provided account number"}'
    
    # erase all data with the ones provided in the update request
    possible_keys = ['type', 'balance', 'cust_name', 'cust_firstname', 'cust_address', 'cust_dob'] # these are all the keys we accept
    for key in possible_keys: # loop over all possible keys and check if they're provided
        if key in data:
            customer[key] = data[key] # add the data to the soon-to-be updated customer
    
    result = validate_customer(customer) # perform data validation
    if result != 'success':
        return '{"status": "failure", "error": %s}' % (result)
    
    # update customer
    resp = customers.update({"number": account_number}, {"$set": customer})
    return '{"status": "success"}'

@app.route('/accounts', methods=['GET'])
def list_entries():
    # retrieve customers collection
    customers = g.cluepoints_db[app.config['CUSTOMERS_COLLECTION']]
    return dumps(list(customers.find()))


app.config.from_object(__name__)
if __name__ == '__main__':
    app.run()
