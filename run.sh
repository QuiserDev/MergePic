#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec .venv/bin/uvicorn main:app --log-config log_config.json "$@"
