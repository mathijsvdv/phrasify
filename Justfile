set dotenv-load

python := `which python`

anki_addon_name := env("ANKI_ADDON_NAME", "Phrasify")
anki_addon_version := env("ANKI_ADDON_VERSION", "0.1.1")
package_name := env("PACKAGE_NAME", "phrasify")
release_folder := env("RELEASE_FOLDER", "./releases")
release_name := anki_addon_name + "-" + anki_addon_version

win_appdata := `wslpath "$(wslvar APPDATA)"`
anki_addons_path := env("ANKI_ADDONS_PATH", win_appdata / "Anki2" / "addons21")
anki_addon_path := anki_addons_path / package_name

requirements := "charset_normalizer dotenv"
anki_addon_copy_env := env("ANKI_ADDON_COPY_ENV", "prod")

chain_api_port := env("CHAIN_API_PORT", "8800")
image := env("IMAGE", "phrasify")
k8s_env := env("K8S_ENV", "dev")

@_default:
	just --list
	echo "\n...with the following variables:"
	just --evaluate

@root:
	echo {{justfile_directory()}}

_install-ipykernel:
	{{python}} -m ipykernel install --user --name phrasify --display-name "Python (phrasify)"

# install the ipykernel for the virtual environment
install-ipykernel:
	hatch run ipykernel-install

_install-nbstripout:
	{{python}} -m nbstripout --install --attributes .gitattributes

# install nbstripout for the virtual environment
install-nbstripout:
	hatch run nbstripout-install

_site-packages-path:
	#!{{python}}
	import sysconfig
	print(sysconfig.get_paths()['purelib'])

# get the path to the site-packages folder
@site-packages-path:
	hatch run site-packages-path

venv:
	rye sync --features api

init: venv
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit autoupdate
	just ipykernel-install
	just nbstripout-install

ankisync addon_path=anki_addon_path:
	if [ ! -d {{addon_path}} ]; then \
		mkdir -p {{addon_path}}; \
	fi
	rsync -avz ./src/phrasify/ {{addon_path}}/ --delete \
	--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
	--exclude ".env" --exclude ".env.*" --exclude "meta.json";
	for req in {{requirements}}; do \
		rsync -avz $(just site-packages-path)/$req {{addon_path}}/lib/ --delete \
		--cvs-exclude --exclude "__pycache__/" --exclude "*.py[cod]" --exclude "*\$py.class" \
		--exclude ".env" --exclude ".env.*"; \
	done

ankimeta addon_path=anki_addon_path:
	cp -f ./src/phrasify/meta.json {{addon_path}}/meta.json

ankienv copy_env=anki_addon_copy_env addon_path=anki_addon_path:
	if [ {{copy_env}} != "" ]; then \
		cp -f ./src/phrasify/user_files/.env.{{copy_env}} {{addon_path}}/user_files/.env; \
	fi

ankidev: ankisync ankimeta ankienv

_test *args="tests":
	{{python}} -m pytest {{args}}

_test-cov *args="tests":
	{{python}} -m pytest {{args}} --cov --cov-report term-missing --cov-report=xml --cov-report=html --junitxml=junit/test-results.xml

# Run the tests
test:
	hatch run test:run

# Run the tests and generate a coverage report
test-cov:
	hatch run test:cov

# Build the Anki addon
build addon_path=(release_folder / release_name): (ankisync addon_path)
	cd {{addon_path}} && zip -r9 ../{{release_name}}.ankiaddon .

clean:
	rm -rf htmlcov
	rm -rf junit
	rm -f .coverage
	rm -f coverage.xml
	rm -rf .pytest_cache
	rm -rf {{release_folder}}
	rm -rf .nox

serve port=chain_api_port:
	hatch run app:serve --port {{port}}

docker-build:
	docker build -t mathijsvdv/{{image}} .

docker-run: docker-build
	docker run --name phrasify -p 8800:8800  mathijsvdv/{{image}}

docker-push: docker-build
	docker build -t mathijsvdv/{{image}} .
	docker push mathijsvdv/{{image}}

docker-run-ollama:
	docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# When deploying to `minikube` be sure to run `minikube tunnel` in a separate terminal first
deploy:
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/envs/$(K8S_ENV)/
	kubectl apply -f ./k8s/apps/ollama.yaml
	kubectl apply -f ./k8s/apps/phrasify.yaml

deploy-ollama:
	kubectl apply -f ./k8s/namespaces.yaml
	kubectl apply -f ./k8s/apps/ollama.yaml

undeploy:
	kubectl delete -f ./k8s/apps/phrasify.yaml

undeploy-ollama:
	kubectl delete -f ./k8s/apps/ollama.yaml

health-local port=chain_api_port:
	curl -X GET "http://localhost:{{port}}/health"
