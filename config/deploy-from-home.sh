#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

ACCOUNT_NAME=manabi LABEL="Manabi Ansible Vault" ./deploy.sh --vault-password-file ~/src/manabi/config/playbooks/vault_password_file "$@"
