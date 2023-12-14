# AnkiConvo
Anki add-on that uses LLMs like ChatGPT to turn your vocabulary flashcards into fresh sentences on the fly and have conversations using your vocabulary.

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation


## License
`anki-convo` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Development
### Branching strategy
This project uses the [https://githubflow.github.io/](GitHub Flow) branching strategy. No pushes to `main` are allowed, only pull requests from feature branches that branch off of `main`. Each feature branch has the following naming convention:
```
git branch <issue-id>-<description-in-kebab-case>
```
It's recommended to open an issue in GitHub before you create a feature branch so that you can more easily track the work and provide much more context.

> **Example**: `git branch 123-cache-cards` is a feature branch implementing caching of cards, referring to Issue 123.
