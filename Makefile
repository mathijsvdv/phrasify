.PHONY: ankisync init serve docker_push deploy undeploy health_local

CHAIN_API_PORT := 8800
IMAGE := anki-convo
WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDON_PATH := ${WIN_APPDATA}/Anki2/addons21/9999999999
SITE_PACKAGES_PATH := ./.direnv/anki-convo/lib/python3.9/site-packages
REQUIREMENTS := yaml openai aiohttp aiosignal async_timeout charset_normalizer frozenlist multidict yarl tqdm dotenv
K8S_ENV?=dev

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
	pre-commit install --hook-type commit-msg
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name anki-convo --display-name "Python (anki-convo)"
	hatch run python -m nbstripout --install --attributes .gitattributes

serve:
	uvicorn src.anki_convo_api.main:app --port $(CHAIN_API_PORT) --reload

docker_run:
	docker build -t mathijsvdv/${IMAGE} .
	docker run --name anki-convo -p 8800:8800  mathijsvdv/${IMAGE}

docker_push:
	docker build -t mathijsvdv/${IMAGE} .
	docker push mathijsvdv/${IMAGE}

# When deploying to `minikube` be sure to run `minikube tunnel` in a separate terminal first
deploy:
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/envs/$(K8S_ENV)/
	kubectl apply -f ./k8s/apps/anki-convo.yaml

undeploy:
	kubectl delete -f ./k8s/apps/anki-convo.yaml

health_local:
	curl -X GET "http://localhost:$(CHAIN_API_PORT)/health"
