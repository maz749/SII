#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'lab1' / 'knowledge_base.pl'
# Только словарь интерфейса; характеристики и рекомендации здесь не хранятся.
NAMES = dict(warrior='Воин', paladin='Паладин', guardian='Страж', ranger='Следопыт',
             assassin='Ассасин', mage='Маг', cleric='Жрец', druid='Друид',
             bard='Бард', necromancer='Некромант')
WEAPONS = dict(sword='меч', bow='лук', staff='посох', dagger='кинжал', mace='булава')
ROLES = {'урон': 'damage', 'защита': 'tank', 'поддержка': 'support'}
RANGES = {'ближняя': 'melee', 'дальняя': 'ranged', 'любая': 'any'}
EXPERIENCE = {'новичок': 'beginner', 'опытный': 'any'}
ENEMIES = {'любой': 'any', 'зверь': 'beast', 'летающий': 'flying',
           'бронированный': 'armored', 'маг': 'caster', 'нежить': 'undead'}
TAGS = {'frontliner': 'держит первую линию', 'protector': 'защищает и поддерживает',
        'ranged_damage': 'наносит урон издалека', 'beginner_choice': 'подходит новичку',
        'armored_hunter': 'эффективен против бронированных',
        'ranged_support': 'поддерживает издалека', 'versatile': 'совмещает урон и поддержку'}

def normalize(value: str) -> str:
    return ' '.join(value.strip().lower().replace('ё', 'е').split())

def parse_choice(value: str, choices: dict[str, str]) -> str:
    try:
        return choices[normalize(value)]
    except KeyError:
        raise ValueError('Допустимые ответы: ' + ', '.join(choices)) from None

def build_query(role: str, distance: str, experience: str, enemy: str) -> str:
    for value, allowed in ((role, ROLES.values()), (distance, RANGES.values()),
                           (experience, EXPERIENCE.values()), (enemy, ENEMIES.values())):
        if value not in allowed:
            raise ValueError(f'Недопустимое значение параметра: {value!r}')
    goals = ['character(X)', f'{role}(X)']
    if distance != 'any':
        goals.append(f'{distance}(X)')
    if experience == 'beginner':
        goals.append('beginner_choice(X)')
    goals.append('has_weapon(X,W)')
    if enemy != 'any':
        goals.append(f'counters(W,{enemy})')
    return ','.join(goals)

def recommend(role: str, distance: str, experience: str, enemy: str) -> tuple[str, list[dict]]:
    query = build_query(role, distance, experience, enemy)
    swipl = shutil.which('swipl')
    if not swipl:
        raise RuntimeError('Не найден swipl. Установите SWI-Prolog и добавьте его в PATH.')
    if not KB.is_file():
        raise RuntimeError(f'Не найдена база знаний: {KB}')
    tags = ','.join(TAGS)
    goal = (f'findall(_{{id:X,weapon:W,tags:Ts}},(({query}),'
            f'findall(T,(member(T,[{tags}]),call(T,X)),Ts)),Rows),'
            'sort(Rows,Unique),json_write_dict(current_output,Unique),nl')
    try:
        result = subprocess.run([swipl, '-q', '-s', str(KB), '-g',
                                 f'use_module(library(http/json)),({goal})', '-t', 'halt'],
                                capture_output=True, text=True, timeout=15, check=True)
        return query, json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise RuntimeError(f'Ошибка обращения к Prolog: {exc}') from exc

def ask(prompt: str, choices: dict[str, str]) -> str:
    while True:
        raw = input(f'{prompt} ({" / ".join(choices)}): ')
        if normalize(raw) in {'выход', 'exit'}:
            raise EOFError
        try:
            return parse_choice(raw, choices)
        except ValueError as exc:
            print(f'Не удалось распознать ответ. {exc}')

def parse_profile(value: str) -> dict[str, str]:
    fields = {'роль': ROLES, 'дистанция': RANGES, 'опыт': EXPERIENCE, 'противник': ENEMIES}
    result = {}
    for part in value.split(';'):
        if part.count('=') != 1:
            raise ValueError('Формат: роль=урон; дистанция=дальняя; опыт=новичок; противник=любой')
        key, raw = map(normalize, part.split('=', 1))
        if key not in fields or key in result:
            raise ValueError('Неизвестное или повторяющееся поле: ' + key)
        result[key] = parse_choice(raw, fields[key])
    if not {'роль', 'дистанция'} <= result.keys():
        raise ValueError('Поля «роль» и «дистанция» обязательны.')
    return result


def fixed_dialog() -> tuple[str, str, str, str]:
    print('Формат: роль=урон; дистанция=дальняя; опыт=новичок; противник=любой')
    print('Опыт и противника можно пропустить: система задаст до двух уточнений.')
    while True:
        raw = input('Ваш запрос: ')
        if normalize(raw) in {'выход', 'exit'}:
            raise EOFError
        try:
            profile = parse_profile(raw)
            break
        except ValueError as exc:
            print(f'Не удалось распознать ответ. {exc}')
    complete = 'опыт' in profile and 'противник' in profile
    if 'опыт' not in profile:
        profile['опыт'] = ask('Ваш опыт', EXPERIENCE)
    if 'противник' not in profile:
        profile['противник'] = ask('Основной противник', ENEMIES)
    if complete and ask('Показать рекомендации', {'да': 'yes', 'нет': 'no'}) == 'no':
        raise EOFError
    return profile['роль'], profile['дистанция'], profile['опыт'], profile['противник']


def main(fixed: bool = False) -> int:
    print('Подбор персонажа фэнтезийной RPG. Для завершения введите «выход».')
    print('Все выбранные ограничения обязательны.')
    try:
        if fixed:
            role, distance, experience, enemy = fixed_dialog()
        else:
            role = ask('Ваша роль', ROLES)
            distance = ask('Дистанция боя', RANGES)
            experience = ask('Ваш опыт', EXPERIENCE)
            enemy = ask('Основной противник', ENEMIES)
        query, rows = recommend(role, distance, experience, enemy)
    except (EOFError, KeyboardInterrupt):
        print('\nДиалог завершен.')
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f'\nЗапрос к БЗ: {query}.')
    if not rows:
        print('В базе нет персонажа, который соответствует всем условиям.')
        print('Повторите диалог, выбрав «любая» дистанция или «любой» противник.')
        return 0
    print(f'Найдено персонажей: {len(rows)}. Все удовлетворяют вашим ограничениям; рейтинг не задан.')
    for row in rows:
        print(f'\n{NAMES.get(row["id"], row["id"])} - оружие: {WEAPONS.get(row["weapon"], row["weapon"])}.')
        print('Обоснование: выбранная роль и все ограничения подтверждены фактами БЗ.')
        print('Выведенные свойства: ' + '; '.join(TAGS[t] for t in row['tags']) + '.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main(fixed='--fixed' in sys.argv[1:]))
