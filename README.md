# Shelf!

## dev setup
1. Install Docker
2. Install Homebrew
3. `brew install pyenv`
4. add `source $(pyenv init -)` to bashrc/equiv & close/reopen terminal
5. `pyenv install 3.11.8`
6. `pyenv global 3.11.8`
7. `pip install poetry==1.8.2`
8. `pyenv global system`  # or whatever you were using previously
9. `git clone https://github.com/.../shelf.git && cd shelf`
10. `poetry install`

## run in dev
```
$ docker image build -t shelf:dev .
$ docker run -it -v ./tmp:/shelf -v ./config:/config -v .:/src --env-file ./secrets.env shelf:dev /bin/sh
```

## run in prod
```
docker run ghcr.io/.../shelf \
    -v /path/to/rssdir:/shelf
    -v /path/to/config:/config
    --env-file secrets.env
```