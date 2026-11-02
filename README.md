# REASON-X Basic

Beginner-friendly Python project based on the research problem:
**Automated Reasoning and Knowledge-Based Expert Systems for Software Requirement Conflict Detection.**

## Features
- Enter natural-language requirement statements.
- Store requirements in SQLite.
- Enter propositional logic formulas.
- Parse formulas and evaluate them using a truth-table solver.
- Check joint satisfiability.
- Find pairwise conflicting requirements and explain the result.

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```
On Windows, activate with `.venv\\Scripts\\activate`.

## Demo
Click **Load Login Demonstration**, then go to **Check Conflicts** and click **Run Conflict Detection**.
Expected result: UNSAT. R2 and R3 conflict.

## Formula syntax
- `A` proposition
- `!A` NOT
- `A & B` AND
- `A | B` OR
- `A -> B` implication
- Parentheses: `(A | B) & C`

## Limitation
This basic version does not understand arbitrary natural language. The user supplies the logical formula. The truth-table solver is suitable for small examples (up to 18 unique propositions). NLP conversion, SAT/SMT solvers and advanced explanation are future extensions.
