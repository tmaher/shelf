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

rsync -avP audiobooks/*.{m4a,jpg} "${target_dir}/"
cd "${target_dir}"
"${shelfdir}/generate_personal_podcast.rb"
```
