#!/bin/sh -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
pushd $DIR
SRC=weather/bin/activate

if [ -f $SRC ]; then
  source $SRC
else
  python3 -m venv weather
  source $SRC
  pip3 install --upgrade pip3 setuptools wheel
  pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
  pip3 install --upgrade geojson python-dateutil pygsheets numpy oauth2client
fi

popd
