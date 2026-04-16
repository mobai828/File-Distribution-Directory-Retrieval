import re

with open('/workspace/agentgithub/templates/index.html', 'r') as f:
    content = f.read()

start_str = "            // Handle form submission"
start_idx = content.find(start_str)

end_str = "        // Helper to remove markdown for TTS"
end_idx = content.find(end_str)

# Find the closing "        });\n" of DOMContentLoaded block
end_dom_idx = content.rfind("        });\n", start_idx, end_idx)

if start_idx == -1 or end_dom_idx == -1:
    print("Could not find boundaries")
    print(start_idx, end_dom_idx)
    import sys
    sys.exit(1)

with open('/workspace/patch.js', 'r') as f:
    patch_js = f.read()

with open('/workspace/patch2.js', 'r') as f:
    patch2_js = f.read()

# Replace the chatForm submit handler and insert appendAssistantResponse
new_content = content[:start_idx] + patch_js + "\n" + patch2_js + "\n" + content[end_dom_idx:]

with open('/workspace/agentgithub/templates/index.html', 'w') as f:
    f.write(new_content)

print("Replacement done")
