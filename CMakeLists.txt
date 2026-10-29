cmake_minimum_required(VERSION 3.16)
project(Compiler LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(THREADS_PREFER_PTHREAD_FLAG ON)

find_package(Java 11 REQUIRED COMPONENTS Runtime)
find_package(Threads REQUIRED)

file(GLOB_RECURSE ANTLR_LIB_FILES CONFIGURE_DEPENDS
     "${CMAKE_CURRENT_SOURCE_DIR}/deps/antlr4-runtime/*.cpp")
add_library(antlr STATIC ${ANTLR_LIB_FILES})
target_include_directories(antlr SYSTEM PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/deps/antlr4-runtime")
target_link_libraries(antlr PUBLIC Threads::Threads)

# Generate into the build directory. A clean checkout needs no generated files,
# and editing a .g4 file automatically regenerates its parser on the next build.
function(add_antlr_grammar target grammar_name)
    set(generated_dir "${CMAKE_CURRENT_BINARY_DIR}/generated/${grammar_name}")
    set(grammar_file "${CMAKE_CURRENT_SOURCE_DIR}/grammar/${grammar_name}.g4")
    set(antlr_jar "${CMAKE_CURRENT_SOURCE_DIR}/deps/antlr-4.13.1-complete.jar")
    set(generated_files)
    foreach(component Lexer Parser Visitor BaseVisitor)
        list(APPEND generated_files
            "${generated_dir}/${grammar_name}${component}.cpp"
            "${generated_dir}/${grammar_name}${component}.h")
    endforeach()
    add_custom_command(
        OUTPUT ${generated_files}
        BYPRODUCTS
            "${generated_dir}/${grammar_name}.interp"
            "${generated_dir}/${grammar_name}.tokens"
            "${generated_dir}/${grammar_name}Lexer.interp"
            "${generated_dir}/${grammar_name}Lexer.tokens"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${generated_dir}"
        COMMAND "${Java_JAVA_EXECUTABLE}" -jar "${antlr_jar}"
                -Dlanguage=Cpp -visitor -no-listener -Werror
                -o "${generated_dir}" "${grammar_file}"
        DEPENDS "${grammar_file}" "${antlr_jar}"
        COMMENT "Generating ${grammar_name} lexer and parser with ANTLR 4.13.1"
        VERBATIM)
    add_library(${target} STATIC EXCLUDE_FROM_ALL ${generated_files})
    target_include_directories(${target} PUBLIC "${generated_dir}")
    target_link_libraries(${target} PUBLIC antlr)
endfunction()

add_antlr_grammar(cact_grammar CACT)
add_executable(compiler src/main.cpp)
target_link_libraries(compiler PRIVATE cact_grammar)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(compiler PRIVATE -Wall -Wextra -Wpedantic)
endif()

# The original tutorial is available explicitly, without becoming the compiler.
add_antlr_grammar(hello_grammar Hello)
add_executable(hello_demo EXCLUDE_FROM_ALL test/hello_demo.cpp)
target_link_libraries(hello_demo PRIVATE hello_grammar)

include(CTest)
if(BUILD_TESTING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    add_test(NAME pr1_samples
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/test/test_pr1.py"
                --compiler $<TARGET_FILE:compiler> --suite samples)
    add_test(NAME pr1_regressions
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/test/test_pr1.py"
                --compiler $<TARGET_FILE:compiler> --suite regressions)
endif()
