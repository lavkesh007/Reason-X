import sqlite3
from itertools import product
import re
import streamlit as st

DB = "requirements.db"

def setup():
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS requirements(
            req_id TEXT PRIMARY KEY, statement TEXT NOT NULL, formula TEXT NOT NULL)""")

def save_requirement(req_id, statement, formula):
    with sqlite3.connect(DB) as con:
        con.execute("INSERT OR REPLACE INTO requirements VALUES(?,?,?)", (req_id, statement, formula))

def get_requirements():
    with sqlite3.connect(DB) as con:
        return con.execute("SELECT req_id, statement, formula FROM requirements ORDER BY req_id").fetchall()

def clear_requirements():
    with sqlite3.connect(DB) as con:
        con.execute("DELETE FROM requirements")

def tokenize(text):
    pattern = r"\s*(->|[()!&|]|[A-Za-z_][A-Za-z0-9_]*)"
    tokens, pos = [], 0
    while pos < len(text):
        match = re.match(pattern, text[pos:])
        if not match:
            raise ValueError(f"Invalid character near: {text[pos:]}")
        tokens.append(match.group(1))
        pos += match.end()
    return tokens

class Parser:
    def __init__(self, text):
        self.tokens = tokenize(text)
        self.pos = 0
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def take(self, expected=None):
        token = self.peek()
        if token is None or (expected and token != expected):
            raise ValueError(f"Expected {expected or 'token'}, found {token}")
        self.pos += 1
        return token
    def parse(self):
        if not self.tokens: raise ValueError("Formula cannot be empty.")
        result = self.implication()
        if self.peek() is not None: raise ValueError(f"Unexpected token: {self.peek()}")
        return result
    def implication(self):
        left = self.disjunction()
        if self.peek() == "->":
            self.take("->")
            return ("implies", left, self.implication())
        return left
    def disjunction(self):
        left = self.conjunction()
        while self.peek() == "|":
            self.take("|")
            left = ("or", left, self.conjunction())
        return left
    def conjunction(self):
        left = self.unary()
        while self.peek() == "&":
            self.take("&")
            left = ("and", left, self.unary())
        return left
    def unary(self):
        token = self.peek()
        if token == "!":
            self.take("!")
            return ("not", self.unary())
        if token == "(":
            self.take("(")
            node = self.implication()
            self.take(")")
            return node
        if token and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            return ("atom", self.take())
        raise ValueError(f"Expected proposition or '(', found {token}")

def evaluate(node, values):
    kind = node[0]
    if kind == "atom": return values[node[1]]
    if kind == "not": return not evaluate(node[1], values)
    left, right = evaluate(node[1], values), evaluate(node[2], values)
    if kind == "and": return left and right
    if kind == "or": return left or right
    if kind == "implies": return (not left) or right
    raise ValueError("Unknown operator")

def get_atoms(node):
    if node[0] == "atom": return {node[1]}
    found = set()
    for part in node[1:]:
        if isinstance(part, tuple): found |= get_atoms(part)
    return found

def is_satisfiable(requirements):
    parsed = [(r[0], r[1], Parser(r[2]).parse()) for r in requirements]
    names = sorted(set().union(*(get_atoms(item[2]) for item in parsed)))
    if len(names) > 18:
        raise ValueError("Truth-table solver supports up to 18 propositions.")
    for bits in product([False, True], repeat=len(names)):
        assignment = dict(zip(names, bits))
        if all(evaluate(item[2], assignment) for item in parsed):
            return True, assignment
    return False, None

def find_conflict_pairs(requirements):
    found = []
    for i in range(len(requirements)):
        for j in range(i + 1, len(requirements)):
            pair = [requirements[i], requirements[j]]
            sat, _ = is_satisfiable(pair)
            if not sat: found.append((pair[0], pair[1]))
    return found

# def main():
#     setup()
#     st.set_page_config(page_title="REASON-X Basic", page_icon="🧠", layout="centered")
#     st.title("🧠 REASON-X Basic")
#     st.subheader("Software Requirement Conflict Detection")
#     st.write("A simple knowledge-based system using propositional logic and truth-table reasoning.")
#     tab1, tab2, tab3 = st.tabs(["Add Requirements", "Knowledge Base", "Check Conflicts"])
#     with tab1:
#         st.markdown("Operators: `!` NOT · `&` AND · `|` OR · `->` IMPLIES")
#         with st.form("add", clear_on_submit=True):
#             rid = st.text_input("Requirement ID", placeholder="R1")
#             statement = st.text_area("Requirement in natural language")
#             formula = st.text_input("Logical formula", placeholder="valid_credentials -> login_allowed")
#             submitted = st.form_submit_button("Save Requirement")
#             if submitted:
#                 if not rid.strip() or not statement.strip() or not formula.strip():
#                     st.error("Complete all fields.")
#                 else:
#                     try:
#                         Parser(formula).parse()
#                         save_requirement(rid.strip(), statement.strip(), formula.strip())
#                         st.success("Requirement saved.")
#                     except Exception as e:
#                         st.error(f"Invalid formula: {e}")
#         if st.button("Load Login Demonstration"):
#             for item in [
#                 ("R1", "Allow login when credentials are valid.", "V -> L"),
#                 ("R2", "Deny login when credentials are invalid.", "!V -> !L"),
#                 ("R3", "Allow login when credentials are invalid.", "!V -> L")
#             ]: save_requirement(*item)
#             st.success("Demo requirements loaded.")
#     with tab2:
#         rows = get_requirements()
#         if rows:
#             st.dataframe([{"ID":r[0],"Requirement":r[1],"Formula":r[2]} for r in rows],
#                          use_container_width=True, hide_index=True)
#             if st.button("Clear Knowledge Base"):
#                 clear_requirements()
#                 st.rerun()
#         else: st.info("No requirements stored.")
#     with tab3:
#         rows = get_requirements()
#         if st.button("Run Conflict Detection", type="primary"):
#             if not rows: st.warning("Add requirements first.")
#             else:
#                 try:
#                     sat, model = is_satisfiable(rows)
#                     if sat:
#                         st.success("SAT: All encoded requirements are consistent.")
#                         st.write("Example satisfying assignment:")
#                         st.json(model)
#                     else:
#                         st.error("UNSAT: The complete set contains a contradiction.")
#                         pairs = find_conflict_pairs(rows)
#                         if pairs:
#                             st.subheader("Conflicting pairs")
#                             for a,b in pairs:
#                                 st.warning(f"{a[0]} conflicts with {b[0]}")
#                                 st.write(f"- {a[1]} (`{a[2]}`)")
#                                 st.write(f"- {b[1]} (`{b[2]}`)")
#                         else:
#                             st.info("Conflict involves three or more requirements; no pairwise conflict found.")
#                 except Exception as e: st.error(str(e))
#     st.divider()
#     st.caption("Research prototype: results apply to formulas entered. Natural-language statements must be formalized and checked by the user.")

# if __name__ == "__main__":
#     main()
