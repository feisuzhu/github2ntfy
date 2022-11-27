github2ntfy
===========

Simple web service to transform and forward GitHub Webhook to [ntfy.sh](https://ntfy.sh) notification

```bash
$ poetry install
$ export NTFY_ENDPOINT = 'http://example.com'
$ export NTFY_TOPIC = 'GitHub'
$ export GIT_WEBHOOK_SECRET = 'my_top_secret'
$ poetry run main.py
```
