.PHONY: ankisync init

CHAIN_API_PORT := 8800
CHAIN_IMAGE := anki-convo-chain
WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDON_PATH := ${WIN_APPDATA}/Anki2/addons21/9999999999
SITE_PACKAGES_PATH := ./.direnv/anki-convo/lib/python3.9/site-packages
REQUIREMENTS := openai aiohttp aiosignal async_timeout charset_normalizer frozenlist multidict yarl tqdm dotenv

ankisync:
	rsync -avz ./src/anki_convo/ ${ANKI_ADDON_PATH}/ --delete \
	--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
	--exclude ".env" --exclude ".env.*";
	for req in ${REQUIREMENTS}; do \
		rsync -avz ${SITE_PACKAGES_PATH}/$$req ${ANKI_ADDON_PATH}/lib/ --delete \
		--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
		--exclude ".env" --exclude ".env.*"; \
	done
	cp -f ./src/anki_convo/user_files/.env.prod ${ANKI_ADDON_PATH}/user_files/.env

init:
	pre-commit install
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name anki-convo --display-name "Python (anki-convo)"
	hatch run python -m nbstripout --install --attributes .gitattributes

serve_chain:
	cd ./k8s/manifests/chain &&	uvicorn app.main:app --port $(CHAIN_API_PORT) --reload

docker_push_chain:
	cd ./k8s/manifests/chain && docker build -t ${CHAIN_IMAGE} .
	docker tag ${CHAIN_IMAGE} mathijsvdv/${CHAIN_IMAGE}
	docker push mathijsvdv/${CHAIN_IMAGE}

deploy_chain:
	kubectl apply -f ./k8s/manifests/chain

deploy_ollama:
	kubectl apply -f ./k8s/manifests/ollama

delete_chain:
	kubectl delete -f ./k8s/manifests/chain

delete_ollama:
	kubectl delete -f ./k8s/manifests/ollama
