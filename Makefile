.PHONY: ankisync init

WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")

ankisync:
	rsync -avz ./src/anki_convo ${WIN_APPDATA}/Anki2/addons21/ \
	--cvs-exclude --delete --filter=':- .gitignore'

init:
	pre-commit install
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name anki-convo --display-name "Python (anki-convo)"
	hatch run python -m nbstripout --install --attributes .gitattributes