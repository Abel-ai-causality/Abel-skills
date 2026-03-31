.PHONY: lint test render verify build-clawhub publish check-refs

# ── Quality ──────────────────────────────────────────────────────
lint:
	ruff check causal-abel/scripts/ maintainers/causal-abel/ scripts/ --fix

test:
	python3 -m pytest tests/ -v

# ── Build ────────────────────────────────────────────────────────
render:
	python3 maintainers/causal-abel/render_skill.py --profile prod --output-dir causal-abel

build-clawhub:
	python3 scripts/build_clawhub_release.py --output-root clawhub

# ── Verification ─────────────────────────────────────────────────
verify:
	@echo "Checking for private endpoint leaks..."
	@! rg -n 'cap-sit|api-sit|localhost|127\.0\.0\.1' causal-abel/ clawhub/causal-abel/ \
		--glob '!*.local.*' --glob '!.gitignore' \
		|| (echo "❌ Private endpoints found in public skill. Fix: remove from causal-abel/ and re-render." && exit 1)
	@echo "✓ No private endpoints in public skill."

check-refs:
	@echo "Checking SKILL.md reference integrity..."
	@cd causal-abel && grep -oP 'references/[a-z/\-]+\.md' SKILL.md | while read ref; do \
		[ -f "$$ref" ] || echo "❌ Missing: $$ref (referenced in SKILL.md). Fix: create the file or remove the reference."; \
	done
	@echo "✓ Reference check complete."

# ── Release ──────────────────────────────────────────────────────
publish:
	python3 scripts/publish_clawhub_release.py --dry-run
	@echo "Dry run complete. Run 'python3 scripts/publish_clawhub_release.py' to publish."
