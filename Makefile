.PHONY: init
init:
	pip install -r requirements.txt
	pre-commit install


.PHONY: fmt
fmt:
ifdef CI_LINT_RUN
	pre-commit run --all-files --show-diff-on-failure
else
	pre-commit run --all-files
endif


.PHONY: test
test:
	pytest -vvv
