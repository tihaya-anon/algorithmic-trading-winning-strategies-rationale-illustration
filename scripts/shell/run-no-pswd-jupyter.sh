#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

docker run -d \
  --name jupyter_server \
  --rm -p 8888:8888 \
  -v "$repo_root/chapters":/home/jovyan/work/chapters \
  -v "$repo_root/fixtures":/home/jovyan/work/fixtures \
  -v "$repo_root/scripts":/home/jovyan/work/scripts \
  vectorbt:full-stable \
  start-notebook.py \
  --ServerApp.ip=0.0.0.0 \
  --ServerApp.port=8888 \
  --ServerApp.root_dir=/home/jovyan/work \
  --ServerApp.token='' \
  --ServerApp.password='' \
  --ServerApp.disable_check_xsrf=True \
  --ServerApp.allow_origin='*'

printf "Jupyter Server 2.14.2 is running at:\n\t http://127.0.0.1:8888/lab\n\t http://host.docker.internal:8888/lab\n"
