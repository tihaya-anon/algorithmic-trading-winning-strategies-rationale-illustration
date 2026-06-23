#!/usr/bin/env bash
set -euo pipefail

docker run -d \
  --rm -p 8888:8888 \
  -v "$PWD":/home/jovyan/work \
  vectorbt:full-stable \
  start-notebook.py \
  --ServerApp.ip=0.0.0.0 \
  --ServerApp.port=8888 \
  --ServerApp.token='' \
  --ServerApp.password='' \
  > /dev/null

printf "Jupyter Server 2.14.2 is running at: http://127.0.0.1:8888/lab \n"
