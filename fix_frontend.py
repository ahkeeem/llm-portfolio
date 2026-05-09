import re

# 1. Fix HTML
with open('/tmp/old_index.html', 'r') as f:
    old_html = f.read()

with open('index.html', 'r') as f:
    new_html = f.read()

# Extract demo content from old HTML
# It's inside <div class="demo-tabs"> ... up to the end of <div id="demo-receipt" ...>
demo_match = re.search(r'(<div class="demo-tabs">.*?<!-- === END DEMOS === -->)', old_html, re.DOTALL)
if not demo_match:
    # Alternative boundary search
    demo_match = re.search(r'(<div class="demo-tabs">.*?</section>)', old_html, re.DOTALL)
    # We just want up to the end of demo-receipt
    demo_inner = re.search(r'(<div class="demo-tabs">.*?</div>\s*</div>\s*</div>)', demo_match.group(1), re.DOTALL)
    demo_content = demo_inner.group(1) if demo_inner else demo_match.group(1)
else:
    demo_content = demo_match.group(1)
    
# Architecture content
arch_match = re.search(r'(<div class="arch-grid">.*?</div>\s*</div>\s*</section>)', old_html, re.DOTALL)
arch_content = re.search(r'(<div class="arch-grid">.*?</div>\s*</div>)', arch_match.group(1), re.DOTALL).group(1) if arch_match else ""

# Skills content
skills_match = re.search(r'(<div class="skills-grid">.*?</div>\s*</div>\s*</section>)', old_html, re.DOTALL)
skills_content = re.search(r'(<div class="skills-grid">.*?</div>\s*</div>)', skills_match.group(1), re.DOTALL).group(1) if skills_match else ""

# Replace in new HTML
new_html = re.sub(r'<!-- Demo UI will be populated by script.js after metrics are fetched -->', demo_content, new_html)
new_html = re.sub(r'<div class="arch-grid">\s*<!-- Architecture cards .*? -->\s*</div>', arch_content, new_html)
new_html = re.sub(r'<div class="skills-grid">\s*<!-- Skills cards .*? -->\s*</div>', skills_content, new_html)

with open('index.html', 'w') as f:
    f.write(new_html)

# 2. Fix CSS
with open('/tmp/old_style.css', 'r') as f:
    old_css = f.read()

with open('style.css', 'r') as f:
    new_css = f.read()

# Extract everything from /* === DEMO TABS === */ onwards
css_match = re.search(r'(/\* === DEMO TABS === \*/.*)', old_css, re.DOTALL)
if css_match:
    missing_css = css_match.group(1)
    # Append to new CSS, replacing the placeholder comment
    new_css = re.sub(r'/\* \.\.\. rest of original stylesheet left unchanged \.\.\. \*/', missing_css, new_css)
    with open('style.css', 'w') as f:
        f.write(new_css)

print("Frontend HTML and CSS patched successfully.")
