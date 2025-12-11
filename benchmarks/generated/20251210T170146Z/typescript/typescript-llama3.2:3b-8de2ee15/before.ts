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
      } else if (currentToken !== '') {
        output.push(currentToken);
        currentToken = '';
      }

      if (char === '(' || char === ')') {
        output.push(char);
      }
    }

    if (currentToken !== '') {
      output.push(currentToken);
    }

    return output;
  }

  private parse(tokens: string[]): number {
    const operatorStack: string[] = [];
    let outputQueue: number[] = [];

    for (const token of tokens) {
      if (token === '(') {
        operatorStack.push(token);
      } else if (token === ')') {
        while (operatorStack[operatorStack.length - 1] !== '(') {
          const operand2 = outputQueue.pop() as number;
          const operand1 = outputQueue.pop() as number;

          const result = this.calculate(operand1, token, operand2);
          outputQueue.push(result);
        }

        operatorStack.pop();
      } else if (this.isOperator(token)) {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token]
        ) {
          const operand2 = outputQueue.pop() as number;
          const operand1 = outputQueue.pop() as number;

          const result = this.calculate(operand1, operatorStack[operatorStack.length - 1], operand2);
          outputQueue.push(result);

          operatorStack.pop();
        }

        operatorStack.push(token);
      } else {
        outputQueue.push(Number(token));
      }
    }

    while (operatorStack.length > 0) {
      const operand2 = outputQueue.pop() as number;
      const operand1 = outputQueue.pop() as number;

      const result = this.calculate(operand1, operatorStack[operatorStack.length - 1], operand2);
      outputQueue.push(result);

      operatorStack.pop();
    }

    return outputQueue[0];
  }

  private calculate(operand1: number, operator: string, operand2: number): number {
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
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }

  private isOperator(token: string): boolean {
    return token in this.precedence;
  }
}

export function evaluateExpression(input: string): number {
  const evaluator = new ExpressionEvaluator();
  return evaluator.evaluateExpression(input);
}

// CLI example
if (require.main === module) {
  console.log(evaluateExpression('1 + 2')); // Output: 3
  console.log(evaluateExpression('2 * 3 + 4')); // Output: 10
  console.log(evaluateExpression('2 * (3 + 4)')); // Output: 14
  console.log(evaluateExpression('8 / 2 * (2 + 2)')); // Output: 16
}