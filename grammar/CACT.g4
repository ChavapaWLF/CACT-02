grammar CACT;

// PR1 checks syntax only
compUnit
    : (decl | funcDef)+ EOF
    ;

decl
    : constDecl
    | varDecl
    ;

constDecl
    : 'const' bType constDef (',' constDef)* ';'
    ;

bType
    : 'int' | 'float' | 'char'
    ;

constDef
    : Ident ('[' IntConst ']')* '=' constInitVal
    ;

constInitVal
    : constExp
    | '{' (constInitVal (',' constInitVal)*)? '}'
    ;

// The initialization examples on spec p.7 and PR1 cases 19/20/23 require
// literals, despite the broader ConstExp -> AddExp production on p.5.
constExp
    : ('+' | '-')? number
    ;

varDecl
    : bType varDef (',' varDef)* ';'
    ;

varDef
    : Ident ('[' IntConst ']')* ('=' constInitVal)?
    ;

funcDef
    : funcType Ident '(' funcFParams? ')' block
    ;

funcType
    : 'void' | bType
    ;

funcFParams
    : funcFParam (',' funcFParam)*
    ;

funcFParam
    : bType Ident ('[' IntConst? ']' ('[' IntConst ']')*)?
    ;

block
    : '{' blockItem* '}'
    ;

blockItem
    : decl
    | stmt
    ;

stmt
    : lVal '=' exp ';'
    | exp? ';'
    | block
    | 'if' '(' cond ')' stmt ('else' stmt)?
    | 'while' '(' cond ')' stmt
    | 'break' ';'
    | 'continue' ';'
    | 'return' exp? ';'
    ;

exp
    : addExp
    ;

lVal
    : Ident ('[' exp ']')*
    ;

number
    : IntConst
    | FloatConst
    | CharConst
    ;

funcRParams
    : exp (',' exp)*
    ;

funcCall
    : Ident '(' funcRParams? ')'
    ;

primaryExp
    : '(' exp ')'
    | lVal
    | number
    ;

unaryExp
    : primaryExp
    | ('+' | '-') unaryExp
    | funcCall
    ;

mulExp
    : unaryExp
    | mulExp ('*' | '/' | '%') unaryExp
    ;

addExp
    : mulExp
    | addExp ('+' | '-') mulExp
    ;

cond
    : lOrExp
    ;

// The spec restricts ! to conditions. Separate the lower precedence layers
// here so ! cannot leak into assignments, returns, indices or call arguments.
// Parentheses still group arithmetic expressions, as in PrimaryExp on p.5.
condPrimaryExp
    : '(' condAddExp ')'
    | lVal
    | number
    ;

condUnaryExp
    : condPrimaryExp
    | ('+' | '-' | '!') condUnaryExp
    | funcCall
    ;

condMulExp
    : condUnaryExp
    | condMulExp ('*' | '/' | '%') condUnaryExp
    ;

condAddExp
    : condMulExp
    | condAddExp ('+' | '-') condMulExp
    ;

relExp
    : condAddExp
    | relExp ('<' | '>' | '<=' | '>=') condAddExp
    ;

eqExp
    : relExp
    | eqExp ('==' | '!=') relExp
    ;

lAndExp
    : eqExp
    | lAndExp '&&' eqExp
    ;

lOrExp
    : lAndExp
    | lOrExp '||' lAndExp
    ;

// Listed as a keyword, but not a BType/FuncType in the 2025 specification.
DOUBLE : 'double';

// Implicit keyword tokens take priority over identifiers of the same length.
Ident
    : [a-zA-Z_] [a-zA-Z_0-9]*
    ;

IntConst
    : [1-9] [0-9]*
    | '0' [0-7]*
    | '0' [xX] [0-9a-fA-F]+
    ;

// CACT uses decimal floating constants, optionally suffixed f/F.
// A decimal point or an exponent is mandatory: 3f is not a float.
FloatConst
    : ([0-9]+ '.' [0-9]* | '.' [0-9]+) Exponent? [fF]?
    | [0-9]+ Exponent [fF]?
    ;

fragment Exponent
    : [eE] [+-]? [0-9]+
    ;

CharConst
    : '\'' (EscapeSequence | AsciiCharacter) '\''
    ;

fragment EscapeSequence
    : '\\' [nt\\'"0]
    ;

// ASCII except LF, CR, single quote and backslash.
fragment AsciiCharacter
    : [\u0000-\u0009\u000B\u000C\u000E-\u0026\u0028-\u005B\u005D-\u007F]
    ;

LineComment
    : '//' ~[\r\n]* -> skip
    ;

BlockComment
    : '/*' .*? '*/' -> skip
    ;

WhiteSpace
    : [ \t\r\n]+ -> skip
    ;
