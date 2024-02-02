# Phrasify
| | |
|--- | --- |
| Testing | [![CI - Test](https://github.com/mathijsvdv/phrasify/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/mathijsvdv/phrasify/actions/workflows/unit-tests.yml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mathijsvdv/phrasify/main.svg)](https://results.pre-commit.ci/latest/github/mathijsvdv/phrasify/main) [![codecov](https://codecov.io/gh/mathijsvdv/phrasify/graph/badge.svg?token=PISQ2ZER6N)](https://codecov.io/gh/mathijsvdv/phrasify) |

[Anki](https://apps.ankiweb.net/) add-on that uses LLMs like ChatGPT to turn your vocabulary flashcards into fresh sentences on the fly and have conversations using your vocabulary.

Anki is a great tool for learning vocabulary, but it's not great at teaching you how to *use* that vocabulary in a sentence. This matters, especially for languages like Ukrainian where each verb and noun can appear in many different forms! Phrasify uses an LLM like GPT 3.5/4 to generate sentences on the fly using your vocabulary. This way, you can practice using your vocabulary in a sentence and start using it in conversations.

For example, say I'm trying to learn the Ukrainian word "дарувати" (to give (a gift)) and I've added it to my deck. Phrasify generates a new relevant sentence every time I review the card:

![gif](assets/Phrasify%20demo%20short.gif)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)
- [Development](#development)
  - [Branching strategy](#branching-strategy)

## Installation
At the moment, Phrasify is not yet available on AnkiWeb. You can install it manually by following the instructions below.
1. Download the latest release from the [releases page](https://github.com/mathijsvdv/phrasify/releases). If you already have Anki installed, you can double-click the .ankiaddon file to install the addon.
2. Phrasify makes use of the OpenAI API to generate sentences. We need to set up the API key in order to use the add-on. To do this, follow these steps:
    1. Sign up for an API key at [OpenAI](https://beta.openai.com/signup/) if you haven't already.
    2. Once you have your API key, you need to add it to your environment variables. You can do this as follows: go to `Tools` > `Add-ons` > (Select Phrasify) > `View Files` in Anki to find the add-on folder. Then navigate to /user_files and create a text file called ".env" with the following contents:
    ```
    OPENAI_API_KEY=your-api-key
    ```
3. Restart Anki and you are good to go!

## License
`phrasify` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Development
### Branching strategy
This project uses the [GitHub Flow](https://githubflow.github.io/]) branching strategy. No pushes to `main` are allowed, only pull requests from feature branches that branch off of `main`. Each feature branch has the following naming convention:
```
git branch <issue-id>-<description-in-kebab-case>
```
It's recommended to open an issue in GitHub before you create a feature branch so that you can more easily track the work and provide much more context.

> **Example**: `git branch 123-cache-cards` is a feature branch implementing caching of cards, referring to Issue 123.
