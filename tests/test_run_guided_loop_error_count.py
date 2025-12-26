from __future__ import annotations


def test_count_compiler_errors_prefers_javac_summary() -> None:
    from scripts.run_guided_loop import count_compiler_errors

    javac_output = """\
ExpressionEvaluator.java:81: error: bad operand types for binary operator '=='
if (token != null && token.type == '+' || token.type == '-') {
                                ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:81: error: bad operand types for binary operator '=='
if (token != null && token.type == '+' || token.type == '-') {
                                                     ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:84: error: bad operand types for binary operator '=='
                    result += token.type == '+' ? nextTerm : -nextTerm;
                                         ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:96: error: bad operand types for binary operator '=='
                if (token.type == '*' || token.type == '/') {
                               ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:96: error: bad operand types for binary operator '=='
                if (token.type == '*' || token.type == '/') {
                                                    ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:99: error: bad operand types for binary operator '=='
                    result *= token.type == '*' ? nextFactor : result / nextFactor;
                                         ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:109: error: bad operand types for binary operator '=='
            if (token.type == '(') {
                           ^
  first type:  Object
  second type: char
ExpressionEvaluator.java:112: error: bad operand types for binary operator '=='
                if (pos < tokens.size() && tokens.get(pos).type == ')') {
                                                                ^
  first type:  Object
  second type: char
8 errors
"""

    # This should report the number of errors (8), not the number of non-empty stderr lines.
    assert count_compiler_errors(javac_output) == 8


def test_count_compiler_errors_counts_error_lines_without_summary() -> None:
    from scripts.run_guided_loop import count_compiler_errors

    gcc_like = """\
file.c:10:5: error: expected ';' before 'return'
file.c:11:1: error: expected declaration or statement at end of input
"""

    assert count_compiler_errors(gcc_like) == 2
