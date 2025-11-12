# Contributing

## Get Started

1. Setup the project

```shell
git clone https://github.com/alexym1/taglyatelle.git
source .venv/bin/activate
make install-prod
```

2. Create a branch (from the master branch)

```shell
git checkout -b branch_name
```

3. Making changes, and check your work:

```shell
make preco
make unittest
```

5. Commit

```shell
git add .
git commit -m "your message"
```

6. Push your branch

```shell
git push origin branch_name
```


## Create a pull request

1. Test the webhook events

```shell
# Start the smee proxy (in one terminal)
export $(grep -v '^#' .env | xargs)
npx smee -u ${WEBHOOK_PROXY_URL} -t http://localhost:8000/taglyatelle/webhooks
```

```shell
# Method n°1: Start the taglyatelle API (in another terminal)
make docker-build
make docker-run

## Method n°2: run the API (not recommanded)
uvicorn taglyatelle.exposition.taglyatelle_api:app --host 0.0.0.0 --port 8000
```

Then, trigger a webhook and check the app's response and results.
Don't forget to include your own ENV variables in `.env`.


2. Run make commands

```shell
make preco
make unittest
make bump2version XXXXX` (choices : major / minor / patch)
```

3. Create a PR from your branch to master

4. Review the PR and merge it.
