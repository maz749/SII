#!/usr/bin/env python3
"""Перенос конечных фактов lab1 в OWL/RDF-XML и 7 правил в SWRL.
Парсер предназначен только для формата нашей БЗ, не для произвольного Prolog.
"""
from pathlib import Path
import re
import types
from owlready2 import World, Thing, ObjectProperty, FunctionalProperty, AllDisjoint, AllDifferent, Imp, DataProperty

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://example.org/rpg-labs#'
CLASS_MAP = dict(character='Character', melee='Melee', ranged='Ranged', damage='Damage',
                 tank='Tank', support='Support', beginner='Beginner', weapon='Weapon', enemy='Enemy')
RULES = {
    'frontliner': ('Frontliner', 'Melee(?x), Tank(?x) -> Frontliner(?x)'),
    'protector': ('Protector', 'Frontliner(?x), Support(?x) -> Protector(?x)'),
    'ranged_damage': ('RangedDamage', 'Ranged(?x), Damage(?x) -> RangedDamage(?x)'),
    'beginner_choice': ('BeginnerChoice', 'Character(?x), Beginner(?x) -> BeginnerChoice(?x)'),
    'armored_hunter': ('ArmoredHunter', 'Damage(?x), hasWeapon(?x, ?w), counters(?w, armored) -> ArmoredHunter(?x)'),
    'ranged_support': ('RangedSupport', 'Ranged(?x), Support(?x) -> RangedSupport(?x)'),
    'versatile': ('Versatile', 'Damage(?x), Support(?x) -> Versatile(?x)'),
}

def read_facts():
    facts = []
    for line in (ROOT/'lab1/knowledge_base.pl').read_text().splitlines():
        s = line.split('%',1)[0].strip()
        if not s or ':-' in s:
            continue
        m = re.fullmatch(r'([a-z_]+)\(([a-z_]+)(?:,\s*([a-z_]+))?\)\.', s)
        if not m:
            raise ValueError(f'Неизвестный формат факта: {s}')
        facts.append((m[1], [v for v in m.groups()[1:] if v is not None]))
    return facts

def build():
    world=World()
    onto=world.get_ontology(BASE)
    facts=read_facts()
    with onto:
        classes={name:types.new_class(name,(Thing,)) for name in ['Character','Weapon','Enemy']}
        for name in list(CLASS_MAP.values())+list(c for c,_ in RULES.values()):
            if name not in classes:
                classes[name]=types.new_class(name,(classes['Character'],))
        # Предметные категории разделены, роли Damage/Tank/Support совместимы.
        AllDisjoint([classes[n] for n in ['Character','Weapon','Enemy']])
        AllDisjoint([classes['Melee'],classes['Ranged']])
        class hasWeapon(ObjectProperty, FunctionalProperty):
            domain=[classes['Character']]
            range=[classes['Weapon']]
        class counters(ObjectProperty):
            domain=[classes['Weapon']]
            range=[classes['Enemy']]
        class beginnerFriendly(DataProperty, FunctionalProperty):
            domain=[classes['Character']]
            range=[bool]
        # Ключевые отношения: ровно одно оружие и хотя бы один тип противника.
        classes['Character'].is_a.append(hasWeapon.exactly(1, classes['Weapon']))
        classes['Weapon'].is_a.append(counters.min(1, classes['Enemy']))
        individuals={}
        for pred,args in facts:
            if len(args)==1:
                cls=classes[CLASS_MAP[pred]]
                name=args[0]
                if name not in individuals:
                    individuals[name]=cls(name)
                elif cls not in individuals[name].is_a:
                    individuals[name].is_a.append(cls)
        for pred,args in facts:
            if len(args)==2:
                a,b=map(individuals.get,args)
                if pred=='has_weapon': a.hasWeapon=b
                elif pred=='counters': a.counters.append(b)
                else: raise ValueError(pred)
        # Тот же beginner/1 отображается в класс и положительный литерал.
        # Отсутствующие факты не превращаем в False (открытый мир).
        for pred,args in facts:
            if pred=='beginner': individuals[args[0]].beginnerFriendly=True
        AllDifferent(list(individuals.values()))
        for i,(pred,(name,text)) in enumerate(RULES.items(),1):
            rule=Imp(f'R{i}_{pred}')
            rule.set_as_rule(text)
            rule.comment=[f'Эквивалент правила Prolog {pred}/1.']
        onto.comment=['Учебная модель вымышленной фэнтезийной RPG. Исходник фактов: lab1/knowledge_base.pl.']
    path=ROOT/'lab2/rpg.owl'
    onto.save(file=str(path),format='rdfxml')
    print(f'OWL: {path.name}; unary={sum(len(a)==1 for _,a in facts)}; binary={sum(len(a)==2 for _,a in facts)}; SWRL={len(RULES)}')
    return path

if __name__=='__main__': build()
