<div align="center">
    <picture><img src="https://raw.githubusercontent.com/Taglyatelle/taglyatelle/master/taglyatelle.png" alt="logo" width="200"></picture>
    <br/><br/>
    <p> Delegate tasks to your AI agent on multiple Git hosting services
    <br/>
    <p>
        <a href="https://github.com/Taglyatelle/taglyatelle/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Apache 2.0 License"></a>
        <a href="https://github.com/apps/taglyatelle"><img src="https://img.shields.io/badge/GitHub_App-taglyatelle-purple.svg" alt="GitHub App"></a>
        <img src="https://img.shields.io/badge/version-0.2.0-green.svg" alt="Version">
        <a href="https://app.codecov.io/gh/Taglyatelle/taglyatelle?branch=master"><img src="https://codecov.io/gh/Taglyatelle/taglyatelle/branch/master/graph/badge.svg" alt="Codecov"></a>
    </p>
</div>


## Key Features

| Feature                      | Description     |
|------------------------------|-----------|
| Synchronize changelog        | Automatically updates the pull request body to reflect changes made to files, ensuring the changelog is accurate and up-to-date. |
| Bump to version              | Automatically increments the new version of your repository when a pull request is merged.          |
| Release automation           | Publishes tag and a release note with changelog details. |
| Slash commands               | Execute commands in PR/issue comments. |


## Slash Commands

Comment on any PR or issue with these commands:

- **`/check_licenses`** - Analyzes dependencies in your files, creates an issue with a detailed license compliance report including package names, license types, and severity levels.

> Supported languages: Python and R
