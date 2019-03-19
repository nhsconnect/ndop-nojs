#!/usr/bin/env bash
set -e
export PS1=0

function installPython () {
  local PYTHON_VERSION=${1}
  echo "--- Installing Python ${PYTHON_VERSION}"
  wget -qO- https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
  echo 'export PATH="~/.pyenv/bin:$PATH"' >> ~/.bashrc
  echo 'eval "$(pyenv init -)"' >> ~/.bashrc
  echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
  source ~/.bashrc
  pyenv update
  pyenv install ${PYTHON_VERSION}
  pyenv global ${PYTHON_VERSION}
  pip install --upgrade pip
  python --version
}

function installPythonGlobalDependencies () {
  local DIRECTORY=${1}
  echo "--- Installing Python global dependencies"
  pip install -r "${DIRECTORY}/requirements.txt"
}

function installPythonDependencies () {
  local DIRECTORY=${1}
  pushd ${DIRECTORY}
  for d in */; do
    pushd ${d}
    if [ -f "requirements.txt" ]; then
      echo "--- requirements.txt found, installing Python dependencies for ${d%/}"
      pip install -r "requirements.txt" -t .
    fi
    popd
  done
  popd
}

#TODO: once linting is up to scratch remove the set +/-e lines so that it actually
#breaks the build if pylint is not 10/10
function lintPythonLambdas () {
  set +e
  local DIRECTORY=${1}
  local PYLINTRC_PATH="${PWD}/${DIRECTORY}/.pylintrc"
  export COMMON_PATH="${PWD}/${DIRECTORY}/common"

  pushd ${DIRECTORY}
  for d in */; do
    pushd ${d}
    d=${d%/}
    if [ "${d}" = "__pycache__" ]; then
      echo "--- Skipping __pycache__ folder"
    elif [ "${d}" = "common" ]; then
      echo "--- Linting common code"
      find . -iname "*.py" | xargs pylint --rcfile=${PYLINTRC_PATH}
    else
      echo "--- Linting python lambda: ${d}"
      pylint ${d}.py --rcfile=${PYLINTRC_PATH}
    fi
    popd
  done
  popd
  set -e
}

#TODO: Uncomment exit for missing unit tests once we are happy and in a position
#where completley missing units tests is a valid condition to break the build
function unitTestPythonLambdas () {
  local DIRECTORY=${1}
  local UNIT_TESTS_DIRECTORY=${2}
  local PWD=$(pwd)
  local COMMON_PATH="${PWD}/${DIRECTORY}/common"
  local TESTS_PATH="${UNIT_TESTS_DIRECTORY}/${DIRECTORY}"

  if [ -d ${TESTS_PATH} ]; then
    if [ -d ${COMMON_PATH} ]; then
      echo "--- Adding common directory to PYTHONPATH"
      export PYTHONPATH="${COMMON_PATH}:${PYTHONPATH}"
    fi
    echo "--- Running python unit tests"
    python -m unittest discover ${UNIT_TESTS_DIRECTORY}/${DIRECTORY}
  else
    echo "--- ERROR: No unit tests present for ${DIRECTORY}"
    #exit 1
  fi
}

#TODO: see the TODO comment above for unitTestPythonLambdas
function coveragePythonLambdas () {
  local DIRECTORY=${1}
  local UNIT_TESTS_DIRECTORY=${2}
  local COVERAGE_THRESHOLD=${3}
  local PWD=$(pwd)
  local COMMON_PATH="${PWD}/${DIRECTORY}/common"
  local TESTS_PATH="${UNIT_TESTS_DIRECTORY}/${DIRECTORY}"

  if [ -d ${TESTS_PATH} ]; then
    if [ -d ${COMMON_PATH} ]; then
      echo "--- common directory found, adding to PYTHONPATH"
      export PYTHONPATH="${COMMON_PATH}:${PYTHONPATH}"
    fi
    echo "--- Running python coverage"
    coverage run --source=${DIRECTORY} -m unittest discover ${UNIT_TESTS_DIRECTORY}/${DIRECTORY}
    coverage report --fail-under ${COVERAGE_THRESHOLD} -m
  else
    echo "--- ERROR: No unit tests present for ${DIRECTORY}, unable to run covereage"
    #exit 1
  fi
}

function packagePythonLambdas () {
  local DIRECTORY=${1}
  local PATH_TO_COMMON="../common"
  local PATH_TO_COMMON_PYCACHE="../common/__pycache__"

  pushd ${DIRECTORY}
  for d in */; do
    pushd $d
    d=${d%/}
    if [ "${d}" = "__pycache__" ]; then
      echo "--- Skipping __pycache__ folder"
    elif [ "${d}" = "common" ]; then
      echo "--- Skipping common folder"
    else
      echo "--- Packaging lambda: ${d}"
      if [ -d ${PATH_TO_COMMON} ]; then
        echo "--- common folder found"
        if [ -d ${PATH_TO_COMMON_PYCACHE} ]; then
          echo "--- __pycache__ directory found in common, removing"
          rm -rf ${PATH_TO_COMMON_PYCACHE}
        fi
        echo "--- Copying contents of common to ${d}"
        cp ${PATH_TO_COMMON}/* .
      fi
      echo "--- Compiling lambda zip: ${d}.zip"
      d=$(tr "_" "-" <<< "${d}")
      zip -q -r ${d}.zip . --exclude ".gitignore" "requirements.txt" "*__pycache__/*"
      sha256sum ${d}.zip | cut -f1 -d\ | xxd -r -p | base64 > ${d}.zip.hash
      printf %s "$(cat ${d}.zip.hash)" > ${d}.zip.hash
      mv ${d}.zip ../../${CODEBUILD_SOURCE_VERSION}/${d}.zip
      mv ${d}.zip.hash ../../${CODEBUILD_SOURCE_VERSION}/${d}.zip.hash
    fi
    popd
  done
  popd
}

function computeZipHash () {
  local ZIPFILE=${1}

  sha256sum ${ZIPFILE} | cut -f1 -d\ | xxd -r -p | base64 > ${ZIPFILE}.hash
  printf %s "$(cat ${ZIPFILE}.hash)" > ${ZIPFILE}.hash
}

function movePackageToGitMarkerDirectory () {
  local PACKAGENAME=${1}
  local GIT_MARKER=${2}

  if [[ -n "${GIT_MARKER}" ]]; then
    mkdir -p ${GIT_MARKER}
    mv ${PACKAGENAME} ${PACKAGENAME}.hash ./${GIT_MARKER}/
  else
    echo "WARNING: \$GIT_MARKER is undefined, doing nothing" >&2
  fi
}

function syncZipsAndHashesToS3 () {
  local BUCKET_NAME=${1}
  local PROJECT_NAME=${2}
  local GIT_MARKER=${3}
  local KMS_KEY_ALIAS=${4}
  local S3_URI="s3://${BUCKET_NAME}/${PROJECT_NAME}/${GIT_MARKER}"
  echo "--- Uploading hash files to s3"
  echo "--- S3_URI=${S3_URI}"
  aws s3 sync ${GIT_MARKER}/ ${S3_URI} --exclude "*" --include "*.zip" --sse aws:kms --sse-kms-key-id ${KMS_KEY_ALIAS} --content-type "binary/octet-stream" --exact-timestamps
  aws s3 sync ${GIT_MARKER}/ ${S3_URI} --exclude "*" --include "*.zip.hash" --sse aws:kms --sse-kms-key-id ${KMS_KEY_ALIAS} --content-type "text/plain"
}

$@
