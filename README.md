cluepointspoc
=============

POC for my application at CluePoints.
I was asked to provide a simple CRUD RESTful API exposing the contents of a database.

This project is using Flask, PyMongo and MongoDB as database.

When the web application server is started, the application responds to 5 URLs:
- GET on /accounts which lists all accounts in the database
- GET on /accounts/<account_number> which will return the data of the providing account number
- POST on /accounts which will insert a new account in the database, providing the data is sent on JSON format and contains all the needed key-value pairs
- UPDATE on /accounts/<account_number> which will update an existing account in the database, providing the data is sent on JSON format
- DELETE on /accounts/<account_number> which will delete an existing account in the database
