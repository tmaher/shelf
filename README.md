# Shelf!

## my audiobook shelf

```
git clone ...
cd shelf
export shelfdir=$PWD

# for activation_bytes, target_dir
. secrets.env.sh

pipenv install
pipenv run ./getlib.py

cd "${target_dir}"
"${shelfdir}/generate_personal_podcast.rb"
```

See also https://github.com/inAudible-NG/tables for activation_bytes
