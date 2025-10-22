    .PHONY: init activate scaffold diag ship

    init:
	THOTH_PROJECT_ROOT=$(PWD) python3 thoth_loader.py

    activate:
	python3 engine/activate_guard.py && echo "activate thoth"

    scaffold:
	python3 engine/activate_guard.py && echo "build scaffold"

    diag:
	python3 engine/activate_guard.py && echo "run diagnostics persona=thoth_om_builder_v1 show=distortions,gates detail=brief"

    ship:
	python3 engine/activate_guard.py && echo "run diagnostics persona=thoth_om_builder_v1 show=distortions,gates detail=brief"
	@echo ">> Crown Verify your artifact in /artifacts before publishing"
