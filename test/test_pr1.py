#!/usr/bin/env python3
"""PR1 acceptance/rejection tests. Uses only the Python standard library."""

import argparse
from pathlib import Path
import re
import subprocess
import tempfile


VALID_PROGRAMS = [
    ("global_without_main", "int global;"),
    ("all_types", "int i; float f; char c; void noop() { return; }"),
    ("keyword_prefixes", "int iffy, while1, return_value, _x2, IF, Return;"),
    ("signed_initializers", "int a=-123,b=+077,c=-0XAf; float f=-43.0e-4F;"),
    ("nested_initializers",
     "const char a[2][2]={{'a','b'},{'c','d'}}; float b[2][2]={{}, {1.f}};"),
    ("empty_initializer", "int a[3]={}; int b[2][2]={{},{}};"),
    ("parameter_dimensions",
     "int f(int a[], float b[][3], char c[2][3][4]) { return a[0]; }"),
    ("hex_octal_dimensions", "int a[0x2][03]; int f(int p[02][0X3]) { return 0; }"),
    ("char_function", "char identity(char ch) { return ch; }"),
    ("float_function", "float identity(float x) { return x; }"),
    ("calls_and_subscripts",
     "int f(int a[][2]) { return g(a[1][1], h(), a[1+2][3*4]); }"),
    ("empty_statement_and_blocks", "void f() { ; {} { ; { ; } } }"),
    ("expression_statements", "void f() { 1; a; f(); 1+2*3; }"),
    ("arithmetic_precedence", "int f() { return -a + b*c / d % e - (f + g); }"),
    ("left_associative_arithmetic", "int f() { return 20-5-2+36/3/2; }"),
    ("recursive_unary", "int f() { return - + - -1; }"),
    ("conditions",
     "void f() { if (a+b*c < d && e != f || g >= h) ; while (i <= j) ; }"),
    ("logical_not_in_conditions", "void f() { if (!a || !!f()) ; while ((!a)+1) ; }"),
    ("dangling_else",
     "void f() { if (a) if (b) f(); else g(); else h(); }"),
    ("else_if_chain", "void f() { if(a) ; else if(b) {} else ; }"),
    ("loop_control", "void f() { while(a) { if(b) break; else continue; } }"),
    ("line_comment_at_eof", "int a; // no final newline"),
    ("all_newline_styles", "// CR\rint a;\r\n// LF\nint b;\t int c;"),
    ("block_comments", "/* 中文注释 */int/**/a; /* // ignored */ int b;"),
    ("first_block_terminator", "/* /* text */ int a;"),
    ("comment_markers_in_chars", "char a='/', b='*', c='\"';"),
    # PR1 must not perform the semantic analysis belonging to later labs.
    ("undefined_names", "int main() { unknown=missing(undeclared); return unknown; }"),
    ("duplicate_definitions", "int a; int a; int f(){} int f(){}"),
    ("no_return_or_wrong_return", "int f() {} void g() { return 1; }"),
    ("break_outside_loop", "void f() { break; continue; }"),
    ("mismatched_types", "int main() { int a; a=1.0f+'c'; return a; }"),
    ("assignment_to_constant", "const int a=1; int main() { a=2; return a; }"),
    ("array_shape_is_semantic", "int a[0]=4; int b[2]={1,{2,3}};"),
]

