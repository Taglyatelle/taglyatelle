# taglyatelle

> Automate low-value tasks on cloud-based platforms

<!-- badges: start -->
![](https://img.shields.io/badge/github%20version-0.1.0-green.svg)
[![Codecov](https://codecov.io/gh/alexym1/taglyatelle/branch/master/graph/badge.svg)](https://app.codecov.io/gh/alexym1/taglyatelle?branch=master)
<!-- badges: end -->


[taglyatelle](https://github.com/apps/taglyatelle) is an app designed to automate repetitive and low-value tasks on GitHub.


## Key Features

| Feature                      | Description     |
|------------------------------|-----------|
| Synchronize changelog        | Automatically updates the pull request body to reflect changes made to files, ensuring the changelog is accurate and up-to-date. |
| Bump to version              | Automatically increments the new version of your repository when a pull request is merged.          |
| Release automation           | Publishes tag and a release note with changelog details. |
| Slash commands               | Execute commands in PR/issue comments. |


## Slash Commands

Comment on any PR or issue with these commands:

- **`/check_licenses`** - Analyzes dependencies in your files, creates an issue with a detailed license compliance report including package names, license types, and severity levels. ONLY FOR PYTHON PROJECT.


## Create your own GitHub App and use it in local

1. Go to https://github.com/settings/apps
2. Click on `New GitHub App`
3. Fill in the mandatory fileds
4. Give the permissions:

* Read access to metadata
* Read and write access to code, issues, pull requests, and repository hooks

5. Click on `Create GitHub App`
6. Add secret in Webhook section
7. Generate a private key and put it at the root of your repository (don't forget to update your .gitignore)
8. Create a `.env` file with the following ENV variables


| ENV variable                                       | Description                | Example                      |
|----------------------------------------------------|----------------------------|----------------------------- |
| OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, MISTRAL_API_KEY, LLAMA_API_KEY  | API to use a llm 		  |        						 |
| LLM_PROVIDER       								 | name of the provider       | gemini, openai, anthropic ... |
| LLM_MODEL          								 | name of the model          | gemini-2.5-flash             |
| APP_ID       								         | Id of your Github App      |                              |
| PRIVATE_KEY_PATH  								 | path of your private_key   | private_key.pem              |
| WEBHOOK_PROXY_URL                                  | Url of the webhook proxy   | https://smee.io/<token>      |
| WEBHOOK_SECRET                                     | Password        			  | 123456789                    |
| USE_TRACING_REQUEST (optional)                     | Save logs in **logs** folder | true or false              |


9. At last, open two terminals and run each block

```shell
# Start the smee proxy (in one terminal)
export $(grep -v '^#' .env | xargs)
npx smee -u ${WEBHOOK_PROXY_URL} -t http://localhost:8000/taglyatelle/webhooks
```

```shell
# Start the taglyatelle API (in another terminal)
docker pull ghcr.io/alexym1/taglyatelle/taglyatelle_image:latest
docker run -p 8000:8000 --env-file ".env" -v "private_key.pem:/app/private_key.pem:ro" taglyatelle:latest
```

Then, open a PR and observe the app's responses and results.
