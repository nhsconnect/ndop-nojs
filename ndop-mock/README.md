# NDOP Mock API

## Quickstart

This is a python flask app which emulates the behaviour of the backend of NDOP. It doesn't support python 2.7, please use 3.6+

There are some environment variables:
```bash
export FLASK_APP=mock.py 
export FLASK_ENV=development

```
FLASK_APP is mandatory, FLASK_ENV=development is preferable for developing as it detects changes and refreshes in real time.

To run the app:
```python 
pip install -r requirements.txt
export FLASK_APP=mock.py
flask run -p 5001
```

Which should return:
```console

* Serving Flask app "mock" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Running on http://127.0.0.1:5001/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

## Session

The mock is designed to respond 200 if any session_id cookie is given, regardless of expiry or validity. 

The endpoint /createsession will set a cookie using a random uuid.

```unique_seed``` URL parameter is for caching purposes. Currently the mock does nothing with it.

## Polls

There are two endpoints (below) which are designed to return 206 (incomplete) a few times before returning 200 (success). 
```counter.py``` has constants for these, currently set at 3. Hitting the endpoints in succession will decrement a counter and after 3 attempts return success.

```
/patientsearchresult
/storepreferencesresult
```

## Available endpoints

There is a basic list of available endpoints on confluence.

## Data

A json array of users is located at ```data/users.json```. To add data, simply extend this list.
Some responses are dependent on whether attributes exist (for example email, mobile). 

Mandatory:
- First name
- Surname
- DOB (x3 separate fields)
- NHS Number

## Quirks

If running flask in development mode, changes made will clear the in memory session cache. When running both apps in conjunction, this can lead to valid sessions in the main flask app which are not valid in the mock. 