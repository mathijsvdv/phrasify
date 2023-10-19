.PHONY: ankisync

WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")

ankisync:
	rsync -avz . ${WIN_APPDATA}/Anki2/addons21/9999999999 --cvs-exclude --delete
