ANKI_ADDON_NAME = Phrasify
ANKI_ADDON_PACKAGE = phrasify
ANKI_ADDON_VERSION = 0.1.0
RELEASE_FOLDER = "./releases"
WIN_APPDATA = $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDONS_PATH = ${WIN_APPDATA}/Anki2/addons21
SITE_PACKAGES_PATH = $(shell hatch run site_packages_path)
REQUIREMENTS = charset_normalizer dotenv
ANKI_ADDON_COPY_ENV = "prod"
CHAIN_API_PORT = 8800
IMAGE = phrasify
K8S_ENV?=dev
