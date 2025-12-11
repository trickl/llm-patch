// expression_evaluator.ts

class ExpressionEvaluator {
  private precedence: { [operator: string]: number };

  constructor() {
    this.precedence = {
      '+': 1,
      '-': 1,
      '*': 2,
      '/': 2,
    };
  }

  public evaluateExpression(input: string): number {
    const tokens = this.tokenize(input);
    return this.parse(tokens);
  }

  private tokenize(input: string): string[] {
    const output = [];
    let currentToken = '';

    for (const char of input) {
      if (char.match(/^[0-9+*/()-]/)) {
        currentToken += char;
      } else if (currentToken && !this.isOperator(char)) {
        output.push(currentToken);
        currentToken = '';
      }

      if (!char.match(/^[0-9+*/()-]$/)) {
        continue;
      }
    }

    if (currentToken) {
      output.push(currentToken);
    }

    return output;
  }

  private isOperator(char: string): boolean {
    return char in this.precedence;
  }

  private parse(tokens: string[]): number {
    const operatorStack = [];
    let outputQueue: number[] = [];

    for (const token of tokens) {
      if (!this.isOperator(token)) {
        outputQueue.push(parseInt(token));
      } else if (token === '(') {
        operatorStack.push(token);
      } else if (token === ')') {
        while (operatorStack[operatorStack.length - 1] !== '(') {
          const operand2 = outputQueue.pop();
          const operand1 = outputQueue.pop();

          const result = this.calculate(operand1, operand2, token);

          outputQueue.push(result);
        }

        operatorStack.pop(); // Remove the '('
      } else {
        while (
          operatorStack.length &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token]
        ) {
          const operand2 = outputQueue.pop();
          const operand1 = outputQueue.pop();

          const result = this.calculate(operand1, operand2, operatorStack[operatorStack.length - 1]);

          outputQueue.push(result);
          operatorStack.pop();
        }

        operatorStack.push(token);
      }
    }

    while (operatorStack.length) {
      const operand2 = outputQueue.pop();
      const operand1 = outputQueue.pop();

      const result = this.calculate(operand1, operand2, operatorStack[operatorStack.length - 1]);

      outputQueue.push(result);
      operatorStack.pop();
    }

    return outputQueue[0];
  }

  private calculate(operand1: number, operand2: number, operator: string): number {
    switch (operator) {
      case '+':
        return operand1 + operand2;
      case '-':
        return operand1 - operand2;
      case '*':
        return operand1 * operand2;
      case '/':
        return Math.floor(operand1 / operand2);
      default:
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }
}

export function evaluateExpression(input: string): number {
  const evaluator = new ExpressionEvaluator();
  return evaluator.evaluateExpression(input);
}

// CLI example
const input = '1 + 2';
console.log(evaluateExpression(input)); // Output: 3

input = '2 * 3 + 4';
console.log(evaluateExpression(input)); // Output: 10

input = '2 * (3 + 4)';
console.log(evaluateExpression(input)); // Output: 14

input = '8 / 2 * (2 + 2)';
console.log(evaluateExpression(input)); // Output: 16