INVALID_PROGRAMS = [
    ("empty_file", ""),
    ("comments_only", "// comment\n/* comment */"),
    ("missing_return_semicolon", "int main() { return 0 }"),
    ("missing_void_return_semicolon", "void f() { return }"),
    ("missing_declaration_semicolon", "int a"),
    ("missing_assignment_semicolon", "int main() { a=0 return 0; }"),
    ("unmatched_parenthesis", "int main( { return 0; }"),
    ("unmatched_block", "int main() { return 0;"),
    ("global_statement", "int a; a=3;"),
    ("global_block", "{ int a; }"),
    ("nested_function", "int main() { int nested() {} return 0; }"),
    ("function_prototype", "int f(int a);"),
    ("void_variable", "void a;"),
    ("void_parameter", "int main(void) { return 0; }"),
    ("double_type", "double a;"),
    ("double_is_reserved", "int double;"),
    ("old_bool_type", "bool a;"),
    ("keyword_identifier", "int while;"),
    ("unicode_identifier", "int 变量;"),
    ("digit_identifier", "int 7j;"),
    ("identifier_initializer", "const int a=1; int b=a;"),
    ("arithmetic_initializer", "const int a=4+5;"),
    ("function_initializer", "int a=f();"),
    ("parenthesized_initializer", "int a=(1);"),
    ("repeated_sign_initializer", "int a=--1;"),
    ("constant_without_initializer", "const int a;"),
    ("trailing_initializer_comma", "int a[2]={1,2,};"),
    ("array_variable_size", "int a[n];"),
    ("array_expression_size", "int a[2+3];"),
    ("array_function_size", "int a[f()];"),
    ("array_float_size", "int a[2.0];"),
    ("array_negative_size", "int a[-1];"),
    ("array_missing_size", "int a[];"),
    ("parameter_missing_inner_size", "int f(int a[][]) {}"),
    ("parameter_expression_size", "int f(int a[1+2]) {}"),
    ("parameter_default", "int f(int a=1) {}"),
    ("parameter_trailing_comma", "int f(int a,) {}"),
    ("argument_trailing_comma", "void f() { g(1,); }"),
    ("argument_missing_comma", "void f() { g(1 2); }"),
    ("comma_index", "int main() { return a[1,2]; }"),
    ("empty_index", "int main() { return a[]; }"),
    ("non_lvalue_assignment", "void f() { (a+1)=2; }"),
    ("call_assignment", "void f() { g()=2; }"),
    ("chained_assignment", "void f() { a=b=c; }"),
    ("assignment_as_expression", "void f() { g(a=1); }"),
    ("comma_expression", "void f() { a,b; }"),
    ("relational_assignment", "void f() { a=b<c; }"),
    ("logical_assignment", "void f() { a=b&&c; }"),
    ("conditional_return", "int f() { return a==b; }"),
    ("logical_not_assignment", "void f() { a=!b; }"),
    ("logical_not_return", "int f() { return !a; }"),
    ("logical_not_call_argument", "void f() { if (g(!a)) ; }"),
    ("logical_not_index", "void f() { if (a[!b]) ; }"),
    ("conditional_grouping_outside_ebnf", "void f() { if ((a<b)) ; }"),
    ("assignment_as_condition", "void f() { if (a=1) ; }"),
    ("orphan_else", "void f() { else ; }"),
    ("declaration_as_if_body", "void f() { if(a) int b; }"),
    ("for_statement", "void f() { for(;;) ; }"),
    ("do_while_statement", "void f() { do {} while(1); }"),
    ("ternary_expression", "int f() { return a?b:c; }"),
    ("bitwise_not", "int f() { return ~0; }"),
    ("bitwise_and", "int f() { return a&b; }"),
    ("compound_assignment", "void f() { a+=1; }"),
    ("string_literal", 'int main() { print_char("a"); }'),
    ("preprocessor", "#include <stdio.h>\nint a;"),
    ("illegal_character_inside", "int main() { return @0; }"),
    ("trailing_valid_token", "int main() { return 0; } 1"),
    ("trailing_illegal_character", "int main() { return 0; } @"),
    ("trailing_unfinished_declaration", "int main() { return 0; } int"),
    ("unterminated_comment", "int main() { return 0; } /* unfinished"),
    ("unterminated_comment_star", "int a; /* unfinished *"),
    ("nested_comment_leftover", "int a; /* outer /* inner */ outer */"),
    ("stray_comment_end", "int a; */"),
]

VALID_NUMBERS = [
    "0", "123456789", "000", "077", "0x0", "0XFa32", "0xdeadBEEF",
    "9.00", "12.43", ".5", "8.", "8.f", "1.F", "3E2f", "43.0e-4F",
    "0e0", "01e+2", "08.5", ".5e+2", "1.e-2", "2E03", "-0XFa", "+.5f",
]
INVALID_NUMBERS = [
    "08", "09", "0128", "0x", "0X", "0xG", "0x3fG", "0x1g",
    "0b10", "123abc", "1_000", "1u", "2L", "3f", "3F",
    ".", ".f", "1e", "1e+", "1e-", "1e2.3", "1.2.3", "1.0ff",
    "1.0L", "0x1.2", "0x1p2",
]
VALID_CHARS = ["'a'", "'Z'", "'0'", "'+'", "' '", "'\"'",
               r"'\n'", r"'\t'", r"'\\'", r"'\''", r"'\"'", r"'\0'"]
