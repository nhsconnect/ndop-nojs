# NDOP no-js Flask App

## Building a zappa package for deployment into an NDOP AWS environment with terraform

Use the `start-build` target to make, with a `git_marker` argument as appropriate. This will spin up a docker container to build the zappa package, and upload the resultant zip file to the build artifacts bucket in S3. Note that you should have valid AWS session credentials in the Thunderbird shared services account to grant you access to upload to the bucket.

You will need to have docker installed and running, awscli installed, and xxd (hex dump) for building the zip file hash.

Example:
```
make start-build git_marker=TDBAT_398_test
```

## Manual Setup

Requirements
* python:3.6 (pip)
* pyenv

### Install Dependencies
Install python 3.6.0, and init pyenv to make python use the right version
```
pyenv install 3.6.0
`eval "$(pyenv init -)"`
```
or install it into a virtual environment which only runs for this project
```
pyenv virtualenv 3.6.0 flask-ndop
echo "flask-ndop" >> .python-version
```
This will switch to your 3.6 flask-ndop environment anytime you enter this project directory

### Install python dependencies
```
pip install -r requirements.txt
cd ndop-mock
pip install -r requirements.txt
cd ..
```
Export ENV_NAME var:
```
export ENV_NAME=ndop-build10
```


### Running

#### Running ndopapp
`FLASK_APP=main.py flask run`

#### Running ndop-mock
`FLASK_APP=ndop-mock/mock.py flask run -p 5001`

### Running tests

API commands can be viewed here https://confluence.digital.nhs.uk/display/NAII/NDOP+Mock+routes

#### Run unit tests
```
python -m unittest discover tests -v
```

#### Run code coverage
```
coverage run --source ndopapp --branch -m unittest discover -v

#Command line
coverage report -m

#creates an html report in htmlcov - index.html
coverage html

#open coverage report in a browser from commandline
open htmlcov/index.html
```

## Setup using docker / docker-compose

Requirements:
* make
* docker
* docker-compose

### Running
This will start the ndop app on port 80 and the nodp-mock api on 5001

```
make run
```

### Running Tests / Coverage
```
make test
```

### Running Coverage
```
make coverage
```

### Building CSS
The css for this project can be found in the `nhsuk-frontend-library repo`

Follow the readme instructions in the repo to build nhsuk.css, then copy it over to `ndopapp/static/css/nhsuk.css`
