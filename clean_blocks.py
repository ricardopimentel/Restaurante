import os
import re

# Match {% block top %} ... {% endblock %} and {% block menu %} ... {% endblock %}
pattern_top = re.compile(r'\{%\s*block\s+top\s*%\}.*?\{%\s*endblock\s*%\}', re.DOTALL)
pattern_menu = re.compile(r'\{%\s*block\s+menu\s*%\}.*?\{%\s*endblock\s*%\}', re.DOTALL)

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = pattern_top.sub('', content)
    new_content = pattern_menu.sub('', new_content)

    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Cleaned {path}")

base_dir = r"d:\Documentos\Projetos\Restaurante\restaurante"

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.html') and f != 'base.html':
            clean_file(os.path.join(root, f))

print("Cleanup complete!")
