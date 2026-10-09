.PHONY: install test build-web run-api run-vision run-simulator demo-prepare demo-prepare-fairface demo-calibrate demo-reset demo-seed demo-simulate demo-sequence-experiment demo-enroll demo-replay demo-analyze demo-verify demo-evidence demo-sequence-evidence

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

demo-prepare:
	@test -n "$(KDEF_ROOT)" || (echo "Thiếu KDEF_ROOT=/duong/dan/toi/KDEF" && exit 1)
	cd services/vision && uv run python ../../scripts/prepare_kdef_demo.py --kdef-root "$(KDEF_ROOT)" --customer-count "$(or $(CUSTOMER_COUNT),5)" --experiment-run-id "$(or $(EXPERIMENT_RUN_ID),KDEF-DEMO-20261008)"

demo-prepare-fairface:
	cd services/vision && uv run python ../../scripts/prepare_demo_dataset.py

demo-calibrate:
	cd services/vision && uv run python ../../scripts/calibrate_face_threshold.py

demo-reset:
	cd apps/api && DATABASE_URL="$(or $(DATABASE_URL),postgresql+psycopg://touchpoint:touchpoint@127.0.0.1:5432/touchpoint)" uv run python ../../scripts/reset_demo_data.py --confirm RESET-DEMO

demo-seed:
	cd services/vision && uv run python ../../scripts/seed_demo_crm.py

demo-simulate:
	curl --fail --show-error --request POST http://localhost:8002/api/v1/runs --header 'Content-Type: application/json' --data '{"customer_count":100,"seed":20260923}'

demo-sequence-experiment:
	cd apps/api && uv run python ../../scripts/run_controlled_sequence_experiment.py --run-id "$(or $(SIMULATION_RUN_ID),SIM-CONTROLLED-20261008)" --seed "$(or $(SEED),20261008)"

demo-enroll:
	cd services/vision && uv run python ../../scripts/enroll_demo_faces.py

demo-replay:
	cd services/vision && uv run python ../../scripts/replay_demo_journeys.py --scenario "$(or $(SCENARIO),all)" --speed "$(or $(SPEED),0)" --minimum-pass-rate "$(or $(MINIMUM_PASS_RATE),1)"

demo-analyze:
	cd services/vision && uv run python ../../scripts/run_sequence_analysis.py --source-type CAMERA --source-run-id "$(or $(EXPERIMENT_RUN_ID),KDEF-DEMO-20261008)"

demo-verify:
	cd services/vision && uv run python ../../scripts/verify_demo_results.py

demo-evidence:
	cd apps/web && node ../../scripts/capture_chapter4.mjs
	cd apps/web && node ../../scripts/capture_chapter5.mjs

demo-sequence-evidence:
	@test -n "$(SOURCE_RUN_ID)" || (echo "Thiếu SOURCE_RUN_ID" && exit 1)
	SOURCE_RUN_ID="$(SOURCE_RUN_ID)" SOURCE_TYPE="$(or $(SOURCE_TYPE),SIMULATOR)" EXPECTED_USED_VISITS="$(or $(EXPECTED_USED_VISITS),125)" EXPECTED_K="$(EXPECTED_K)" node scripts/capture_sequence_analysis.mjs
