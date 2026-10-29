#!/usr/bin/env bash
# User-local, reproducible bootstrap for the Ubuntu x86_64 PR1 environment.
set -euo pipefail

if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo "This bootstrap targets Linux x86_64; install Java >= 11 and CMake >= 3.16 for other platforms." >&2
    exit 1
fi
for tool in curl tar sha256sum g++ make python3; do
    if ! command -v "$tool" >/dev/null; then
        echo "Missing prerequisite: $tool" >&2
        exit 1
    fi
done

tools_dir="${CACT_PR1_TOOLS:-$HOME/.local/share/cact-pr1}"
mkdir -p "$tools_dir"
stage=$(mktemp -d "$tools_dir/.install.XXXXXX")
trap 'rm -rf -- "$stage"' EXIT

install_archive() {
    local name=$1 executable=$2 checksum=$3 url=$4
    if [[ -x "$tools_dir/$name/bin/$executable" ]]; then
        echo "Already installed: $tools_dir/$name"
        return
    fi
    if [[ -e "$tools_dir/$name" ]]; then
        echo "Installation destination already exists: $tools_dir/$name" >&2
        return 1
    fi
    mkdir -p "$stage/$name"
    curl -fL --retry 3 --connect-timeout 20 --max-time 600 \
        "$url" -o "$stage/$name.tar.gz"
    printf '%s  %s\n' "$checksum" "$stage/$name.tar.gz" | sha256sum -c -
    tar -xzf "$stage/$name.tar.gz" --strip-components=1 -C "$stage/$name"
    test -x "$stage/$name/bin/$executable"
    mv "$stage/$name" "$tools_dir/$name"
}

# Official Eclipse Adoptium release; checksum from its release metadata.
install_archive jdk-17 java \
    8b9b611d917e3dfd8419d3566b5949226f69b052fed7e109c1368add1dfe8711 \
    'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/OpenJDK17U-jdk_x64_linux_hotspot_17.0.21_9.tar.gz'

# Official Kitware binary; checksum from cmake-3.31.12-SHA-256.txt.
install_archive cmake-3.31.12 cmake \
    0dc2e9a6860f06bf10bd8fadc03e35d9eeb4df46e33763a7e480e987758f385c \
    'https://cmake.org/files/v3.31/cmake-3.31.12-linux-x86_64.tar.gz'

"$tools_dir/jdk-17/bin/java" -version
"$tools_dir/cmake-3.31.12/bin/cmake" --version
echo "Ready. From the repository root, run: source tools/pr1_env.sh"
