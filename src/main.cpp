#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

#include "antlr4-runtime.h"
#include "CACTLexer.h"
#include "CACTParser.h"

namespace {

class SyntaxError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

// ANTLR normally recovers from errors. Throw from BOTH recognizers so that a
// skipped illegal character or an inserted token can never turn into success.
class ThrowingErrorListener final : public antlr4::BaseErrorListener {
public:
    void syntaxError(antlr4::Recognizer*, antlr4::Token*, size_t line,
                     size_t column, const std::string& message,
                     std::exception_ptr) override {
        throw SyntaxError(std::to_string(line) + ":" +
                          std::to_string(column + 1) + ": error: " + message);
    }
};

} // namespace

int main(int argc, const char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <source.cact>\n";
        return 2;
    }

    try {
        std::ifstream source(argv[1], std::ios::binary);
        if (!source.is_open()) {
            std::cerr << argv[1] << ": error: cannot open input file\n";
            return 2;
        }
        source.exceptions(std::ios::badbit);

        antlr4::ANTLRInputStream input(source);
        ThrowingErrorListener errors;
        CACTLexer lexer(&input);
        lexer.removeErrorListeners();
        lexer.addErrorListener(&errors);

        antlr4::CommonTokenStream tokens(&lexer);
        CACTParser parser(&tokens);
        parser.removeErrorListeners();
        parser.addErrorListener(&errors);

        // compUnit includes EOF: a valid prefix does not hide a malformed tail.
        parser.compUnit();
        return 0;
    } catch (const SyntaxError& error) {
        std::cerr << argv[1] << ':' << error.what() << '\n';
        return 1;
    } catch (const std::exception& error) {
        std::cerr << argv[1] << ": error: " << error.what() << '\n';
        return 2;
    }
}
