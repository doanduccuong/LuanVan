.PHONY: install test build-web run-api run-vision run-simulator demo-portraits demo-prepare demo-calibrate demo-reset demo-seed demo-simulate demo-enroll demo-replay demo-verify

install:
	cd apps/api && uv sync --dev
	cd services/vision && uv sync --dev
	cd apps/web && npm install

test:
	cd apps/api && uv run pytest
	cd services/vision && uv run pytest
	cd apps/web && npm run build

build-web:
	cd apps/web && npm run build

run-api:
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

run-vision:
	cd services/vision && uv run uvicorn app.main:app --reload --port 8001

run-simulator:
	cd services/simulator && uv run uvicorn app.main:app --reload --port 8002

demo-portraits:
	cd services/vision && uv run python ../../scripts/prepare_customer_portraits.py --count 100

demo-prepare:
	cd services/vision && uv run python ../../scripts/prepare_demo_dataset.py --source "$(DEMO_SOURCE)"

demo-calibrate:
	cd services/vision && uv run python ../../scripts/calibrate_face_threshold.py

demo-reset:
	cd apps/api && uv run python ../../scripts/reset_demo_data.py --confirm RESET-DEMO

demo-seed:
	cd services/vision && uv run python ../../scripts/seed_demo_crm.py

demo-simulate:
	curl --fail --show-error --request POST http://localhost:8002/api/v1/runs --header 'Content-Type: application/json' --data '{"customer_count":100,"seed":20260923}'

demo-enroll:
	cd services/vision && uv run python ../../scripts/enroll_demo_faces.py

demo-replay:
	cd services/vision && uv run python ../../scripts/replay_demo_journeys.py --scenario "$(or $(SCENARIO),all)" --speed "$(or $(SPEED),0)"

demo-verify:
	cd services/vision && uv run python ../../scripts/verify_demo_results.py
