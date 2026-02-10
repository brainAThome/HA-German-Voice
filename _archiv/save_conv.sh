#!/bin/sh
# Simple wrapper for conversation memory
# Usage: save_conv.sh "frage" "intent" "antwort"
python3 /config/conversation_memory.py add "$1" "$2" "$3" "{}"
