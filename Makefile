.PHONY: ankienv ankisync init serve docker_push deploy undeploy health_local

PHRASIFY_VERSION := 0.1.0
CHAIN_API_PORT := 8800
IMAGE := phrasify
WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDON_PATH := ${WIN_APPDATA}/Anki2/addons21/phrasify
ANKI_ADDON_COPY_ENV := "prod"
RELEASE_FOLDER := "./releases"
RELEASE_NAME := "Phrasify-v${PHRASIFY_VERSION}"
SITE_PACKAGES_PATH = $(shell hatch run site_packages_path)
REQUIREMENTS := charset_normalizer dotenv
K8S_ENV?=dev

init:
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name phrasify --display-name "Python (phrasify)"
	hatch run python -m nbstripout --install --attributes .gitattributes

ankisync:
	if [ ! -d ${ANKI_ADDON_PATH} ]; then \
		mkdir -p ${ANKI_ADDON_PATH}; \
	fi
	rsync -avz ./src/phrasify/ ${ANKI_ADDON_PATH}/ --delete \
	--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
	--exclude ".env" --exclude ".env.*" --exclude "meta.json";
	for req in ${REQUIREMENTS}; do \
		rsync -avz ${SITE_PACKAGES_PATH}/$$req ${ANKI_ADDON_PATH}/lib/ --delete \
		--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
		--exclude ".env" --exclude ".env.*"; \
	done

ankimeta:
	cp -f ./src/phrasify/meta.json ${ANKI_ADDON_PATH}/meta.json

ankienv:
	if [ $(ANKI_ADDON_COPY_ENV) != "" ]; then \
		cp -f ./src/phrasify/user_files/.env.${ANKI_ADDON_COPY_ENV} ${ANKI_ADDON_PATH}/user_files/.env; \
	fi

ankidev: ankisync ankimeta ankienv

build: ANKI_ADDON_PATH="$(RELEASE_FOLDER)/$(RELEASE_NAME)"
build: ankisync
	cd $(ANKI_ADDON_PATH) && zip -r9 ../${RELEASE_NAME}.ankiaddon .

clean:
	rm -rf $(RELEASE_FOLDER)

serve:
	uvicorn src.phrasify_api.main:app --port $(CHAIN_API_PORT) --reload

docker_run:
	docker build -t mathijsvdv/${IMAGE} .
	docker run --name phrasify -p 8800:8800  mathijsvdv/${IMAGE}

docker_push:
	docker build -t mathijsvdv/${IMAGE} .
	docker push mathijsvdv/${IMAGE}

docker_run_ollama:
	docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# When deploying to `minikube` be sure to run `minikube tunnel` in a separate terminal first
deploy:
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/envs/$(K8S_ENV)/
	kubectl apply -f ./k8s/apps/ollama.yaml
	kubectl apply -f ./k8s/apps/phrasify.yaml

deploy_ollama:
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/apps/ollama.yaml

undeploy:
	kubectl delete -f ./k8s/apps/phrasify.yaml

undeploy_ollama:
	kubectl delete -f ./k8s/apps/ollama.yaml

health_local:
	curl -X GET "http://localhost:$(CHAIN_API_PORT)/health"
