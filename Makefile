# Recon Engine - build and test targets
# Requires Python 3.11+ (developed and tested on 3.13).

PYTHON ?= python3.13
SCOPE  ?= lab-runtime/scope.csv
OUTPUT ?= run

.PHONY: test run clean help

help:
	@echo "Targets:"
	@echo "  make test   - run the full test suite (unittest)"
	@echo "  make run    - run the recon engine against the local lab"
	@echo "  make clean  - remove generated run output and caches"

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	cd recon-engine && $(PYTHON) cli.py --target 127.0.0.1 --scope ../$(SCOPE) --output ../$(OUTPUT) --rate 25

clean:
	rm -rf $(OUTPUT)/checkpoint.json $(OUTPUT)/*.tmp
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
