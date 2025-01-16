#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default variable values
VERBOSE_MODE=false
KEEP_GIT_CREDENTIALS_FILE=false
PATH_PIP_SEARCH_FOLDER="./src"

# Function to display script usage
function usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo " -h, --help                     Display this help message"
    echo " -v, --verbose                  Enable verbose mode"
    echo " --git-credentials-file         use this git credentials file"
    echo " --keep-git-credentials-file    keep git credentials file (default: does not keep)"
    echo " --use-ci-job-token             use CI_JOB_TOKEN as password"
    echo " --path-pip-search-folder       path to search for directories matching the pattern 'module/resource/module' (default: ./src, if not exists, does not search)"
}

function has_argument {
    [[ ("$1" == *=* && -n ${1#*=}) || ( ! -z "$2" && "$2" != -*)  ]];
}

function extract_argument {
  echo "${2:-${1#*=}}"
}

# Function to handle options and arguments
function handle_options {
  while [ $# -gt 0 ]; do
    case $1 in
      -h | --help)
        usage
        exit 0
        ;;
      -v | --verbose)
        VERBOSE_MODE=true
        ;;
      --git-credentials-file)
        if ! has_argument $@; then
          echo "File not specified." >&2
          usage
          exit 1
        fi

        GIT_CREDENTIALS_FILE=$(extract_argument $@)

        shift
        ;;
      --keep-git-credentials-file)
        KEEP_GIT_CREDENTIALS_FILE=true
        ;;
      --use-ci-job-token)
        USE_CI_JOB_TOKEN=true
        ;;
      --path-pip-search-folder)
        if ! has_argument $@; then
          echo "Path not specified." >&2
          usage
          exit 1
        fi

        PATH_PIP_SEARCH_FOLDER=$(extract_argument $@)

        shift
        ;;
      *)
        echo "Invalid option: $1" >&2
        usage
        exit 1
        ;;
    esac
    shift
  done
}

# Main script execution
handle_options "$@"

# Perform the desired actions based on the provided flags and arguments
if [ "$VERBOSE_MODE" = true ]; then
 echo "Verbose mode enabled."
fi

function install_apt_deps {
    rv=0
    apt update
    apt install -y \
        python3-pip \
        git
    rv=$?
    return $rv
}

function install_pip_deps {
    rv=0
    pip3 install vcstool
    if [ $? -ne 0 ]; then
        echo "Error installing vcstool"
    fi

    return $rv
}

# This script searches for directories matching the pattern 'module/resource/module',
# where 'module' can be any name, and installs files within them using pip.
#
# Arguments:
#   path: The path to search for directories matching the pattern.
#
function install_module_resources {
    rv=0
    path=$1

    if [ -d "$path" ]; then
        # Find directories matching the pattern
        find "$path" -type d | while read -r dir; do
            # Get the components of the path
            IFS='/' read -ra path_components <<< "$dir"

            # Iterate over the indices of the path components
            for i in "${!path_components[@]}"; do
                # Check if the current component is 'resource'
                if [[ "${path_components[$i]}" == "resource" ]]; then
                    echo "------"
                    # Ensure there is a component before and after 'resource'
                    if [[ $i -ge 1 ]]; then
                        # Extract the module names before and after 'resource'
                        module="${path_components[$((i - 1))]}"

                        # Reconstruct the full path to the target directory
                        target_dir="${dir}"

                        # Print information about the directory and its modules
                        echo "Found directory: $target_dir"
                        echo "Module before 'resource': $module"

                        # Install files within the target directory
                        for file in "$target_dir"/*; do
                            filename=$(basename "$file")
                            echo "Checking file: $filename"
                            if [ "$module" == "$filename" ]; then
                                echo "Installing from $file"
                                pip3 install -r "$file"
                                if [ $? -ne 0 ]; then
                                    rv=$rv+1
                                fi
                            elif [ "$module.apt" == "$filename" ]; then
                                echo "Installing from $file"
                                xargs -a "$file" apt install -y
                                if [ $? -ne 0 ]; then
                                    rv=$rv+1
                                fi
                            fi
                        done

                        # Break to avoid multiple processing of the same directory
                        break
                    fi
                fi
            done
        done
    else
        echo "No directory found at $path"
        ls -l
        rv=1
    fi

    return $rv
}

function install_ros_deps {
    rosdep install --from-paths src --ignore-src -r -y
    rv=$?
}

function clone_repos {
    rv=0
    cd "$SCRIPT_DIR"
    vcs import .. < ../.rosinstall
    rv=$?
    cd -
    return $rv
}

error_counter=0
commands=(
    "install_apt_deps"
    "clone_repos"
    "install_pip_deps"
    "install_module_resources \"$PATH_PIP_SEARCH_FOLDER\""
    "install_ros_deps"
)

# Loop over each command and execute it
for cmd in "${commands[@]}"; do
    # Use eval to allow executing commands with arguments
    eval "$cmd"
    if [ $? -ne 0 ]; then
        error_counter=$(( error_counter + 1 ))
        echo "ERROR: $cmd"
    fi
done

echo "error counter $error_counter"

exit $error_counter
