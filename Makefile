style:
	@echo "Run black" && \
	black . && \
	echo "Run isort" && \
	isort . && \
	echo "Run ruff" && \
	ruff . --fix