INVALID_CHARS = ["''", "'ab'", "'中'", "'é'", "'\n'", "'\r'", "'a",
                 r"'\q'", r"'\r'", r"'\a'", r"'\x41'", r"'\101'", r"'\00'"]


def regression_cases():
    for name, source in VALID_PROGRAMS:
        yield name, source, 0
    for name, source in INVALID_PROGRAMS:
        yield name, source, 1
    for values, code, category in [
        (VALID_NUMBERS, 0, "valid_number"),
        (INVALID_NUMBERS, 1, "invalid_number"),
        (VALID_CHARS, 0, "valid_char"),
        (INVALID_CHARS, 1, "invalid_char"),
    ]:
        for index, value in enumerate(values):
            yield f"{category}_{index}", f"int main() {{ return {value}; }}", code
    yield "invalid_utf8", b"int a;\xff", 2
    # Exercise complete consumption and practical input size without PR2/PR3.
    yield "many_declarations", "int a;\n" * 2000, 0
    yield "long_comment", "/*" + "x\n" * 10000 + "*/ int a;", 0
    yield "long_arithmetic", "int f(){ return " + "+".join(["1"] * 500) + "; }", 0


def main():
    test_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=test_dir.parent / "build/compiler")
    parser.add_argument("--suite", choices=["all", "samples", "regressions"], default="all")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    if not compiler.is_file():
        parser.error(f"compiler does not exist: {compiler}")

    passed = total = 0

    def check(name, arguments, expected, location=None):
        nonlocal passed, total
        total += 1
        try:
            result = subprocess.run(
                [str(compiler), *map(str, arguments)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"FAIL {name}: {error}")
            return
        stderr = result.stderr.decode("utf-8", errors="replace")
        success = result.returncode == expected
        if location is not None:
            success = success and location in stderr
        if success:
            passed += 1
            if args.verbose:
                print(f"PASS {name}")
        else:
            print(f"FAIL {name}: expected exit {expected}, got {result.returncode}")
            print(stderr or result.stdout.decode("utf-8", errors="replace"))

    if args.suite in ("all", "samples"):
        samples = sorted((test_dir / "samples_lex_and_syntax").glob("*.cact"))
        if not samples:
            parser.error("no course PR1 samples found")
        for sample in samples:
            match = re.match(r"\d+_(true|false)_", sample.name)
            if not match:
                parser.error(f"unrecognized sample name: {sample.name}")
            check(sample.name, [sample], 0 if match[1] == "true" else 1)

    if args.suite in ("all", "regressions"):
        with tempfile.TemporaryDirectory(prefix="cact-pr1-") as temp:
            temp_dir = Path(temp)
            for name, source, code in regression_cases():
                path = temp_dir / f"{name}.cact"
                path.write_bytes(source if isinstance(source, bytes) else source.encode("utf-8"))
                check(name, [path], code)
            valid = temp_dir / "file with spaces.cact"
            valid.write_text("int main() { return 0; }\n", encoding="utf-8")
            check("filename_with_spaces", [valid], 0)
            check("missing_argument", [], 2)
            check("extra_argument", [valid, valid], 2)
            check("missing_file", [temp_dir / "absent.cact"], 2)
            check("directory_input", [temp_dir], 2)
            bad = temp_dir / "diagnostic.cact"
            bad.write_text("int main() {\n  return @0;\n}\n", encoding="utf-8")
            check("lexer_error_location", [bad], 1, f"{bad}:2:10: error:")
            bad.write_text("int main() {\n  return 0\n}\n", encoding="utf-8")
            check("parser_error_location", [bad], 1, f"{bad}:3:1: error:")

    print(f"PR1 {args.suite}: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
