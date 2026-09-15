

**Question 1:** “`pyproject.toml` gained the dependencies `mlflow`, `torch`, `torchvision`, and `scikit-learn`, plus a CUDA PyTorch package index. `uv.lock` records the exact versions of those packages and their dependencies.”

**Question 2:** “`--backend-store-uri sqlite:///mlflow.db` tells MLflow where to store experiment and run metadata, such as parameters, metrics, IDs, and timestamps. `--default-artifact-root ./mlruns` sets the location for files produced by new experiments, such as saved models. Metadata is recorded information; artifacts are output files.”

**Question 3:** “`mlflow.db` changes whenever runs are logged, and `mlruns/` can contain large model files. Tracking them in Git would create unnecessary commits. DVC tracks our versioned Food-11 data; MLflow already manages the experiment records and artifacts.”

**Question 4:** “When I first called `mlflow.set_experiment("food11")`, MLflow created the experiment automatically because it did not exist. The `food11` experiment then appeared in the MLflow UI.”

**Question 5:** “A parameter is fixed for one run, such as its learning rate or batch size. A metric is measured during or after training, such as loss or accuracy. `log_metric` uses `step=epoch` so MLflow can show how the value changes across epochs; a parameter does not change across epochs.”

**Question 6:** “The run page shows the parameters, metric charts, and logged model. The model is saved on disk under `mlruns/`. For my `rambunctious-cat-365` run, the weights are at `mlruns/1/models/m-c5629294642d4b4f8174faff4ce42a43/artifacts/data/model.pth`.”


**Question 7:** “Among the learning rates I tested with batch size 32, `lr=0.01` gave the best final validation accuracy: **69.53%**. A higher learning rate is not always better; these runs do not show what would happen above 0.01.”

**Question 8:** “The very small learning rate, `0.0001`, reached only **41.15%** validation accuracy after five epochs. `lr=0.01` with batch size 32 was best at **69.53%**. At `lr=0.001`, batch size 32 (**68.70%**) performed slightly better than batch size 64 (**67.24%**).”

**Question 9:** “The best of the four runs I compared was `rambunctious-cat-365`, with `lr=0.01`, batch size 32, and `val_accuracy=69.53%`. Its run ID is **`472545440051494db1432da14514e310`**.”