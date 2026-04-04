# generate_presentation.py
import sqlite3
from jinja2 import Template
import argparse
import random

def fix_latex_escapes(s):
    return "" if s is None else s.replace('\\\\', '\\')

def matches_level(db_level, allowed_school, allowed_univ):
    if not db_level:
        return True
    if ':' not in db_level:
        return True
    lvl_type, lvl_val = db_level.split(':', 1)
    try:
        lvl_num = int(lvl_val)
    except ValueError:
        return True
    school_strs = [str(x) for x in (allowed_school or [])]
    univ_strs = [str(x) for x in (allowed_univ or [])]
    if allowed_school and lvl_type == 'school':
        return str(lvl_num) in school_strs
    if allowed_univ and lvl_type == 'university':
        return str(lvl_num) in univ_strs
    return not allowed_school and not allowed_univ

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", nargs='+', type=str, help="Фильтр по названию (точное совпадение)")
    parser.add_argument("--section", nargs='+')
    parser.add_argument("--subsection", nargs='+')
    parser.add_argument("--school", nargs='+', type=int, help="Номера школьных классов (например: 7 8 9)")
    parser.add_argument("--university", nargs='+', type=int, help="Номера курсов (например: 1 2)")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Количество вопросов в варианте")
    parser.add_argument("--variants", "-v", type=int, default=1, help="Количество вариантов")
    parser.add_argument("--output-prefix", type=str, default="presentation", help="Префикс для имён файлов")
    parser.add_argument("--adaptive-time", type=float, 
                        help="Коэффициент для адаптивного времени (сек/символ). Если не задан — фиксированное время.")
    args = parser.parse_args()

    conn = sqlite3.connect('physics.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Загрузка переменных с обработкой NULL
    cursor.execute("SELECT key, symbol_latex, description_ru, unit FROM variables")
    variables_dict = {
        r['key']: {
            'symbol': fix_latex_escapes(r['symbol_latex']) or "",
            'desc': r['description_ru'] or "",
            'unit': r['unit'] or ""
        }
        for r in cursor.fetchall()
    }

    items = []
    
    # === Обработка формул ===
    cursor.execute("SELECT * FROM formulas")
    for f in cursor.fetchall():
        if args.name and not any(f['name'].strip().lower() == n.strip().lower() for n in args.name):
            continue
        if args.section and not any(s.lower() in f['section'].lower() for s in args.section):
            continue
        if args.subsection and not any(sb.lower() in f['subsection'].lower() for sb in args.subsection):
            continue
        if not matches_level(f['level'], args.school, args.university):
            continue
        
        name_with_formula = f"{f['name']} (формула)"
        formula_content = fix_latex_escapes(f['formula_latex']) or ""
        
        # Расчёт общей длины текста для записи
        total_length = len(formula_content)
        
        if args.adaptive_time is not None:
            keys = [k.strip() for k in f['variable_keys'].split(',') if k.strip()]
            for key in keys:
                if key in variables_dict:
                    var = variables_dict[key]
                    total_length += len(var['symbol'])
                    total_length += len(var['desc'])
                    total_length += len(var['unit'])
        
        # Определение длительности
        if args.adaptive_time is not None:
            duration_ms = int(total_length * args.adaptive_time * 1000)
        else:
            duration_ms = 90_000  # 90 сек по умолчанию
        
        items.append({
            'type': 'formula',
            'name': name_with_formula,
            'content': formula_content,
            'duration': duration_ms
        })

    # === Обработка концепций ===
    cursor.execute("SELECT * FROM concepts")
    for c in cursor.fetchall():
        if args.name and not any(c['name'].strip().lower() == n.strip().lower() for n in args.name):
            continue
        if args.section and not any(s.lower() in c['section'].lower() for s in args.section):
            continue
        if args.subsection and not any(sb.lower() in c['subsection'].lower() for sb in args.subsection):
            continue
        if not matches_level(c['level'], args.school, args.university):
            continue
        
        content = c['definition'] or ""
        if args.adaptive_time is not None:
            duration_ms = int(len(content) * args.adaptive_time * 1000)
        else:
            duration_ms = 120_000  # 120 сек по умолчанию
        
        items.append({
            'type': 'concept',
            'name': c['name'],
            'content': content,
            'duration': duration_ms
        })
    
    conn.close()

    if not items:
        print("⚠️ Нет данных, удовлетворяющих фильтрам")
        return

    for var_num in range(1, args.variants + 1):
        pool = items.copy()
        random.shuffle(pool)
        selected = pool[:args.limit]

        # Сохранение списка ответов
        quiz_file = f"{args.output_prefix}_variant_{var_num}.txt"
        with open(quiz_file, 'w', encoding='utf-8') as f_list:
            f_list.write(f"Вариант {var_num}\n\n")
            for i, item in enumerate(selected, 1):
                f_list.write(f"{i}. {item['name']}\n")
                if item['type'] == 'formula':
                    f_list.write(f"   Ответ: ${item['content']}$\n\n")
                else:
                    f_list.write(f"   Ответ: {item['content']}\n\n")

        # Подготовка слайдов
        slides = []
        for i, item in enumerate(selected, 1):
            slides.append({
                'number': i,
                'name': item['name'],
                'duration': item['duration']
            })

        instructions = "Перед диктантом запишите:\n-дату\n -ФИО\n -факультет\n -курс и группу\n -номер варианта\n\n"
        with open('templates/presentation.html', 'r', encoding='utf-8') as f_html:
            template = Template(f_html.read())
            html = template.render(
            slides=slides,
            variant_number=var_num,
            instructions=instructions
        )

        html_file = f"{args.output_prefix}_variant_{var_num}.html"
        with open(html_file, 'w', encoding='utf-8') as f_html:
            f_html.write(html)

        print(f"✅ Вариант {var_num}: {html_file}, {quiz_file}")

if __name__ == "__main__":
    main()