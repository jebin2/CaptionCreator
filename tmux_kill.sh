#!/bin/bash

terminate_session() {
    tmux kill-session -t caption_creator
    echo "Session 'caption_creator' has been terminated."
}

# You can call this function when needed, or bind it to a key in tmux