PYTHON ?= python

.PHONY: setup train predict schemas test e2e confusion clean

setup:
	$(PYTHON) -m pip install -r requirements-sprint11.lock.txt

train:
	$(PYTHON) src/run_sprint10_validation_latency.py

predict:
	$(PYTHON) src/predict_cli_sprint11.py --input examples/input_valid_sprint11.json --output results/prediction_cli_sprint11.json --pretty

schemas:
	$(PYTHON) src/generate_contract_schemas_sprint11.py

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*sprint11.py" -v

e2e:
	$(PYTHON) src/run_e2e_sprint11.py

confusion:
	$(PYTHON) src/generate_confusion_matrices_sprint10.py

clean:
	rm -f results/prediction_cli_sprint11.json results/e2e_output_sprint11.json results/e2e_summary_sprint11.json
