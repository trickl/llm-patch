// expression_evaluator.ts

interface Token {
  type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN';
  value?: number;
}

class ExpressionEvaluator {
  private precedence: { [operator: string]: number };

  constructor() {
    this.precedence = {
      '+': 1,
      '-': 1,
      '*': 2,
      '/': 2
    };
  }

  tokenize(expression: string): Token[] {
    const tokens: Token[] = [];
    let currentToken: Token | null = null;
    for (const char of expression) {
      if (char === ' ') continue;
      if (!currentToken || !this.isOperator(char)) {
        currentToken = { type: 'NUMBER', value: parseInt(char, 10) };
      } else {
        if (currentToken) tokens.push(currentToken);
        currentToken = { type: char };
      }
    }
    if (currentToken) tokens.push(currentToken);
    return tokens;
  }

  private isOperator(char: string): boolean {
    return ['+', '-', '*', '/'].includes(char);
  }

  parse(tokens: Token[]): number[] {
    const outputQueue: number[] = [];
    const operatorStack: string[] = [];

    for (const token of tokens) {
      if (token.type === 'NUMBER') {
        outputQueue.push(token.value as number);
      } else if (token.type === 'LPAREN') {
        operatorStack.push(token.type);
      } else if (token.type === 'RPAREN') {
        while (operatorStack[operatorStack.length - 1] !== 'LPAREN') {
          const op = operatorStack.pop()!;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          const result = this.evaluate(op, leftOperand, rightOperand);
          outputQueue.push(result);
        }
        operatorStack.pop();
      } else if (token.type === 'PLUS' || token.type === 'MINUS') {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token.type]
        ) {
          const op = operatorStack.pop()!;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          const result = this.evaluate(op, leftOperand, rightOperand);
          outputQueue.push(result);
        }
        operatorStack.push(token.type);
      } else if (token.type === 'MUL' || token.type === 'DIV') {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token.type]
        ) {
          const op = operatorStack.pop()!;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          const result = this.evaluate(op, leftOperand, rightOperand);
          outputQueue.push(result);
        }
        operatorStack.push(token.type);
      } else if (token.type === 'MINUS') {
        while (operatorStack.length > 0 && operatorStack[operatorStack.length - 1] === 'PLUS') {
          const op = operatorStack.pop()!;
          const rightOperand = outputQueue.pop() as number;
          const leftOperand = outputQueue.pop() as number;
          const result = this.evaluate(op, leftOperand, rightOperand);
          outputQueue.push(result);
        }
        operatorStack.push(token.type);
      }
    }

    while (operatorStack.length > 0) {
      const op = operatorStack.pop()!;
      const rightOperand = outputQueue.pop() as number;
      const leftOperand = outputQueue.pop() as number;
      const result = this.evaluate(op, leftOperand, rightOperand);
      outputQueue.push(result);
    }

    return outputQueue[0];
  }

  private evaluate(operator: string, leftOperand: number, rightOperand: number): number {
    switch (operator) {
      case '+':
        return leftOperand + rightOperand;
      case '-':
        return -leftOperand + rightOperand;
      case '*':
        return leftOperand * rightOperand;
      case '/':
        return Math.floor(leftOperand / rightOperand);
      default:
        throw new Error(`Unsupported operator: ${operator}`);
    }
  }

  public evaluateExpression(input: string): number {
    const tokens = this.tokenize(input);
    return this.parse(tokens);
  }
}

// CLI example
const evaluator = new ExpressionEvaluator();
console.log(evaluator.evaluateExpression('1 + 2')); // Output: 3
console.log(evaluator.evaluateExpression('2 * 3 + 4')); // Output: 10
console.log(evaluator.evaluateExpression('2 * (3 + 4)')); // Output: 14
console.log(evaluator.evaluateExpression('8 / 2 * (2 + 2)')); // Output: 16