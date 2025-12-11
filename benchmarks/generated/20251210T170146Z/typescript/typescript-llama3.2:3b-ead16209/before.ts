// expression_evaluator.ts

class ExpressionEvaluator {
  private precedence: { [operator: string]: number } = {
    '+': 1,
    '-': 1,
    '*': 2,
    '/': 2,
  };

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
      if (!char.match(/[\d+*/()-]/)) {
        throw new Error(`Invalid character: ${char}`);
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
        outputQueue.push(parseInt(token, 10));
      } else if (token === '(') {
        operatorStack.push(token);
      } else if (token === ')') {
        while (operatorStack[operatorStack.length - 1] !== '(') {
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          outputQueue.push(this.calculate(leftOperand, op, rightOperand));
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
          outputQueue.push(this.calculate(leftOperand, op, rightOperand));
        }
        operatorStack.push(token);
      }
    }

    while (operatorStack.length) {
      const op = operatorStack.pop() as string;
      const rightOperand = outputQueue.pop() as number;
      const leftOperand = outputQueue.pop() as number;
      outputQueue.push(this.calculate(leftOperand, op, rightOperand));
    }

    return outputQueue[0];
  }

  private calculate(left: number, op: string, right: number): number {
    if (op === '+') {
      return left + right;
    } else if (op === '-') {
      return -left + right;
    } else if (op === '*') {
      return left * right;
    } else if (op === '/') {
      return Math.floor(left / right);
    }
  }
}

// CLI example
const evaluator = new ExpressionEvaluator();
console.log(evaluator.evaluateExpression('1 + 2')); // Output: 3
console.log(evaluator.evaluateExpression('2 * 3 + 4')); // Output: 10
console.log(evaluator.evaluateExpression('2 * (3 + 4)')); // Output: 14
console.log(evaluator.evaluateExpression('8 / 2 * (2 + 2)')); // Output: 16