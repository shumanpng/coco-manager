.PHONY: planning-index state-index

planning-index:
	python ./scripts/generate_planning_index.py \
	  --repo-root . \
	  --items-dir planning/items \
	  --out-index planning/INDEX.md \
	  --out-horizons planning/horizons.md

state-index:
	python ./scripts/generate_state_index.py \
	  --repo-root . \
	  --items-dir state/items \
	  --out state/INDEX.md
