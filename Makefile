.PHONY: help install dev test lint

help: ## List this Makefile's targets with their descriptions
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "%-10s %s\n", $$1, $$2}'

install: ## Install backend and frontend dependencies, and configure git hooks
	uv sync
	npm install --prefix frontend
	git config core.hooksPath .githooks

dev: ## Run the backend and frontend dev servers together
	@export NO_PROXY="localhost,127.0.0.1,*.local"; \
	export no_proxy="$$NO_PROXY"; \
	cleanup() { \
		pkill -f "uvicorn backend.main:app" 2>/dev/null; \
		pkill -f "next dev --hostname" 2>/dev/null; \
		sleep 1; \
		pkill -9 -f "uvicorn backend.main:app" 2>/dev/null; \
		pkill -9 -f "next dev --hostname" 2>/dev/null; \
	}; \
	trap cleanup EXIT INT TERM; \
	echo "⚡ Launching FastAPI backend on port 8000..."; \
	uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 & \
	echo "⏳ Waiting for backend..."; \
	for i in $$(seq 1 30); do curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1 && break; sleep 1; done; \
	echo "🎨 Launching Next.js frontend on port 3000..."; \
	npm run dev --prefix frontend & \
	echo "⏳ Waiting for frontend..."; \
	for i in $$(seq 1 30); do curl -sf http://127.0.0.1:3000 > /dev/null 2>&1 && break; sleep 1; done; \
	open http://127.0.0.1:3000/login; \
	LOCAL_IP=$$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || ipconfig getifaddr bridge0 2>/dev/null); \
	if [ -n "$$LOCAL_IP" ]; then echo "📱 On your phone (same WiFi): http://$$LOCAL_IP:3000/login"; fi; \
	echo "🟢 App is running! Press [CTRL+C] to stop."; \
	wait

test: ## Run backend, frontend, and Sandcastle test suites
	uv run python -m pytest
	npm test --prefix frontend
	node --test .sandcastle/lib/

lint: ## Run backend and frontend linters
	uv run black --check backend tests
	uv run python scripts/check_docs.py
	npm run lint --prefix frontend
