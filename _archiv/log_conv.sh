#!/bin/sh
echo "$(date '+%Y-%m-%d %H:%M:%S') | FRAGE: $1 | INTENT: $2 | ANTWORT: $3" >> /config/conversation_log.txt
