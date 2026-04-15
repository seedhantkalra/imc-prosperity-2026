# IMC Prosperity 2026

Shared repository for strategy development, local analysis, and later backtesting/visualization.

## Repo layout

```text
imc-prosperity-2026/
├── .gitignore
├── README.md
├── algo.py
├── backtester/
├── utils/
├── data/
├── strategies/
└── tests/
```

## Working agreement

- `main` stays stable.
- No one pushes directly to `main`.
- Each person works on their own branch.
- Merge through pull requests only.
- Raw CSVs go in `data/` and are not tracked by git.

## Suggested branch naming

- `seedhant/setup-repo`
- `kalra/emeralds-mm`
- `rehan/tomatoes-analysis`
- `mehdi/mean-reversion`
- `niall/visualizer-spikes`

## Where code goes

- `algo.py`: submission wrapper
- `strategies/`: mergeable strategy files
- `tests/<name>/`: personal sandbox / notebooks
- `utils/`: shared helpers
- `backtester/`: reserved for simulator code later
- `data/`: local CSVs only

## First-time setup

```bash
git clone <repo-url>
cd imc-prosperity-2026
python -m venv .venv
source .venv/bin/activate
```

## Typical workflow

```bash
git checkout -b yourname/short-feature-name
git add .
git commit -m "Add initial work"
git push -u origin yourname/short-feature-name
```

Then open a pull request into `main`.

## Pull request checklist

- Code runs locally
- No CSVs accidentally committed
- No notebook checkpoint files committed
- Imports are clean
- Short PR description explains the change

## Backtester Setup

We are using the Prosperity 4 backtester package.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


