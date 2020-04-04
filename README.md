```
cd shelf

# for activation_bytes
. secrets.env.sh

pipenv install
pipenv run ./getlib.py

export GOPATH=$(pwd)/gopath
export PATH=${GOPATH}/bin:$PATH
go install github.com/lpar/podcaster

```
