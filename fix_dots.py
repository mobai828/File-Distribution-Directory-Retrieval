import sys
content = open('/workspace/patch.js').read()
content = content.replace("<span></span>\n                    <span></span>\n                    <span></span>", "<div class=\"typing-indicator\">\n                        <span></span><span></span><span></span>\n                    </div>")
open('/workspace/patch.js', 'w').write(content)
