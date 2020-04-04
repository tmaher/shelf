```
cd shelf

# for activation_bytes
. secrets.env.sh

pipenv install
pipenv run ./getlib.py

export target_dir=/path/to/nginx/directory

for audible_file in audiobooks/*.aax; do
  audible_name=$(basename -s .aax "${audible_file}")
  ffmpeg -activation_bytes "${activation_bytes}" \
    -i "${audible_file}" -c:a copy \
    "${target_dir}/${audible_name}.m4a"
done

export GOPATH="${PWD}/gopath"
export PATH="${GOPATH}/bin:$PATH"
go install github.com/lpar/podcaster



```
