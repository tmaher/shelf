# Shelf!

## dev environment
Setup
1. Install Docker
2. Install Homebrew
3. `brew install pyenv`
4. add `source $(pyenv init -)` to bashrc/equiv & close/reopen terminal
5. `pyenv install 
4. `pyenv install 

```
$ git clone https://github.com/.../shelf.git
$ docker image build -t shelf:dev . && docker run -it -v ./tmp:/shelf -v ./config:/config -v .:/src --env-file ./secrets.env shelf:dev /bin/sh

## my audiobook shelf

```
docker run ghcr.io/tmaher/shelf \
    -v /path/to/rssdir:/shelf
    -v /path/to/credsdir:/creds
    --env-file secrets.env
```

`secrets.env` needs to contain `activation_bytes`

See also https://github.com/inAudible-NG/tables for activation_bytes
