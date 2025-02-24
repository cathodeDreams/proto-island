#!/bin/bash

poetry lock
poetry install
poetry show > poetry_show.txt
poetry env info > poetry_env_info.txt
poetry run pytest > poetry_pytest.txt
tree --gitignore > poetry_directory.txt