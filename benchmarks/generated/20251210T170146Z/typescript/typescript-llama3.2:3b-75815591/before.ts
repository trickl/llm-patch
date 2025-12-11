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
      if (char === '(' || char === ')') {
        output.push(char);
      }
    }
    if (currentToken) {
      output.push(currentToken);
    }
    return output;
  }

  private isOperator(char: string): boolean {
    return ['*', '/'].includes(char);
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
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          this.applyOperator(op, leftOperand, rightOperand);
        }
        operatorStack.pop(); // Remove the '('
      } else {
        while (
          operatorStack.length &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token]
        ) {
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          this.applyOperator(op, leftOperand, rightOperand);
        }
        operatorStack.push(token);
      }
    }

    while (operatorStack.length) {
      const op = operatorStack.pop() as string;
      const rightOperand = outputQueue.pop() as number;
      const leftOperand = outputQueue.pop() as number;
      this.applyOperator(op, leftOperand, rightOperand);
    }

    return outputQueue[0];
  }

  private applyOperator(operator: string, leftOperand: number, rightOperand: number): void {
    switch (operator) {
      case '+':
        outputQueue.push(leftOperand + rightOperand);
        break;
      case '-':
        outputQueue.push(leftOperand - rightOperand);
        break;
      case '*':
        outputQueue.push(leftOperand * rightOperand);
        break;
      case '/':
        outputQueue.push(Math.floor(leftOperand / rightOperand));
        break;
    }
  }
}

export function evaluateExpression(input: string): number {
  return new ExpressionEvaluator().evaluateExpression(input);
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