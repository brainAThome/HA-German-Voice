#!/usr/bin/env python3
"""
Conversation Memory System for Home Assistant
Stores the last N conversations in a rotating JSON file for training purposes.
"""
import json
import os
import sys
from datetime import datetime

MEMORY_FILE = "/config/conversation_memory.json"
MAX_CONVERSATIONS = 200

def load_memory():
    """Load existing conversation memory."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"conversations": [], "stats": {"total_count": 0}}
    return {"conversations": [], "stats": {"total_count": 0}}

def save_memory(memory):
    """Save conversation memory to file."""
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def add_conversation(frage, intent, slots, antwort, erfolg=True):
    """Add a new conversation to memory with FIFO rotation."""
    memory = load_memory()
    
    conversation = {
        "id": memory["stats"]["total_count"] + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input": frage,
        "intent": intent,
        "slots": slots if slots else {},
        "response": antwort,
        "success": erfolg
    }
    
    # Add to beginning (newest first)
    memory["conversations"].insert(0, conversation)
    
    # Keep only last MAX_CONVERSATIONS
    if len(memory["conversations"]) > MAX_CONVERSATIONS:
        memory["conversations"] = memory["conversations"][:MAX_CONVERSATIONS]
    
    # Update stats
    memory["stats"]["total_count"] += 1
    memory["stats"]["last_updated"] = conversation["timestamp"]
    
    save_memory(memory)
    return conversation["id"]

def get_stats():
    """Get memory statistics."""
    memory = load_memory()
    stats = memory.get("stats", {})
    stats["current_stored"] = len(memory.get("conversations", []))
    stats["max_capacity"] = MAX_CONVERSATIONS
    return stats

def export_training_data(output_file="/config/training_data.jsonl"):
    """Export conversations as JSONL for training."""
    memory = load_memory()
    with open(output_file, 'w', encoding='utf-8') as f:
        for conv in memory.get("conversations", []):
            training_entry = {
                "input": conv.get("input", ""),
                "intent": conv.get("intent", ""),
                "slots": conv.get("slots", {}),
                "output": conv.get("response", "")
            }
            f.write(json.dumps(training_entry, ensure_ascii=False) + "\n")
    return len(memory.get("conversations", []))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: conversation_memory.py <command> [args]")
        print("Commands: add, stats, export")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) >= 5:
            frage = sys.argv[2]
            intent = sys.argv[3]
            antwort = sys.argv[4]
            slots = sys.argv[5] if len(sys.argv) > 5 else "{}"
            conv_id = add_conversation(frage, intent, slots, antwort)
            print(f"Added conversation #{conv_id}")
        else:
            print("Usage: add <frage> <intent> <antwort> [slots]")
    
    elif command == "stats":
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    
    elif command == "export":
        output = sys.argv[2] if len(sys.argv) > 2 else "/config/training_data.jsonl"
        count = export_training_data(output)
        print(f"Exported {count} conversations to {output}")
    
    else:
        print(f"Unknown command: {command}")
