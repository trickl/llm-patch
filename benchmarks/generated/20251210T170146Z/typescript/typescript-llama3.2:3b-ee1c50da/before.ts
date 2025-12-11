// expression_evaluator.ts

class Token {
  type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN';
  value: number | string;

  constructor(type: 'NUMBER' | 'PLUS' | 'MINUS' | 'MUL' | 'DIV' | 'LPAREN' | 'RPAREN', value: number | string) {
    this.type = type;
    this.value = value;
  }
}

class Evaluator {
  private precedence: { [key: string]: number };
  private tokens: Token[];

  constructor() {
    this.precedence = {
      '+': 1,
      '-': 1,
      '*': 2,
      '/': 2
    };

    this.tokens = [];
  }

  tokenize(expression: string): void {
    const numbers = expression.match(/\d+/g);
    if (numbers) {
      for (const num of numbers) {
        this.tokens.push(new Token('NUMBER', parseInt(num)));
      }
    }

    let currentToken = '';
    for (let i = 0; i < expression.length; i++) {
      const char = expression[i];
      if (!isNaN(parseInt(char)) || char === ' ') {
        continue;
      } else if (char === '(') {
        this.tokens.push(new Token('LPAREN', char));
      } else if (char === ')') {
        this.tokens.push(new Token('RPAREN', char));
      } else if (['+', '-', '*', '/'].includes(char)) {
        if (currentToken !== '') {
          this.tokens.push(new Token(currentToken, currentToken));
          currentToken = '';
        }
        this.tokens.push(new Token(char, char));
      } else if (char === '-') {
        if (currentToken !== '') {
          this.tokens.push(new Token(currentToken, currentToken));
          currentToken = '';
        }
        this.tokens.push(new Token('-', '-'));
      } else {
        continue;
      }

      i++;
    }

    if (currentToken !== '') {
      this.tokens.push(new Token(currentToken, currentToken));
    }
  }

  parse(tokens: Token[]): number[] {
    const outputQueue: number[] = [];
    const operatorStack: string[] = [];

    for (const token of tokens) {
      if (token.type === 'NUMBER') {
        outputQueue.push(token.value);
      } else if (token.type === 'LPAREN') {
        operatorStack.push(token.type);
      } else if (token.type === 'RPAREN') {
        while (operatorStack[operatorStack.length - 1] !== 'LPAREN') {
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop();
          const leftOperand = outputQueue.pop();

          let result: number;
          switch (op) {
            case '+':
              result = leftOperand + rightOperand;
              break;
            case '-':
              result = leftOperand - rightOperand;
              break;
            case '*':
              result = leftOperand * rightOperand;
              break;
            case '/':
              result = leftOperand / rightOperand;
              break;
          }

          outputQueue.push(result);
        }
        operatorStack.pop();
      } else if (token.type === 'PLUS' || token.type === 'MINUS') {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token.type]
        ) {
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop();
          const leftOperand = outputQueue.pop();

          let result: number;
          switch (op) {
            case '+':
              result = leftOperand + rightOperand;
              break;
            case '-':
              result = leftOperand - rightOperand;
              break;
          }

          outputQueue.push(result);
        }
        operatorStack.push(token.type);
      } else if (token.type === 'MUL' || token.type === 'DIV') {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence[token.type]
        ) {
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop();
          const leftOperand = outputQueue.pop();

          let result: number;
          switch (op) {
            case '+':
              result = leftOperand + rightOperand;
              break;
            case '-':
              result = leftOperand - rightOperand;
              break;
          }

          outputQueue.push(result);
        }
        operatorStack.push(token.type);
      } else if (token.type === '-') {
        while (
          operatorStack.length > 0 &&
          this.precedence[operatorStack[operatorStack.length - 1]] >=
            this.precedence['MINUS']
        ) {
          const op = operatorStack.pop() as string;
          const rightOperand = outputQueue.pop();
          const leftOperand = outputQueue.pop();

          let result: number;
          switch (op) {
            case '+':
              result = leftOperand + rightOperand;
              break;
            case '-':
              result = leftOperand - rightOperand;
              break;
          }

          outputQueue.push(result);
        }
        operatorStack.push(token.type);
      }
    }

    while (operatorStack.length > 0) {
      const op = operatorStack.pop() as string;
      const rightOperand = outputQueue.pop();
      const leftOperand = outputQueue.pop();

      let result: number;
      switch (op) {
        case '+':
          result = leftOperand + rightOperand;
          break;
        case '-':
          result = leftOperand - rightOperand;
          break;
        case '*':
          result = leftOperand * rightOperand;
          break;
        case '/':
          result = leftOperand / rightOperand;
          break;
      }

      outputQueue.push(result);
    }

    return outputQueue[0];
  }
}

function evaluateExpression(input: string): number {
  const evaluator = new Evaluator();
  evaluator.tokenize(input);

  try {
    return evaluator.parse(evaluator.tokens);
  } catch (error) {
    throw new Error('Invalid expression');
  }
}

export function evaluateExpression(input: string): number {
  return evaluateExpression(input);
}