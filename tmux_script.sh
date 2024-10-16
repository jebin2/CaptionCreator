#!/bin/bash

# Start a new tmux session named 'caption_creator'
tmux new-session -d -s caption_creator

# Split the window into four panes (2x2 layout)
tmux split-window -v
tmux split-window -h
tmux select-pane -t 0
tmux split-window -h

# Run the commands in the respective panes
tmux send-keys -t caption_creator:0.0 'cd ContentData && bun run index.ts' C-m  # Pane 1 (top-left)
tmux send-keys -t caption_creator:0.1 'python3 audiotovideo.py' C-m  # Pane 2 (top-right)
tmux send-keys -t caption_creator:0.2 'python3 publish_to_yt.py' C-m  # Pane 3 (bottom-left)
tmux send-keys -t caption_creator:0.3 'python3 publish_to_x.py' C-m  # Pane 4 (bottom-right)

# Set titles for each pane
tmux select-pane -t caption_creator:0.0 -T 'Index Script'      # Title for Pane 1
tmux select-pane -t caption_creator:0.1 -T 'Audio to Video'     # Title for Pane 2
tmux select-pane -t caption_creator:0.2 -T 'Publish to YT'      # Title for Pane 3
tmux select-pane -t caption_creator:0.3 -T 'Publish to X'    # Title for Pane 4

# Attach to the session
tmux attach -t caption_creator