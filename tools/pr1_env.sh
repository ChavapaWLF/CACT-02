# Source this file after running tools/setup_pr1.sh.
export CACT_PR1_TOOLS="${CACT_PR1_TOOLS:-$HOME/.local/share/cact-pr1}"
export JAVA_HOME="$CACT_PR1_TOOLS/jdk-17"
export PATH="$JAVA_HOME/bin:$CACT_PR1_TOOLS/cmake-3.31.12/bin:$PATH"
