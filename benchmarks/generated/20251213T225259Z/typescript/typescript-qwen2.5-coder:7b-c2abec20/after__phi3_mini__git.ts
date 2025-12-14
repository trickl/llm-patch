// expression_evaluator.ts

function tokenize(input: string): string[] {
    return input.match(/[\d\+\-\*\/\(\)]/g) || [];
}

function parse(tokens: string[]): number[] {
    const values: number[] = [];
    const operators: string[] = [];

    tokens.forEach(token => {
        if (/\d/.test(token)) {
            values.push(parseInt(token, 10));
        } else if (token === '(') {
            operators.push(token);
        } else if (token === ')') {
            while (operators.length > 0 && operators[operators.length - 1] !== '(') {
                applyOperator(values, operators);
            }
            operators.pop(); // Remove '('
        } else if (/\+\-|\*\//.test(token)) {
            while (
                operators.length > 0 &&
                precedence(operators[operators.length - 1]) >= precedence(token)
            ) {
                applyOperator(values, operators);
            }
            operators.push(token);
        }
    });

    while (operators.length > 0) {
        applyOperator(values, operators);
    }

    return values;
}

function evaluateExpression(input: string): number {
    const tokens = tokenize(input);
    const parsedValues = parse(tokens);
    if (parsedValues.length !== 1) {
        throw new Error('Invalid expression');
    }
    return parsedValues[0];
}

function precedence(operator: string): number {
    switch (operator) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            return 0;
    }
}

function applyOperator(values: number[], operators: string[]): void {
    const operator = operators.pop();
    if (!operator) throw new Error('Invalid expression');
    const b = values.pop();
    const a = values.pop();
    if (b === undefined || a === undefined) throw new Error('Invalid expression');

    switch (operator) {
        case '+':
            values.push(a + b);
            break;
        case '-':
            values.push(a - b);
            break;
        case '*':
            values.push(a * b);
            break;
        case '/':
            if (b === 0) throw new Error('Division by zero');
            values.push(Math.trunc(a / b));
            break;
    }
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
        console.error(`Error: ${error.message}`);
    }
}

node expression_evaluator.ts "3 + 4 * (2 - 1)"