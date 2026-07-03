# Makefile for Live Translation

ZIP_FILE = translation-service.zip

.PHONY: proto build-installer bundle lock install shell help

help:
	@echo "Available commands:"
	@echo "  proto            - Regenerate Mumble protobuf files"
	@echo "  lock             - Update dependencies lock file"
	@echo "  lint             - Check code style and type hints"
	@echo "  format           - Format code"
	@echo "  install          - Install dependencies"
	@echo "  shell            - Open a shell in the virtual environment"
	@echo "  test             - Run unit tests and show coverage"

proto:
	@echo "Regenerating protobuf files..."
	uv run --with grpcio-tools python -m grpc_tools.protoc \
	  --proto_path=lib/mumble/src/pymumble_py3 \
	  --python_out=lib/mumble/src/pymumble_py3 \
	  lib/mumble/src/pymumble_py3/Mumble.proto
	@echo "Protobuf files regenerated successfully."

lock:
	uv lock

install:
	uv sync

lint:
	uv run ruff check
	uv run mypy src

format:
	uv run ruff format

shell:
	uv run zsh

test:
	uv run pytest --cov=src tests/
