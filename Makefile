.PHONY: ankisync init serve docker_push deploy undeploy health_local

CHAIN_API_PORT := 8800
IMAGE := phrasify
WIN_APPDATA := $(shell wslpath "$$(wslvar APPDATA)")
ANKI_ADDON_PATH := ${WIN_APPDATA}/Anki2/addons21/9999999999
SITE_PACKAGES_PATH := ./.direnv/phrasify/lib/python3.9/site-packages
REQUIREMENTS := charset_normalizer dotenv
K8S_ENV?=dev

ankisync:
	rsync -avz ./src/phrasify/ ${ANKI_ADDON_PATH}/ --delete \
	--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
	--exclude ".env" --exclude ".env.*";
	for req in ${REQUIREMENTS}; do \
		rsync -avz ${SITE_PACKAGES_PATH}/$$req ${ANKI_ADDON_PATH}/lib/ --delete \
		--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
		--exclude ".env" --exclude ".env.*"; \
	done
	cp -f ./src/phrasify/user_files/.env.prod ${ANKI_ADDON_PATH}/user_files/.env

init:
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit autoupdate
	hatch env create
	hatch run python -m ipykernel install --user --name phrasify --display-name "Python (phrasify)"
	hatch run python -m nbstripout --install --attributes .gitattributes

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
