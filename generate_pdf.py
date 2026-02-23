# generate_pdf.py
import sqlite3
from jinja2 import Template
import subprocess
import os
import argparse
from collections import defaultdict

def fix_latex_escapes(s):
    if s is None:
        return ""
    return s.replace('\\\\', '\\')

def parse_intervals(input_list):
    result = set()
    if not input_list:
        return result
    for item in input_list:
        if '-' in item:
            try:
                start, end = map(int, item.split('-'))
                result.update(range(start, end + 1))
            except ValueError:
                result.add(item)
        else:
            try:
                result.add(int(item))
            except ValueError:
                result.add(item)
    return result

def matches_interval(db_value, allowed_set):
    if not db_value or not allowed_set:
        return False
    db_parts = str(db_value).split('-')
    try:
        if len(db_parts) == 2:
            start, end = int(db_parts[0]), int(db_parts[1])
            db_numbers = set(range(start, end + 1))
        else:
            db_numbers = {int(db_value)}
        return bool(db_numbers & allowed_set)
    except ValueError:
        return db_value in allowed_set

def filter_by_level(level_str, school_set, univ_set):
    if not level_str:
        return True
    if ':' not in level_str:
        return True
    lvl_type, lvl_val = level_str.split(':', 1)
    if school_set and lvl_type == 'school':
        return matches_interval(lvl_val, school_set)
    if univ_set and lvl_type == 'university':
        return matches_interval(lvl_val, univ_set)
    if not school_set and not univ_set:
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Генерация справочника по физике")
    parser.add_argument("--name", nargs='+', type=str, help="Название формулы или концепции")
    parser.add_argument("--section", nargs='+', type=str, help="Раздел: механика, термодинамика...")
    parser.add_argument("--subsection", nargs='+', type=str, help="Подраздел: кинематика, динамика...")
    parser.add_argument("--school", nargs='+', type=str, help="Класс(ы): 7, 8-9, 10...")
    parser.add_argument("--university", nargs='+', type=str, help="Курс(ы): 1, 2-4, 3+...")
    parser.add_argument("--description", nargs='+', type=str, help="Описание переменной")
    parser.add_argument("--unit", nargs='+', type=str, help="Единица измерения")
    parser.add_argument("--toc", action="store_true", help="Добавить оглавление")
    parser.add_argument("--bibliography", action="store_true", help="Добавить список литературы")

    args = parser.parse_args()

    conn = sqlite3.connect('physics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Загрузка переменных
    cursor.execute("SELECT key, symbol_latex, description_ru, unit FROM variables")
    variables_dict = {
        row['key']: {
            'symbol': fix_latex_escapes(row['symbol_latex']),
            'desc': row['description_ru'],
            'unit': row['unit']
        }
        for row in cursor.fetchall()
    }

    school_set = parse_intervals(args.school)
    univ_set = parse_intervals(args.university)

    # === Фильтрация формул ===
    cursor.execute("SELECT * FROM formulas/* ORDER BY section, subsection, name*/")
    all_formulas = cursor.fetchall()
    filtered_formulas = []
    for f in all_formulas:
        if args.name and not any(n.lower() in f['name'].lower() for n in args.name):
            continue
        if args.section and not any(s.lower() in f['section'].lower() for s in args.section):
            continue
        if args.subsection and not any(sb.lower() in f['subsection'].lower() for sb in args.subsection):
            continue
        if not filter_by_level(f['level'], school_set, univ_set):
            continue

        keys = [k.strip() for k in f['variable_keys'].split(',')]
        desc_ok = True
        unit_ok = True
        if args.description:
            desc_ok = any(
                any(d.lower() in variables_dict.get(k, {}).get('desc', '').lower() for d in args.description)
                for k in keys if k in variables_dict
            )
        if args.unit:
            unit_ok = any(
                any(u.lower() in variables_dict.get(k, {}).get('unit', '').lower() for u in args.unit)
                for k in keys if k in variables_dict
            )
        if desc_ok and unit_ok:
            cursor.execute("SELECT source_id FROM formula_sources WHERE formula_id = ?", (f['id'],))
            source_ids = [r[0] for r in cursor.fetchall()]
            filtered_formulas.append((f, source_ids))

    # === Фильтрация концепций ===
    cursor.execute("SELECT * FROM concepts/* ORDER BY section, subsection, name*/")
    all_concepts = cursor.fetchall()
    filtered_concepts = []
    for c in all_concepts:
        if args.name and not any(n.lower() in c['name'].lower() for n in args.name):
            continue
        if args.section and not any(s.lower() in c['section'].lower() for s in args.section):
            continue
        if args.subsection and not any(sb.lower() in c['subsection'].lower() for sb in args.subsection):
            continue
        if not filter_by_level(c['level'], school_set, univ_set):
            continue
        cursor.execute("SELECT source_id FROM concept_sources WHERE concept_id = ?", (c['id'],))
        source_ids = [r[0] for r in cursor.fetchall()]
        filtered_concepts.append((c, source_ids))

    # === Сбор использованных источников и группировка ===
    used_source_ids = set()
    sections_dict = defaultdict(lambda: defaultdict(lambda: {'formulas': [], 'concepts': []}))

    for f, src_ids in filtered_formulas:
        if args.bibliography:
            used_source_ids.update(src_ids)
        sections_dict[f['section']][f['subsection']]['formulas'].append({
            'name': f['name'],
            'formula_latex': fix_latex_escapes(f['formula_latex']),
            'variable_keys': f['variable_keys'],
            'variables': variables_dict,
            'image_path': f['image_path'],
            'sources': src_ids if args.bibliography else []
        })

    for c, src_ids in filtered_concepts:
        if args.bibliography:
            used_source_ids.update(src_ids)
        sections_dict[c['section']][c['subsection']]['concepts'].append({
            'name': c['name'],
            'definition': c['definition'],
            'image_path': c['image_path'],
            'sources': src_ids if args.bibliography else []
        })

    # === Формирование items ===
    items = []
    for section, subsections in sorted(sections_dict.items()):
        subsections_list = []
        for subsection, content in sorted(subsections.items()):
            subsections_list.append({
                'name': subsection,
                'formulas': content['formulas'],
                'concepts': content['concepts']
            })
        items.append({
            'name': section,
            'subsections': subsections_list
        })

    # === Загрузка только используемых источников ===
    if args.bibliography and used_source_ids:
        placeholders = ','.join('?' * len(used_source_ids))
        cursor.execute(f"SELECT id, citation FROM sources WHERE id IN ({placeholders}) ORDER BY id", list(used_source_ids))
        used_sources = {row[0]: row[1] for row in cursor.fetchall()}
    else:
        used_sources = {}

    conn.close()

    # === Генерация PDF ===
    with open('templates/physics.tex', 'r', encoding='utf-8') as f:
        template_str = f.read()

    template = Template(template_str)
    latex_output = template.render(
        items=items,
        sources=used_sources,
        toc=args.toc,
        bibliography=args.bibliography
    )

    with open('output.tex', 'w', encoding='utf-8') as f:
        f.write(latex_output)

    try:
        for _ in range(2):
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', 'output.tex'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        print("✅ PDF создан: output.pdf")
        for ext in ['tex', 'log', 'aux', 'out', 'toc']:
            try:
                os.remove(f'output.{ext}')
            except FileNotFoundError:
                pass
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()