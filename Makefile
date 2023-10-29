include .env

.PHONY: ankisync init

WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDON_PATH := ${WIN_APPDATA}/Anki2/addons21/9999999999
SITE_PACKAGES_PATH := ./.direnv/anki-convo/lib/python3.9/site-packages
REQUIREMENTS := openai aiohttp aiosignal async_timeout charset_normalizer frozenlist multidict yarl tqdm

ankisync:
	rsync -avz ./src/anki_convo/ ${ANKI_ADDON_PATH}/ --delete \
	--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class";
	for req in ${REQUIREMENTS}; do \
		rsync -avz ${SITE_PACKAGES_PATH}/$$req ${ANKI_ADDON_PATH}/lib/ --delete \
		--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class"; \
	done

	@echo "Replacing OpenAI API Key in 'config.json' with own key"
	@jq '.openaiApiKey = "${OPENAI_API_KEY}"' ./src/anki_convo/config.json > ${ANKI_ADDON_PATH}/config.json
	@echo "Done!"

init:
	pre-commit install
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name anki-convo --display-name "Python (anki-convo)"
	hatch run python -m nbstripout --install --attributes .gitattributes
