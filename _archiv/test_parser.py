#!/usr/bin/env python3
"""Test log parsing"""
import re
import subprocess

# Get logs
result = subprocess.run(["ha", "core", "logs", "--lines", "500"], capture_output=True, text=True, timeout=60)

# Strip ANSI escape codes
ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
logs = ansi_escape.sub('', result.stdout)

print(f"Got {len(logs)} characters of logs (after ANSI strip)")
lines = logs.split("\n")
print(f"Split into {len(lines)} lines")

# Debug first few lines
for i, line in enumerate(lines[:5]):
    ts_match = re.match(r"\d{4}-\d{2}-\d{2}", line)
    print(f"Line {i}: hasTS={bool(ts_match)} start='{line[:40]}...'")

# Join lines that are continuations
joined_lines = []
current = ""
for line in lines:
    if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line):
        if current:
            joined_lines.append(current)
        current = line
    else:
        current += " " + line.strip()
if current:
    joined_lines.append(current)

print(f"Joined into {len(joined_lines)} log entries")

# Pattern for user input
user_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*UserContent.*content='([^']+)'"
user_matches = list(re.finditer(user_pattern, "\n".join(joined_lines)))
print(f"Found {len(user_matches)} user inputs")

# Pattern for tool result
tool_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*ToolResultContent.*tool_name='(\w+)'.*'speech': '([^']+)'"
tool_matches = list(re.finditer(tool_pattern, "\n".join(joined_lines)))
print(f"Found {len(tool_matches)} tool results")

# Show examples
for m in user_matches[:10]:
    print(f"User: {m.group(1)} - {m.group(2)[:60]}...")
print("---")
for m in tool_matches[:10]:
    print(f"Tool: {m.group(1)} - {m.group(2)} - {m.group(3)[:40]}...")
