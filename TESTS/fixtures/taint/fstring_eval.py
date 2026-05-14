"""Fixture: f-string propagation into eval() — code injection via JSON body."""

from flask import request


def calculate():
    user_input = request.json  # taint source
    cmd = f"result = {user_input}"  # hop 1 — f-string propagation
    eval(cmd)  # sink (hop 2)


def evaluate_expr():
    expr = request.args.get("expr")  # taint source (1 hop direct)
    eval(expr)  # sink


def safe_calculate(x: int, y: int):
    # no request data — should produce 0 findings
    result = x + y
    return result
