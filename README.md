
# NDOP (National Data Opt-out)

The National Data Opt-out Service is a service that allows patients to opt out of their confidential patient information being used for research and planning, the website project consists of multiple repositories ([ndop-back-end](https://github.com/nhsconnect/ndop-back-end), [ndop-front-end](https://github.com/nhsconnect/ndop-front-end), [ndop-nojs](https://github.com/nhsconnect/ndop-nojs))


# NDOP no-js Flask App

## What is this project:

1. This project is intended to replace the NDOP javascript client with a flask app runnning on the serverside to serve the html pages for people with disabled javascript browser.
2. It makes call directly to the NDOP API, does the same job is being done by the screen lambdas in the [ndop-front-end](https://github.com/nhsconnect/ndop-front-end) repo.
3. The flask app will run on a single AWS lambda, we use [Zappa](https://github.com/Miserlou/Zappa) to generate the code and deploy to lambda.
4. Mock API project is mocking the existing NDOP front-end API.

## Building a zappa package for deployment into an NDOP AWS environment with terraform

Use the `start-build` target to make, with a `git_marker` argument as appropriate. This will spin up a docker container to build the zappa package, and upload the resultant zip file to the build artifacts bucket in S3. Note that you should have valid AWS session credentials in the target account.

The command will upload the generated code to S3 bucket where it then can be used from the bucket to deploy to the lambda.

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
It needes to set the ENV_NAME variable to local to disable the https restrictions
`export ENV_NAME=local`
`export CLIENT_FACING_URL="http://localhost:5000/"`
`export API_URL=<env-url>`
`export FLASK_ENV=production`
`export FLASK_APP=main`
`flask run -p 5000`

#### Running ndop-mock
`FLASK_APP=ndop-mock/mock.py flask run -p 5001`

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

