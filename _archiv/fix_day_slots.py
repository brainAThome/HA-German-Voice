import re

# Read the file
with open('intent_script.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find: {% set day_slot = day | default(X) | int %}
pattern = r"\{% set day_slot = day \| default\((\d+)\) \| int %\}"

# Replacement template
def make_replacement(match):
    default_val = match.group(1)
    return f"""{{% set day_input = day | default({default_val}) %}}
      {{% set weekday_map = {{'montag': 0, 'dienstag': 1, 'mittwoch': 2, 'donnerstag': 3, 'freitag': 4, 'samstag': 5, 'sonntag': 6}} %}}
      {{% set today_weekday = now().weekday() %}}
      {{% if day_input in weekday_map %}}
        {{% set target_weekday = weekday_map[day_input] %}}
        {{% set days_until = (target_weekday - today_weekday) % 7 %}}
        {{% set days_until = days_until if days_until > 0 else 7 %}}
        {{% set day_slot = days_until %}}
      {{% else %}}
        {{% set day_slot = day_input | int(default={default_val}) %}}
      {{% endif %}}"""

# Count occurrences first
matches = re.findall(pattern, content)
print(f"Found {len(matches)} occurrences to fix")

# Replace all occurrences
new_content = re.sub(pattern, make_replacement, content)

# Write back
with open('intent_script.yaml', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done! Fixed all day_slot patterns.")
