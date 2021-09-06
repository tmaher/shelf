# Shelf!

## [old] my audiobook shelf

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

## new for audible module 0.5.5
```
git clone ...
cd shelf
export shelfdir=$PWD

# for activation_bytes, target_dir
. secrets.env.sh

pipenv install

## WARNING - sensitive files get created in the creds directory.
#
## start first time only section - to get long-lived creds (like years)
## this will require you sign in via browser to amazon.com with one or more
## regional accounts. After successful MFA challenges, you'll
## fail an oauth flow midway through, but there's a live access token
## in the browser nav bar now, so paste that into the terminal prompt.
## The python script will take it from there. You should only have to
## do this once, unless the creds directory gets nuked.

# US account
export audible_locale=us
pipenv run ./register.py

# UK account
export audible_locale=uk
pipenv run ./register.py

unset audible_locale
## end first time only section for credential registration

pipenv run get_library_catalog.py

```

See also https://github.com/inAudible-NG/tables for activation_bytes
