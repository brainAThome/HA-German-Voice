#!/usr/bin/env python3
"""
Parses HA logs for UserContent + ToolResultContent and stores conversations.
Run via cron every 5 minutes: */5 * * * * python3 /config/parse_conv_logs.py
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path("/config/conversation_memory.json")
LAST_PARSED_FILE = Path("/config/.last_parsed_timestamp")
MAX_CONVERSATIONS = 500

def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"conversations": [], "stats": {"total_count": 0}}

def save_memory(memory):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def get_last_parsed():
    if LAST_PARSED_FILE.exists():
        return LAST_PARSED_FILE.read_text().strip()
    return "1970-01-01 00:00:00"

def save_last_parsed(timestamp):
    LAST_PARSED_FILE.write_text(timestamp)

def get_ha_logs():
    """Get HA logs via ha command"""
    try:
        result = subprocess.run(
            ["ha", "core", "logs", "--lines", "2000"],
            capture_output=True, text=True, timeout=60
        )
        # Strip ANSI escape codes
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', result.stdout)
    except:
        return ""

def parse_conversations(logs):
    """Parse UserContent + ToolResultContent (success) AND failed intents from logs"""
    conversations = []
    
    # Join lines that are continuations (don't start with timestamp)
    lines = logs.split("\n")
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
    
    cleaned_logs = "\n".join(joined_lines)
    
    # Pattern for user input - look for UserContent with content=
    user_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*UserContent.*content='([^']+)'"
    
    # Pattern for tool result (SUCCESS) - look for ToolResultContent with speech
    tool_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*ToolResultContent.*tool_name='(\w+)'.*'speech': '([^']+)'"
    
    # Pattern for failed response - AssistantContent with content='...' and tool_calls=None
    # This indicates intent was NOT recognized
    fail_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*AssistantContent.*content='([^']+)'.*tool_calls=None"
    
    # Find all matches
    user_matches = list(re.finditer(user_pattern, cleaned_logs))
    tool_matches = list(re.finditer(tool_pattern, cleaned_logs))
    fail_matches = list(re.finditer(fail_pattern, cleaned_logs))
    
    # Track which user inputs have been matched to success
    matched_users = set()
    
    # Match user inputs with SUCCESSFUL responses (within 5 seconds)
    for user_match in user_matches:
        user_ts = datetime.strptime(user_match.group(1), "%Y-%m-%d %H:%M:%S")
        user_text = user_match.group(2)
        
        for tool_match in tool_matches:
            tool_ts = datetime.strptime(tool_match.group(1), "%Y-%m-%d %H:%M:%S")
            time_diff = (tool_ts - user_ts).total_seconds()
            
            if 0 <= time_diff < 5:
                intent = tool_match.group(2)
                response = tool_match.group(3).replace("\\n", " ").strip()
                
                conversations.append({
                    "timestamp": user_match.group(1),
                    "input": user_text,
                    "intent": intent,
                    "response": response,
                    "success": True
                })
                matched_users.add((user_match.group(1), user_text))
                break
    
    # Match remaining user inputs with FAILED responses
    for user_match in user_matches:
        user_key = (user_match.group(1), user_match.group(2))
        if user_key in matched_users:
            continue  # Already matched to success
        
        user_ts = datetime.strptime(user_match.group(1), "%Y-%m-%d %H:%M:%S")
        user_text = user_match.group(2)
        
        for fail_match in fail_matches:
            fail_ts = datetime.strptime(fail_match.group(1), "%Y-%m-%d %H:%M:%S")
            time_diff = (fail_ts - user_ts).total_seconds()
            
            if 0 <= time_diff < 5:
                error_response = fail_match.group(2).replace("\\n", " ").strip()
                
                conversations.append({
                    "timestamp": user_match.group(1),
                    "input": user_text,
                    "intent": None,  # No intent recognized
                    "response": error_response,
                    "success": False
                })
                break
    
    return conversations

def main():
    last_parsed = get_last_parsed()
    logs = get_ha_logs()
    
    if not logs:
        print("No logs available")
        return
    
    new_conversations = parse_conversations(logs)
    print(f"Parsed {len(new_conversations)} conversations from logs")
    
    if not new_conversations:
        print("No conversations found in logs")
        return
    
    # Filter to only new conversations (compare timestamp strings)
    new_convs = [c for c in new_conversations if c["timestamp"] > last_parsed]
    print(f"Found {len(new_convs)} new conversations (after {last_parsed})")
    
    memory = load_memory()
    added = 0
    
    for conv in new_convs:
        # Check for duplicates
        existing = any(
            c["timestamp"] == conv["timestamp"] and c["input"] == conv["input"]
            for c in memory["conversations"]
        )
        if existing:
            continue
        
        new_id = memory["stats"]["total_count"] + 1
        entry = {
            "id": new_id,
            "timestamp": conv["timestamp"],
            "input": conv["input"],
            "intent": conv.get("intent"),  # None for failed
            "response": conv["response"],
            "success": conv.get("success", True)  # Use actual success value
        }
        memory["conversations"].insert(0, entry)
        memory["stats"]["total_count"] = new_id
        memory["stats"]["last_updated"] = conv["timestamp"]
        added += 1
    
    # Keep only MAX_CONVERSATIONS
    if len(memory["conversations"]) > MAX_CONVERSATIONS:
        memory["conversations"] = memory["conversations"][:MAX_CONVERSATIONS]
    
    save_memory(memory)
    
    # Update last parsed timestamp
    if new_convs:
        save_last_parsed(new_convs[-1]["timestamp"])
    
    print(f"Added {added} new conversations. Total: {memory['stats']['total_count']}")

if __name__ == "__main__":
    main()
