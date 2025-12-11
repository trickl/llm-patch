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
      if (char.match(/[\d+*/()-]/)) {
        currentToken += char;
      } else if (currentToken && !this.isOperator(char)) {
        output.push(currentToken);
        currentToken = '';
      }

      if (!char.match(/[\d+*/()-]/) && !currentToken) {
        throw new Error('Malformed input');
      }
    }

    if (currentToken) {
      output.push(currentToken);
    }

    return output;
  }

  private isOperator(char: string): boolean {
    return char === '+' || char === '-' || char === '*' || char === '/';
  }

  private parse(tokens: string[]): number {
    const operatorStack = [];
    let outputQueue = [];

    for (const token of tokens) {
      if (!this.isOperator(token)) {
        outputQueue.push(parseInt(token));
      } else if (token === '(') {
        operatorStack.push(token);
      } else if (token === ')') {
        while (operatorStack[operatorStack.length - 1] !== '(') {
          const operand2 = outputQueue.pop();
          const operand1 = outputQueue.pop();

          const result = this.applyOperator(operand1, operand2, token);
          outputQueue.push(result);

          if (!this.isOperator(operatorStack[operatorStack.length - 1])) {
            throw new Error('Malformed input');
          }
        }

        operatorStack.pop();
      } else {
        while (
          operatorStack.length &&
          this.precedence[this.getOperator(token)] >=
          this.precedence[this.getOperator(operatorStack[operatorStack.length - 1])]
        ) {
          const operand2 = outputQueue.pop();
          const operand1 = outputQueue.pop();

          const result = this.applyOperator(operand1, operand2, operatorStack[operatorStack.length - 1]);
          outputQueue.push(result);

          operatorStack.pop();
        }

        operatorStack.push(token);
      }
    }

    while (operatorStack.length) {
      const operand2 = outputQueue.pop();
      const operand1 = outputQueue.pop();

      const result = this.applyOperator(operand1, operand2, operatorStack[operatorStack.length - 1]);
      outputQueue.push(result);

      if (!this.isOperator(operatorStack[operatorStack.length - 1])) {
        throw new Error('Malformed input');
      }

      operatorStack.pop();
    }

    return outputQueue[0];
  }

  private applyOperator(operand1: number, operand2: number, operator: string): number {
    switch (operator) {
      case '+':
        return operand1 + operand2;
      case '-':
        return operand1 - operand2;
      case '*':
        return operand1 * operand2;
      case '/':
        return operand1 / operand2;
      default:
        throw new Error('Invalid operator');
    }
  }

  private getOperator(operator: string): string {
    for (const key in this.precedence) {
      if (this.precedence[key] === this.precedence[operator]) {
        return key;
      }
    }

    throw new Error(`Unknown operator: ${operator}`);
  }
}

export function evaluateExpression(input: string): number {
  const evaluator = new ExpressionEvaluator();
  try {
    return evaluator.evaluateExpression(input);
  } catch (error) {
    console.error(error.message);
    return NaN;
  }
}