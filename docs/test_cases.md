# Canonical Test Problems

This catalog tracks the seeded programming scenarios we use when generating failing code samples from LLMs. Each entry describes the specification, required features, and representative test vectors so generator prompts stay consistent across languages.

## 1. Expression Evaluator (Mini Calculator with Precedence)

| Attribute | Details |
| --- | --- |
| **ID** | `expr_eval_v1` |
| **Description** | Build a mini calculator that parses and evaluates infix arithmetic expressions supporting parentheses, operator precedence, and unary minus. |
| **Scope** | ~150–200 LOC split across tokenizer, parser, and evaluator utilities. |
| **Operators** | `+`, `-`, `*`, `/` with integer semantics. |
| **Edge Cases** | Mixed whitespace, nested parentheses, unary negation, integer division, invalid tokens (should surface errors). |
| **Why we chose it** | Forces models to implement tokenization, parsing (recursive descent or stacks), and evaluation. It is widely used as a litmus test for reasoning + code generation quality. |

### Functional Requirements

1. Accept an input string such as `"3 + 4 * (2 - 1)"`.
2. Produce an integer result (`7` in the example above).
3. Respect standard precedence: multiplication/division before addition/subtraction, unless overridden by parentheses.
4. Support unary minus (e.g., `"-3 + 5" -> 2`).
5. Provide structured code with helper functions/classes (e.g., tokenizer, parser, evaluator modules) rather than a single monolithic function.
6. Include basic error handling for malformed expressions.

### Reference Test Cases

| Input | Expected Output |
| --- | --- |
| `"1 + 2"` | `3` |
| `"2 * 3 + 4"` | `10` |
| `"2 * (3 + 4)"` | `14` |
| `"8 / 2 * (2 + 2)"` | `16` |

### Prompt Snippet

```
You are writing a full program called "Expression Evaluator".
Requirements:
- Tokenize infix arithmetic strings containing +, -, *, /, parentheses, and whitespace.
- Parse respecting operator precedence and parentheses.
- Support unary minus.
- Return an integer result.
- Organize code into logical helpers (tokenizer, parser, evaluator) and include a simple CLI entry point.
```

Future problems (sorting visualizer, REST client, etc.) will be appended to this catalog as we expand coverage.
