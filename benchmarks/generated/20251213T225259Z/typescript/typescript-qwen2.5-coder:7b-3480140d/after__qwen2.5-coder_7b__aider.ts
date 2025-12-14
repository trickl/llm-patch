import { strict as assert } from 'assert';
import * as process from 'process';
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
  private input: string;
  private pos: number = 0;
  private currentChar: string | null = this.input[this.pos];

  constructor(input: string) {
    this.input = input;
  }

  nextToken(): Token {
    while (this.currentChar !== null && /\s/.test(this.currentChar)) {
      this.advance();
    }

    if (this.currentChar === null) {
      return { type: TokenType.EOF };
    }

    if (/^\d+$/.test(this.currentChar)) {
      let num = '';
      while (this.currentChar !== null && /^\d+$/.test(this.currentChar)) {
        num += this.currentChar;
        this.advance();
      }
      return { type: TokenType.NUMBER, value: parseInt(num, 10) };
    }

    if (this.currentChar === '+') {
      this.advance();
      return { type: TokenType.PLUS };
    }

    if (this.currentChar === '-') {
      this.advance();
      return { type: TokenType.MINUS };
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

    throw new Error(`Invalid character: ${this.currentChar}`);
  }

  private advance() {
    this.pos++;
    if (this.pos < this.input.length) {
      this.currentChar = this.input[this.pos];
    } else {
      this.currentChar = null;
    }
  }
}

class Parser {
  private lexer: Lexer;
  private currentToken: Token;

  constructor(lexer: Lexer) {
    this.lexer = lexer;
    this.currentToken = lexer.nextToken();
  }

  parse(): number {
    return this.expression();
  }

  private expression(): number {
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

  private factor(): number {
    const token = this.currentToken;

    if (token.type === TokenType.PLUS) {
      this.eat(TokenType.PLUS);
      return this.factor();
    } else if (token.type === TokenType.MINUS) {
      this.eat(TokenType.MINUS);
      return -this.factor();
    } else if (token.type === TokenType.NUMBER) {
      this.eat(TokenType.NUMBER);
      return token.value as number;
    } else if (token.type === TokenType.LPAREN) {
      this.eat(TokenType.LPAREN);
      const result = this.expression();
      this.eat(TokenType.RPAREN);
      return result;
    }

    throw new Error(`Unexpected token: ${token.type}`);
  }

    }
  }
  private eat(tokenType: TokenType): void {
    if (this.currentToken.type === tokenType) {
      this.currentToken = this.lexer.nextToken();
    } else {
      throw new Error(`Expected token: ${tokenType}, but got: ${this.currentToken.type}`);
    }
  }
}

export function evaluateExpression(input: string): number {
  const lexer = new Lexer(input);
  const parser = new Parser(lexer);
  return parser.parse();
}

// CLI example
if (require.main === module) {
  const input = process.argv[2];
  if (input) {
    try {
      const result = evaluateExpression(input);
      console.log(`Result: ${result}`);
    } catch (error) {
      console.error(`Error: ${error.message}`);
    }
  } else {
    console.log('Usage: node expression_evaluator.ts "expression"');
  }
}

// Automated tests
assert.strictEqual(evaluateExpression("1 + 2"), 3);
assert.strictEqual(evaluateExpression("2 * 3 + 4"), 10);
assert.strictEqual(evaluateExpression("2 * (3 + 4)"), 14);
assert.strictEqual(evaluateExpression("8 / 2 * (2 + 2)"), 16);
