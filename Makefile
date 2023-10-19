.PHONY: ankisync init

WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")

ankisync:
	rsync -avz . ${WIN_APPDATA}/Anki2/addons21/9999999999 --cvs-exclude --delete

init:
	pre-commit install
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name anki-convo --display-name "Python (anki-convo)"
