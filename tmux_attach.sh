#!/bin/bash

# Check if the session exists
if tmux has-session -t caption_creator 2>/dev/null; then
    # If it exists, attach to it
    tmux attach-session -t caption_creator
else
    # If it doesn't exist, inform the user
    echo "Session 'caption_creator' does not exist."
    echo "You may need to run the script to create the session first."
fi