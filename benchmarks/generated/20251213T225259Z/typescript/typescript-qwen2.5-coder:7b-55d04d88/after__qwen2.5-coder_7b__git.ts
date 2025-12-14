import { strict as assert } from 'assert';

// Token types
enum TokenType {
  NUMBER,
  PLUS,
  MINUS,
  MUL,
  DIV,
  LPAREN,
  RPAREN,
  EOF,
}

interface Token {
  type: TokenType;
  value?: number | string;
}

class Lexer {
  public input: string;
  private pos: number = 0;
  private currentChar: string | null = this.input[this.pos];

  constructor(input: string) {
    this.input = input;
  }

  private error(): never {
    throw new Error('Invalid character');
  }

  private advance() {
    this.pos++;
    if (this.pos < this.input.length) {
      this.currentChar = this.input[this.pos];
    } else {
      this.currentChar = null;
    }
  }

  private skipWhitespace() {
    while (this.currentChar !== null && /\s/.test(this.currentChar)) {
      this.advance();
    }
  }

  private number(): Token {
    let result = '';
    while (this.currentChar !== null && /\d/.test(this.currentChar)) {
      result += this.currentChar;
      this.advance();
    }
    return { type: TokenType.NUMBER, value: parseInt(result, 10) };
  }

  private peek(): string | null {
    const nextPos = this.pos + 1;
    if (nextPos < this.input.length) {
      return this.input[nextPos];
    } else {
      return null;
    }
  }

  public getNextToken(): Token {
    while (this.currentChar !== null) {
      if (/^\s+$/.test(this.currentChar)) {
        this.skipWhitespace();
        continue;
      }

      if (/\d/.test(this.currentChar)) {
        return this.number();
      }

      if (this.currentChar === '+') {
        this.advance();
        return { type: TokenType.PLUS };
      }

      if (this.currentChar === '-') {
        this.advance();
        if (this.peek() === '-' || /\d/.test(this.peek())) {
          return { type: TokenType.MINUS };
        } else {
          return { type: TokenType.MINUS, value: -1 };
        }
      }

      if (this.currentChar === '*') {
        this.advance();
        return { type: TokenType.MUL };
      }

      if (this.currentChar === '/') {
        this.advance();
        return { type: TokenType.DIV };
      }

      if (this.currentChar === '(') {
        this.advance();
        return { type: TokenType.LPAREN };
      }

      if (this.currentChar === ')') {
        this.advance();
        return { type: TokenType.RPAREN };
      }

      this.error();
    }
    return { type: TokenType.EOF };
  }
}

class Parser {
  private lexer: Lexer;
  private currentToken: Token;

  constructor(lexer: Lexer) {
    this.lexer = lexer;
    this.currentToken = lexer.getNextToken();
  }

  private error(): never {
    throw new Error(`Invalid token at ${this.currentToken.value}`);
  }

  private eat(tokenType: TokenType): void {
    if (this.currentToken.type === tokenType) {
      this.currentToken = this.lexer.getNextToken();
    } else {
      this.error();
    }
  }

  private factor(): number {
    let token = this.currentToken;
    if (token.type === TokenType.NUMBER) {
      this.eat(TokenType.NUMBER);
      return token.value as number;
    } else if (token.type === TokenType.MINUS && typeof token.value === 'number') {
      this.eat(TokenType.MINUS);
      return -this.factor();
    } else if (token.type === TokenType.LPAREN) {
      this.eat(TokenType.LPAREN);
      const result = this.expr();
      this.eat(TokenType.RPAREN);
      return result;
    }
    this.error();
  }

  private term(): number {
    let result = this.factor();

    while (this.currentToken.type === TokenType.MUL || this.currentToken.type === TokenType.DIV) {
      const token = this.currentToken;
      if (token.type === TokenType.MUL) {
        this.eat(TokenType.MUL);
        result *= this.factor();
      } else if (token.type === TokenType.DIV) {
        this.eat(TokenType.DIV);
        result /= this.factor();
      }
    }

    return result;
  }

  public expr(): number {
    let result = this.term();

    while (this.currentToken.type === TokenType.PLUS || this.currentToken.type === TokenType.MINUS) {
      const token = this.currentToken;
      if (token.type === TokenType.PLUS) {
        this.eat(TokenType.PLUS);
        result += this.term();
      } else if (token.type === TokenType.MINUS) {
        this.eat(TokenType.MINUS);
        result -= this.term();
      }
    }

    return result;
  }
}

export function evaluateExpression(input: string): number {
  const lexer = new Lexer(input);
  const parser = new Parser(lexer);
  return parser.expr();
}

// CLI example
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length !== 1) {
    console.error('Usage: node expression_evaluator.ts "expression"');
    process.exit(1);
  }
  try {
    const result = evaluateExpression(args[0]);
    console.log(result);
  } catch (error) {
    console.error(`Error evaluating expression: ${error.message}`);
  }
}

// Automated tests
assert.strictEqual(evaluateExpression('1 + 2'), 3);
assert.strictEqual(evaluateExpression('2 * 3 + 4'), 10);
assert.strictEqual(evaluateExpression('2 * (3 + 4)'), 14);
assert.strictEqual(evaluateExpression('8 / 2 * (2 + 2)'), 16);