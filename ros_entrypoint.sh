#!/bin/bash
set -e

# Source the ROS 2 Humble setup script
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source "/opt/ros/humble/setup.bash"
fi

# Source any workspace setup files (optional, if you have built your workspace)
if [ -f "/workspace/install/setup.bash" ]; then
    source "/workspace/install/setup.bash"
fi

# Execute the passed command
exec "$@"
