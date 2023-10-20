.PHONY: ankisync init

WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDON_PATH := ${WIN_APPDATA}/Anki2/addons21/9999999999/

ankisync:
	rsync -avz ./src/anki_convo/ ${ANKI_ADDON_PATH}/ \
	--cvs-exclude --delete --filter=':- .gitignore'

init:
	pre-commit install
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name anki-convo --display-name "Python (anki-convo)"
	hatch run python -m nbstripout --install --attributes .gitattributes
