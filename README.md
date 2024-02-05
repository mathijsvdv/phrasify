# Phrasify
| | |
|--- | --- |
| Testing | [![CI - Test](https://github.com/mathijsvdv/phrasify/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/mathijsvdv/phrasify/actions/workflows/unit-tests.yml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mathijsvdv/phrasify/main.svg)](https://results.pre-commit.ci/latest/github/mathijsvdv/phrasify/main) [![codecov](https://codecov.io/gh/mathijsvdv/phrasify/graph/badge.svg?token=PISQ2ZER6N)](https://codecov.io/gh/mathijsvdv/phrasify) |

[Anki](https://apps.ankiweb.net/) add-on that uses LLMs like ChatGPT to turn your vocabulary flashcards into fresh sentences on the fly.

Anki is a great tool for learning vocabulary, but it's not great at teaching you how to *use* that vocabulary in a sentence. This matters, especially for languages like Ukrainian where each verb and noun can appear in many different forms! Phrasify uses an LLM like GPT 3.5/4 to generate sentences on the fly using your vocabulary. This way, you can practice using your vocabulary in a sentence and start using it in conversations.

For example, say I'm trying to learn the Ukrainian word "дарувати" (to give (a gift)) and I've added it to my deck. Phrasify generates a new relevant sentence every time I review the card:

![gif](assets/Phrasify%20demo%20short.gif)

-----

**Table of Contents**

- [Installation](#installation)
- [Try it out!](#try-it-out)
- [License](#license)
- [Development](#development)
    - [Setting up the development environment](#setting-up-the-development-environment)
    - [Running tests](#running-tests)
    - [Windows installation, WSL development only - Applying the current code to your Anki installation](#windows-installation-wsl-development-only---applying-the-current-code-to-your-anki-installation)
    - [Building the add-on](#building-the-add-on)
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

## Try it out!
Phrasify's automatic card generation can be enabled for a given note type by navigating to `Tools` > `Manage Note Types` > (Select your note type).

If you go to the `Fields` button, you might see fields "Front" and "Back" like this:
![Field Names](assets/field%20names.png)

Phrasify works using a [field filter](https://docs.ankiweb.net/templates/fields.html), by replacing the values in these fields with the generated
sentence. To do this, you need to tell Phrasify which fields to replace. Going back to
`Tools` > `Manage Note Types` > (Select your note type), click on the `Cards` button.

In the `Front Template` and `Back Template`, replace the fields `{{Front}}` with
```
{{phrasify vocab-to-sentence source_lang=English target_lang=Ukrainian source_field=Front target_field=Back:Front}}
```

and `{{Back}}` with
```
{{phrasify vocab-to-sentence source_lang=English target_lang=Ukrainian source_field=Front target_field=Back:Back}}
```

For the default Basic card, the `Front Template` would then look like this:
![Front Template](assets/front%20template.png)

and the `Back Template` would look like this:
![Back Template](assets/back%20template.png)

This will tell Phrasify to replace the fields `Front` and `Back` with the generated sentence
at the spot in the template where `{{phrasify ...:Front}}` and `{{phrasify ...:Back}}` are.

> Be sure to adjust the following arguments of the `{{phrasify...}}` filter to your needs:
> - `source_lang`: source language, i.e. language that you know,
> - `target_lang`: target language, i.e. language that you want to learn,
> - `source_field`: field name for source language: stores the vocabulary in the language that you know,
> - `target_field`: field name for target language: stores the vocabulary in the language that you want to learn.

That's it! When you review a card with the note type you just edited, Phrasify will generate a sentence using the vocabulary on the card and replace the fields `Front` and `Back` with the generated sentence.

## License
`phrasify` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Development
### Setting up the development environment
First, clone the repository:
```bash
git clone https://github.com/mathijsvdv/phrasify.git
```

This repo uses [Hatch](https://github.com/pypa/hatch) for dependency management. I recommend
[using `pipx` to install it globally](https://hatch.pypa.io/latest/install/). To ensure that Visual Studio Code recognizes the virtual environment, set the virtual environment directory ./direnv:
```bash
hatch config set dirs.env.virtual .direnv
```

To set up the virtual environment along with pre-commit hooks and jupyter notebooks, run:
```bash
make init
```

To activate the virtual environment, run:
```bash
hatch shell
```

You will need to set up the OPENAI_API_KEY environment variable as described in the [installation](#installation) section.
In the directory `src/phrasify/user_files` you need to create two files:
- `.env` with the following content:
    ```
    OPENAI_API_KEY=your-api-key
    INIT_PHRASIFY_ADDON=false
    ```
- `.env.prod` with the following content:
    ```
    OPENAI_API_KEY=your-api-key
    INIT_PHRASIFY_ADDON=true
    ```

The `INIT_PHRASIFY_ADDON` environment variable is used to determine whether the field filters from the
add-on should be initialized. We want to disable this in the development environment where
the unit tests are run, but enable it when testing the add-on in Anki (i.e. when [applying the current code to your Anki installation](#windows-installation-wsl-development-only---applying-the-current-code-to-your-anki-installation)).

### Running tests
To run the tests, run:
```bash
hatch run test:run
```

Running the tests with code coverage can be done using:
```bash
hatch run test:cov
```

### Windows installation, WSL development only - Applying the current code to your Anki installation
To apply the current development code to your Anki installation, run:
```bash
make ankidev
```

This copies the current code to your Anki add-ons folder. You can then restart Anki to see the changes.

### Building the add-on
To build the add-on, run:
```bash
make build
```

### Branching strategy
This project uses the [GitHub Flow](https://githubflow.github.io/]) branching strategy. No pushes to `main` are allowed, only pull requests from feature branches that branch off of `main`. Each feature branch has the following naming convention:
```
git branch <issue-id>-<description-in-kebab-case>
```
It's recommended to open an issue in GitHub before you create a feature branch so that you can more easily track the work and provide much more context.

> **Example**: `git branch 123-cache-cards` is a feature branch implementing caching of cards, referring to Issue 123.
