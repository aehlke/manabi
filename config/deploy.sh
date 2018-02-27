#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

pipenv install --ignore-pipfile --two --deploy

cd playbooks
pipenv run ansible-galaxy install -r requirements.yml --force
pipenv run ansible-playbook deploy.yml "$@"
