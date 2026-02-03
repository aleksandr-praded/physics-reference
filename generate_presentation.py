# generate_presentation.py
import sqlite3
from jinja2 import Template
import argparse
from collections import defaultdict

def fix_latex_escapes(s):
    return "" if s is None else s.replace('\\\\', '\\')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", nargs='+')
    parser.add_argument("--school", nargs='+')
    parser.add_argument("--university", nargs='+')
    args = parser.parse_args()

    conn = sqlite3.connect('physics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT key, symbol_latex, description_ru, unit FROM variables")
    variables_dict = {
        r['key']: {'symbol': fix_latex_escapes(r['symbol_latex']), 'desc': r['description_ru'], 'unit': r['unit']}
        for r in cursor.fetchall()
    }

    cursor.execute("SELECT id, citation FROM sources ORDER BY id")
    all_sources = {r[0]: r[1] for r in cursor.fetchall()}

    # Формулы
    cursor.execute("SELECT * FROM formulas ORDER BY section, subsection, name")
    formulas = []
    used_source_ids = set()
    for f in cursor.fetchall():
        if args.section and not any(s.lower() in f['section'].lower() for s in args.section): continue
        keys = [k.strip() for k in f['variable_keys'].split(',')]
        vars_list = [
            variables_dict[key] if key in variables_dict
            else {'symbol': f"[{key}]", 'desc': "неизвестная переменная", 'unit': ""}
            for key in keys
        ]
        cursor.execute("SELECT source_id FROM formula_sources WHERE formula_id = ?", (f['id'],))
        src_ids = [r[0] for r in cursor.fetchall()]
        used_source_ids.update(src_ids)
        formulas.append({
            'name': f['name'],
            'formula_latex': fix_latex_escapes(f['formula_latex']),
            'variables': vars_list,
            'sources': src_ids
        })

    # Концепции
    cursor.execute("SELECT * FROM concepts ORDER BY section, subsection, name")
    concepts = []
    for c in cursor.fetchall():
        if args.section and not any(s.lower() in c['section'].lower() for s in args.section): continue
        cursor.execute("SELECT source_id FROM concept_sources WHERE concept_id = ?", (c['id'],))
        src_ids = [r[0] for r in cursor.fetchall()]
        used_source_ids.update(src_ids)
        concepts.append({
            'name': c['name'],
            'definition': c['definition'],
            'sources': src_ids
        })

    sources = {sid: all_sources[sid] for sid in used_source_ids if sid in all_sources}
    conn.close()

    with open('templates/presentation.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    html = template.render(formulas=formulas, concepts=concepts, sources=sources)

    with open('presentation.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ Презентация создана: presentation.html")

if __name__ == "__main__":
    main()