# Source package

Canonical package with no nested `src` directory.

- `agents`: credit, demand, and recommendation engines
- `services`: schemas, training, model registry, company profiles, policy application
- `data_generator`: optional synthetic development data
- `ui`: Streamlit workspace
- `smoke_check.py`: end-to-end validation

Run from the project root with `python -m src.smoke_check` and `python -m streamlit run src/ui/app.py`.
