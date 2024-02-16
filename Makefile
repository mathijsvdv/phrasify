CONFIG_FILES = config-default.mk $(wildcard config.mk)
include $(CONFIG_FILES)

ANKI_ADDON_PATH = ${ANKI_ADDONS_PATH}/${ANKI_ADDON_PACKAGE}
RELEASE_NAME = "${ANKI_ADDON_NAME}-v${ANKI_ADDON_VERSION}"

.PHONY: print-%
print-%:
	@echo $* = $($*)

.PHONY: init
init:
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit autoupdate
	hatch env create
	hatch run ipykernel_install
	hatch run nbstripout_install

.PHONY: ankisync
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

.PHONY: ankimeta
ankimeta:
	cp -f ./src/phrasify/meta.json ${ANKI_ADDON_PATH}/meta.json

.PHONY: ankienv
ankienv:
	if [ $(ANKI_ADDON_COPY_ENV) != "" ]; then \
		cp -f ./src/phrasify/user_files/.env.${ANKI_ADDON_COPY_ENV} ${ANKI_ADDON_PATH}/user_files/.env; \
	fi

.PHONY: ankidev
ankidev: ankisync ankimeta ankienv

.PHONY: build
build: ANKI_ADDON_PATH="$(RELEASE_FOLDER)/$(RELEASE_NAME)"
build: ankisync
	cd $(ANKI_ADDON_PATH) && zip -r9 ../${RELEASE_NAME}.ankiaddon .

.PHONY: clean
clean:
	rm -rf $(RELEASE_FOLDER)

.PHONY: serve
serve:
	uvicorn src.phrasify_api.main:app --port $(CHAIN_API_PORT) --reload

.PHONY: docker_run
docker_run:
	docker build -t mathijsvdv/${IMAGE} .
	docker run --name phrasify -p 8800:8800  mathijsvdv/${IMAGE}

.PHONY: docker_push
docker_push:
	docker build -t mathijsvdv/${IMAGE} .
	docker push mathijsvdv/${IMAGE}

.PHONY: docker_run_ollama
docker_run_ollama:
	docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

.PHONY: deploy_env
deploy_env:
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/envs/$(K8S_ENV)/ --recursive

.PHONY: deploy_phrasify
deploy_phrasify: deploy_env
	kubectl apply -f ./k8s/apps/phrasify.yaml

.PHONY: deploy_ollama
deploy_ollama: deploy_env
	kubectl apply -f ./k8s/apps/ollama.yaml

.PHONY: deploy
# When deploying to `minikube` be sure to run `minikube tunnel` in a separate terminal first
deploy: deploy_phrasify deploy_ollama
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/envs/$(K8S_ENV)/ --recursive
	kubectl apply -f ./k8s/apps/ollama.yaml
	kubectl apply -f ./k8s/apps/phrasify.yaml

.PHONY: undeploy_phrasify
undeploy_phrasify:
	kubectl delete -f ./k8s/apps/phrasify.yaml

.PHONY: undeploy_ollama
undeploy_ollama:
	kubectl delete -f ./k8s/apps/ollama.yaml

.PHONY: undeploy_env
undeploy_env: undeploy_phrasify undeploy_ollama
	kubectl delete -f ./k8s/envs/$(K8S_ENV)/ --recursive
	kubectl delete -f ./k8s/namespaces.yaml

.PHONY: undeploy
undeploy: undeploy_env

.PHONY: health_local
health_local:
	curl -X GET "http://localhost:$(CHAIN_API_PORT)/health"

.PHONY: health_eks
health_eks:
	curl -X GET "http://ankiconvo.mvdvlies.com/health"

.PHONY: eksconfig
eksconfig:
	aws eks update-kubeconfig --name $(EKS_CLUSTER_NAME) --region $(AWS_REGION)
