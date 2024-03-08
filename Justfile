set dotenv-load

python := "python"
_uv_windows_activate := ".venv\\Scripts\\activate"
_uv_unix_activate := "source .venv/bin/activate"
_uv_windows_python := ".venv\\Scripts\\python.exe"
_uv_unix_python := ".venv/bin/python"

anki_addon_name := env("ANKI_ADDON_NAME", "Phrasify")
anki_addon_version := env("ANKI_ADDON_VERSION", "0.1.1")
package_name := env("PACKAGE_NAME", "phrasify")
release_folder := env("RELEASE_FOLDER", "./releases")
release_name := anki_addon_name + "-" + anki_addon_version

# Path to Anki folder - depends on OS
# See https://docs.ankiweb.net/files.html?highlight=anki%20folder#file-locations
anki_path_default := if os() == "linux" {
	```
	if uname -a | grep -q "microsoft"; then
		# WSL
		echo "$(wslpath $(wslvar APPDATA))/Anki2";
	else
		# Linux
		echo "~/.local/share/Anki2";
	fi
	```
} else if os() == "windows" {
	replace(`echo "$APPDATA\Anki2"`, "\\", "/")
} else if os() == "macos" {
	`echo "~/Library/Application Support/Anki2"`
} else {
	""
}
anki_path := env("ANKI_PATH", anki_path_default)
anki_addons_path := env("ANKI_ADDONS_PATH", anki_path / "addons21")
anki_addon_path := anki_addons_path / package_name

requirements := "charset_normalizer dotenv"
anki_addon_copy_env := env("ANKI_ADDON_COPY_ENV", "prod")

api_port := env("API_PORT", "8800")
serve_args := "--port " + api_port
image := env("IMAGE", "phrasify")
k8s_env := env("K8S_ENV", "dev")

@_default:
	just --list
	echo "\n...with the following variables:"
	just --evaluate

@root:
	echo "{{replace(justfile_directory(), "\\", "/")}}"

@python-version level="3":
	{{python}} -c "import sys; print('.'.join(map(str, sys.version_info[:{{level}}])))"

@_site-packages-path:
    {{python}} -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"

# get the path to the site-packages folder
@site-packages-path:
	hatch run site-packages-path

_install-ipykernel:
	{{python}} -m ipykernel install --user --name phrasify --display-name "Python (phrasify)"

# install the ipykernel for the virtual environment
install-ipykernel:
	hatch run install-ipykernel

_install-nbstripout:
	{{python}} -m nbstripout --install --attributes .gitattributes

# install nbstripout for the virtual environment
install-nbstripout:
	hatch run install-nbstripout

init:
	pre-commit install
	pre-commit install --hook-type commit-msg
	pre-commit autoupdate
	just install-ipykernel
	just install-nbstripout

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
	INIT_PHRASIFY_ADDON=false {{python}} -m pytest {{args}}

_test-cov *args="tests":
	echo "Python used for _test-cov: $(which python)"
	INIT_PHRASIFY_ADDON=false {{python}} -m pytest {{args}} --cov --cov-report term-missing --cov-report=xml --cov-report=html --junitxml=junit/test-results.xml

# Run the tests
test:
	hatch run test:run

# Run the tests and generate a coverage report
test-cov:
	hatch run test:cov

_uv-venv system_flag="":
	if [ ! -d .venv ] && [ "{{system_flag}}" != "--system" ]; then \
		uv venv; \
	fi

_uv-pip-install-test system_flag="":
	echo "Python used during install: $(which python)" && \
	uv pip install {{system_flag}} -r requirements/test.py$(just python-version 2).txt 'phrasify @ .'

_ci-test system_flag="":
	just _uv-pip-install-test "{{system_flag}}"
	just _test-cov

[unix]
_ci-test-in-venv: _uv-venv
	#!/bin/bash
	{{_uv_unix_activate}}
	just _ci-test

[windows]
_ci-test-in-venv: _uv-venv
	#!/bin/sh
	{{_uv_windows_activate}}
	just _ci-test

# Run the tests in CI while using UV to install the requirements. Be sure to keep the `system_flag` empty when running the tests locally
ci-test system_flag="":
	if [ "{{system_flag}}" = "--system" ]; then \
		just _ci-test "{{system_flag}}"; \
	else \
		just _ci-test-in-venv; \
	fi

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

_serve *args=serve_args:
	{{python}} -m uvicorn src.phrasify_api.main:app {{args}} --reload

serve *args=serve_args:
	hatch run app:serve {{args}}

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

health-local port=api_port:
	curl -X GET "http://localhost:{{port}}/health"
