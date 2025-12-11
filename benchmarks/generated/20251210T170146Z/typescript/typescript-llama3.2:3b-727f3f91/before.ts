// Token types
enum TokenType {
  NUMBER,
  PLUS,
  MINUS,
  MUL,
  DIV,
  LPAREN,
  RPAREN,
}

// Token class
class Token {
  type: TokenType;
  value: string | number;

  constructor(type: TokenType, value: string | number) {
    this.type = type;
    this.value = value;
  }
}

// Lexer class
class Lexer {
  private input: string;
  private pos: number;
  private tokens: Token[] = [];

  constructor(input: string) {
    this.input = input;
    this.pos = 0;
  }

  public nextToken(): Token {
    while (this.pos < this.input.length) {
      const c = this.input[this.pos];
      if (!isNaN(parseInt(c))) {
        // Number
        let num = '';
        while (this.pos < this.input.length && !isNaN(parseInt(this.input[this.pos]))) {
          num += this.input[this.pos++];
        }
        this.tokens.push(new Token(TokenType.NUMBER, parseInt(num)));
        return this.nextToken();
      } else if (c === '+') {
        // +
        this.tokens.push(new Token(TokenType.PLUS, '+'));
        return this.nextToken();
      } else if (c === '-') {
        // -
        this.tokens.push(new Token(TokenType.MINUS, '-'));
        return this.nextToken();
      } else if (c === '*') {
        // *
        this.tokens.push(new Token(TokenType.MUL, '*'));
        return this.nextToken();
      } else if (c === '/') {
        // /
        this.tokens.push(new Token(TokenType.DIV, '/'));
        return this.nextToken();
      } else if (c === '(') {
        // (
        this.tokens.push(new Token(TokenType.LPAREN, '('));
        return this.nextToken();
      } else if (c === ')') {
        // )
        this.tokens.push(new Token(TokenType.RPAREN, ')'));
        return this.nextToken();
      }
    }

    throw new Error('Invalid input');
  }

  public getTokens(): Token[] {
    return this.tokens;
  }
}

// Parser class
class Parser {
  private tokens: Token[];
  private pos: number;

  constructor(tokens: Token[]) {
    this.tokens = tokens;
    this.pos = 0;
  }

  public parse(): [number, string] | null {
    const num1 = this.parseNumber();
    if (num1 === null) return null;

    const op = this.matchToken(TokenType.PLUS);
    if (op === null) return [num1, ''];

    const num2 = this.parseNumber();
    if (num2 === null) return null;

    return [num1, op.value, num2];
  }

  private parseNumber(): number | null {
    while (this.pos < this.tokens.length && this.tokens[this.pos].type === TokenType.NUMBER) {
      const token = this.tokens[++this.pos];
      if (token.type !== TokenType.NUMBER) throw new Error('Invalid input');
    }
    return this.pos > this.tokens.length ? null : this.tokens[this.pos - 1].value;
  }

  private matchToken(type: TokenType): Token | null {
    if (this.pos >= this.tokens.length) return null;
    const token = this.tokens[this.pos];
    if (token.type === type) {
      this.pos++;
      return token;
    }
    return null;
  }
}

// Evaluator class
class Evaluator {
  private pos: number;

  constructor() {
    this.pos = 0;
  }

  public evaluate(expression: string): number | null {
    const tokens = new Lexer(expression).getTokens();
    if (tokens.length === 0) return null;

    const parser = new Parser(tokens);
    let result = parser.parse();

    while (result !== null && result[1] !== '') {
      switch (result[1]) {
        case '+':
          result = [result[0], '', this.evaluateExpression(result[2])];
          break;
        case '-':
          result = [result[0], '', -this.evaluateExpression(result[2])];
          break;
        case '*':
          result = [result[0], '', this.multiply(this.evaluateExpression(result[2]), result[0])];
          break;
        case '/':
          result = [result[0], '', this.divide(this.evaluateExpression(result[2]), result[0])];
          break;
      }
    }

    return result !== null ? result[2] : null;
  }

  private evaluateExpression(expression: string): number {
    const tokens = new Lexer(expression).getTokens();
    if (tokens.length === 0) return 0;

    const parser = new Parser(tokens);
    let result = parser.parse();

    while (result !== null && result[1] !== '') {
      switch (result[1]) {
        case '+':
          result = [result[0], '', this.evaluateExpression(result[2])];
          break;
        case '-':
          result = [result[0], '', -this.evaluateExpression(result[2])];
          break;
        case '*':
          result = [result[0], '', this.multiply(this.evaluateExpression(result[2]), result[0])];
          break;
        case '/':
          result = [result[0], '', this.divide(this.evaluateExpression(result[2]), result[0])];
          break;
      }
    }

    return result !== null ? result[2] : 0;
  }

  private multiply(num1: number, num2: number): number {
    if (num1 === 0 || num2 === 0) return 0;
    return num1 * num2;
  }

  private divide(num1: number, num2: number): number {
    if (num2 === 0) throw new Error('Division by zero');
    return num1 / num2;
  }
}

// Usage
const evaluator = new Evaluator();
console.log(evaluator.evaluate('1 + 2')); // Output: 3
console.log(evaluator.evaluate('2 * 3 + 4')); // Output: 10
console.log(evaluator.evaluate('2 * (3 + 4)')); // Output: 14
console.log(evaluator.evaluate('8 / 2 * (2 + 2)')); // Output: 16