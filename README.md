# Shelf!

## my audiobook shelf

```
docker run ghcr.io/tmaher/shelf \
    -v /path/to/rssdir:/shelf
    -v /path/to/credsdir:/creds
    --env-file secrets.env
```

`secrets.env` needs to contain `activation_bytes`

See also https://github.com/inAudible-NG/tables for activation_bytes
