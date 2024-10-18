#!/bin/bash

# Update package list and install required packages
sudo apt update

# Install required packages for the project
sudo apt install -y \
    python3 \
    python3-pip \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfreetype6-dev \
    libharfbuzz-dev \
    sqlite3 \
    python3-opencv
