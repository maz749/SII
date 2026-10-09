#!/usr/bin/env python3
"""Собирает 3 кратких и общий расширенный отчет из проверенных результатов."""
from pathlib import Path
import json
import re
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf'
OUT.mkdir(parents=True,exist_ok=True)
RESULT=json.loads((ROOT/'evidence/ontology_results.json').read_text())
assert RESULT['consistent'] and all(r['equal'] for r in RESULT['rules'].values())
FONT=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf'),('Code','Courier New.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
ST=getSampleStyleSheet()
ST.add(ParagraphStyle(name='TextRU',fontName='Body',fontSize=10.7,leading=15.3,spaceAfter=7))
ST.add(ParagraphStyle(name='HeadingRU',fontName='Bold',fontSize=15,leading=19,textColor=colors.HexColor('#000000'),spaceAfter=12))
ST.add(ParagraphStyle(name='SubRU',fontName='Bold',fontSize=11.5,leading=15,spaceBefore=7,spaceAfter=8,textColor=colors.HexColor('#000000')))
ST.add(ParagraphStyle(name='TitleRU',fontName='Bold',fontSize=23,leading=28,textColor=colors.HexColor('#000000'),spaceAfter=16))
ST.add(ParagraphStyle(name='SmallRU',fontName='Body',fontSize=8.5,leading=11.5,spaceAfter=5))
ST.add(ParagraphStyle(name='CodeRU',fontName='Code',fontSize=8.5,leading=11.5,spaceBefore=5,spaceAfter=9,backColor=colors.HexColor('#f2f2f2'),borderPadding=8))

def P(s,style='TextRU'):
    return Paragraph(escape(str(s)).replace('\n','<br/>'),ST[style])
def p(s): return ('p',s)
def h(s): return ('h',s)
def code(s): return ('code',s)
def table(headers,rows,widths=None): return ('table',headers,rows,widths)
def diagram(): return ('diagram',)
def page(title,*items): return (title,list(items))

ROLE={'damage':'урон','tank':'защита','support':'поддержка'}
NAME={'warrior':'Воин','paladin':'Паладин','guardian':'Страж','ranger':'Следопыт','assassin':'Ассасин','mage':'Маг','cleric':'Жрец','druid':'Друид','bard':'Бард','necromancer':'Некромант'}
KB=(ROOT/'lab1/knowledge_base.pl').read_text()
facts=[]
for line in KB.splitlines():
    m=re.fullmatch(r'(\w+)\((\w+)(?:,\s*(\w+))?\)\.',line)
    if m:facts.append((m[1],m[2],m[3]))
def has(pred,x):return (pred,x,None) in facts
def weapon(x):return next(b for pred,a,b in facts if pred=='has_weapon' and a==x)
characters=[a for pred,a,b in facts if pred=='character']
CATALOG=[[x,', '.join(v for k,v in ROLE.items() if has(k,x)), 'ближняя' if has('melee',x) else 'дальняя','да' if has('beginner',x) else 'нет факта',weapon(x)] for x in characters]
RULE_ROWS=[[f'R{i} {pred}',', '.join(r['prolog'])] for i,(pred,r) in enumerate(RESULT['rules'].items(),1)]
RULE_CODE='\n'.join(line for line in KB.splitlines() if ':-' in line)
SWRL=[
'Melee(?x), Tank(?x) -> Frontliner(?x)',
'Frontliner(?x), Support(?x) -> Protector(?x)',
'Ranged(?x), Damage(?x) -> RangedDamage(?x)',
'Character(?x), Beginner(?x) -> BeginnerChoice(?x)',
'Damage(?x), hasWeapon(?x, ?w),\n  counters(?w, armored) -> ArmoredHunter(?x)',
'Ranged(?x), Support(?x) -> RangedSupport(?x)',
'Damage(?x), Support(?x) -> Versatile(?x)']
Q_ROWS=[
['has_weapon(X, staff).','druid, mage, necromancer'],
['tank(X), support(X).','paladin'],
['(tank(X); support(X)).','bard, cleric, druid, guardian, paladin, warrior'],
['character(X), \\+ beginner(X).','assassin, druid, mage, necromancer'],
['protector(X).','paladin'],
['armored_hunter(X).','druid, mage, necromancer'],
['ranged_damage(X), beginner_choice(X).','ranger'],
['ranged_support(X), has_weapon(X,W).','bard-bow, druid-staff'],
['tank(X), ranged(X).','нет решений']]
SCENARIOS=[
['урон / дальняя / новичок / любой','ranger'],
['поддержка / дальняя / опытный / любой','bard, druid'],
['урон / дальняя / опытный / бронированный','druid, mage, necromancer'],
['поддержка / любая / новичок / нежить','cleric'],
['защита / дальняя / новичок / любой','пустой результат']]
SOURCES=[
'1. Бессмертный И.А. и др. Системы искусственного интеллекта. ИТМО, 2024. Предоставленный файл 3308.pdf: печатные стр. 56-58 (задания), 73 (структура отчета).',
'2. SWI-Prolog. PL-Unit, запуск тестов: https://www.swi-prolog.org/pldoc/package/plunit',
'3. Owlready2. SWRL rules: https://owlready2.readthedocs.io/en/latest/rule.html',
'4. Protégé. DLQueryTab: https://protegewiki.stanford.edu/wiki/DLQueryTab']
LIMIT=p('Онтология создана программно и проверена reasoner Pellet. GUI Protégé в этой среде не запускался: установка через Homebrew заблокирована проверкой Gatekeeper. Файл OWL и сценарий проверки в редакторе подготовлены; скриншотов Protégé в отчете нет.')
META=p('Дисциплина: «Системы искусственного интеллекта»\nМодуль 1. Базы знаний и онтологии\nТема: подбор персонажа вымышленной фэнтезийной RPG\nСтудент: Бирюков Ян    Группа: 3321\nДата подготовки: 7 октября 2026 г.')

# Содержание всех отчетов соответствует присланному шаблону модуля 1.
ANNOTATION=(
'В работе разработана система поддержки принятия решений для выбора персонажа вымышленной фэнтезийной RPG. '
'Предметная область представлена базой знаний Prolog, содержащей 50 унарных фактов, 15 бинарных фактов и семь правил. '
'Факты и правила перенесены в онтологию OWL/SWRL с иерархией классов, типизированными свойствами и ограничениями. '
'Онтология проверена средствами HermiT и Pellet, а результаты вывода сопоставлены с ответами Prolog. '
'Консольная DSS принимает строку фиксированного формата, уточняет недостающие данные и объясняет рекомендации. '
'Работоспособность подтверждена автоматическими тестами, компетентностными запросами и пятью сценариями использования.'
)

def cover(kind):
    return page('',('cover',kind))

INTRO=[
 p('Цель модуля - освоить логическое моделирование, построение онтологий, проверяемый вывод и применение знаний в системе поддержки принятия решений (DSS). Последовательность работы: БЗ Prolog → онтология OWL/SWRL → диалоговое приложение.'),
 p('Базы знаний отделяют сведения о предметной области от интерфейса. Это позволяет повторно использовать факты, проверять вывод и объяснять рекомендации. Онтология дополнительно задает общую терминологию, иерархию и ограничения согласованности данных.'),
 p('Выбран домен игровых персонажей. Пользователь задает роль, дистанцию боя, опыт и тип противника; система возвращает все подходящие архетипы. Игровые характеристики являются авторскими допущениями учебной модели и не описывают баланс коммерческой игры.'),
]
TRACE=[
 ['character(paladin).','paladin rdf:type Character','Индивид и его класс'],
 ['melee(paladin).','paladin rdf:type Melee','Melee subClassOf Character'],
 ['beginner(paladin).','Beginner; beginnerFriendly true','Класс + литерал xsd:boolean'],
 ['has_weapon(paladin,sword).','paladin hasWeapon sword','Character → Weapon'],
 ['counters(sword,beast).','sword counters beast','Weapon → Enemy'],
 ['protector(X) :- ...','Protector и правило R2','Результат выводится reasoner']
]
SPARQL_ROWS=[
 ['C1','Какие персонажи доступны?','Все 10 персонажей'],
 ['C2','Кто наносит урон на расстоянии?','druid, mage, necromancer, ranger'],
 ['C3','Кто защищает и поддерживает?','paladin'],
 ['C4','Кто атакует бронированных?','druid, mage, necromancer'],
 ['C5','Кто подойдет новичку для дальней атаки?','ranger'],
 ['C6','У кого beginnerFriendly = true?','bard, cleric, guardian, paladin, ranger, warrior']
]
SPARQL_CODE='''PREFIX rpg: <https://example.org/rpg-labs#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# Перед каждым запросом используются эти префиксы.
# C1
SELECT DISTINCT ?x WHERE {
  ?x a/rdfs:subClassOf* rpg:Character
} ORDER BY ?x
# C2
SELECT ?x WHERE { ?x a rpg:RangedDamage } ORDER BY ?x
# C3
SELECT ?x WHERE { ?x a rpg:Protector } ORDER BY ?x
# C4
SELECT ?x WHERE {
  ?x a rpg:Damage; rpg:hasWeapon ?w.
  ?w rpg:counters rpg:armored
} ORDER BY ?x
# C5
SELECT ?x WHERE {
  ?x a rpg:RangedDamage, rpg:BeginnerChoice
} ORDER BY ?x
# C6
SELECT ?x WHERE { ?x rpg:beginnerFriendly true } ORDER BY ?x'''
PROLOG_LISTING='''Q1: character(X).
[assassin,bard,cleric,druid,guardian,mage,
 necromancer,paladin,ranger,warrior]
Q2: has_weapon(X, staff).
[druid,mage,necromancer]
Q3: tank(X), support(X).
[paladin]
Q4: (tank(X); support(X)).
[bard,cleric,druid,guardian,paladin,warrior]
Q5: character(X), \\+ beginner(X).
[assassin,druid,mage,necromancer]
Q6: protector(X).
[paladin]
Q7: armored_hunter(X).
[druid,mage,necromancer]
Q8: ranged_damage(X), beginner_choice(X).
[ranger]
Q9: ranged_support(X), has_weapon(X,W).
[bard-bow,druid-staff]
Q10: tank(X), ranged(X).
[]'''
# Ответы листинга сверены с evidence/prolog_queries.txt; порядок меняет sort/2.
SCENARIO_DATA=json.loads((ROOT/'evidence/dss_scenarios.json').read_text())
EXPLANATIONS=[
 'Следопыт удовлетворяет damage, ranged и beginner_choice; его оружие - лук. Остальные дальние атакующие в БЗ не имеют подтверждения пригодности новичку.',
 'Бард и друид обладают support и ranged. Опытный игрок не ограничивает выбор предикатом beginner_choice. У барда лук, у друида посох.',
 'Друид, маг и некромант наносят урон издалека, имеют посох; counters(staff,armored) подтверждает эффективность против выбранного противника.',
 'Жрец имеет роль поддержки и beginner_choice. Его булава удовлетворяет counters(mace,undead). Дистанция не ограничена.',
 'Все защитники в каталоге относятся к ближнему бою, поэтому совместный запрос tank и ranged не имеет решений. Система сообщает об отсутствии совпадений и предлагает при повторном запуске выбрать любую дистанцию; самовольно запрос не ослабляет.'
]
def scenario(i):
    row=SCENARIO_DATA[i]
    ids=', '.join(r['id'] for r in row['rows']) or 'нет решений'
    return [h(f'6.{i+2}. Сценарий {i+1}'),p('Вход: '+row['profile']+'. Уточнения: '+row['experience']+'; '+row['enemy']+'.'),
            code(row['query']+'.'),p('Фактическая рекомендация: '+ids+'. '+EXPLANATIONS[i])]

prolog_pages=[
 page('4. База знаний в Prolog\nЛР1, часть 1: дизайн и реализация',
 h('4.1. Сущности и отношения'),
 p('Каталог содержит десять архетипов. Роли «урон», «защита», «поддержка» совместимы. Дистанция в этой модели одна: ближняя либо дальняя. beginner/1 означает подтвержденную пригодность новичку; отсутствие факта не доказывает объективную сложность.'),
 table(['Персонаж','Роли','Дистанция','Новичок','Оружие'],CATALOG,[90,150,75,80,90]),
 p('Русские названия: warrior - воин; paladin - паладин; guardian - страж; ranger - следопыт; assassin - ассасин; mage - маг; cleric - жрец; druid - друид; bard - бард; necromancer - некромант.'),
 table(['Предикат','Назначение'],[['character/1','Множество доступных персонажей'],['melee/1, ranged/1','Дистанция боя'],['damage/1, tank/1, support/1','Игровая роль'],['beginner/1','Пригодность новичку'],['weapon/1, enemy/1','Словари оружия и противников'],['has_weapon/2','Основное оружие персонажа'],['counters/2','Эффективность оружия против противника']],[210,275]),
 p('Связи оружия: sword → beast; bow → flying; staff → armored; dagger → caster; mace → undead. Это правила выбранной учебной игры.')),
 page('4. База знаний в Prolog\nСтруктура и правила',
 h('4.2. Требования и организация файлов'),
 table(['Элемент','Требуется','Выполнено'],[['Унарные факты','не менее 20','50'],['Бинарные факты','10-15','15'],['Правила','5-7','7'],['Примеры запросов','6-10','10']],[195,145,145]),
 p('knowledge_base.pl разделен комментариями на сущности, признаки, словари, отношения и правила. Запросы вынесены в queries.pl, тесты - в tests/knowledge_base_tests.pl. Разделение позволяет запускать примеры и тесты независимо от приложения.'),
 p('Состав унарных фактов: character - 10; melee и ranged - по 5; damage - 7; tank - 3; support - 4; beginner - 6; weapon и enemy - по 5. Бинарные факты: 10 has_weapon и 5 counters.'),
 h('4.3. Полный набор правил'),code(RULE_CODE),
 h('4.4. Композиция и отрицание'),
 p('Для protector(paladin) сначала доказывается frontliner(paladin): нужны melee(paladin) и tank(paladin). Затем проверяется support(paladin). Все три факта есть, поэтому паладин попадает в результат. Это композиция правил R1 и R2.'),
 p('Конъюнкция задается запятой, дизъюнкция - точкой с запятой. Отрицание как неуспех \\+ используется в запросе после character(X), когда X уже связан. Положительные правила переносятся в SWRL; отрицание не подменяет отсутствие знания логическим отрицанием в OWL.')),
 page('4. База знаний в Prolog\nЗапросы и фактические ответы',
 p('Ниже приведены десять запросов и ответы SWI-Prolog. Скрипт собирает ответы findall/3 и устраняет повторы sort/2. Поэтому Q4 содержит паладина один раз, хотя он удовлетворяет обеим ветвям.'),
 code(PROLOG_LISTING),
 p('Q1-Q2 обращаются к фактам и отношениям; Q3-Q5 демонстрируют И, ИЛИ и НЕ; Q6-Q8 требуют логического вывода; Q9 связывает две переменные; Q10 демонстрирует отсутствие решения. Порядок строк - от прямого поиска к составным условиям и правилам.'),
 code('swipl -q -s lab1/queries.pl -g main -t halt'),
 p('Источник фактических ответов: evidence/prolog_queries.txt. БЗ проверена 14 тестами PL-Unit. У каждого персонажа ровно одно основное оружие и одна дистанция; все связи ведут к объявленным объектам.'))]

ontology_pages=[
 page('5. Онтология в Protégé\nЛР1, часть 2: моделирование',
 p('Исходные факты переведены в OWL/RDF-XML. Созданы 16 классов, 20 предметных индивидов, два ObjectProperty, один DataProperty и семь правил SWRL. Иерархия имеет три уровня с учетом owl:Thing: Thing → Character → конкретный признак или выводной класс.'),
 diagram(),
 h('5.1. Мини-матрица трассируемости'),
 table(['Prolog','OWL-элемент','Комментарий'],TRACE,[170,175,140]),
 p('beginnerFriendly - дополнительное представление того же факта beginner/1 литералом true типа xsd:boolean. Оно не вводит новые сведения о персонаже. Для остальных четырех персонажей значение не задано; false из отсутствия факта не выводится.'),
 p('OWL создается скриптом lab2/build_ontology.py; факты читаются из БЗ, а перевод семи правил описан явно. Исходный rpg.owl не содержит заранее присвоенных выводных классов.')),
 page('5. Онтология в Protégé\nСвойства, ограничения и SWRL',
 table(['Свойство','Домен / диапазон','Ограничение'],[['hasWeapon','Character / Weapon','Functional; exactly 1'],['counters','Weapon / Enemy','Для Weapon: min 1'],['beginnerFriendly','Character / xsd:boolean','Functional; значение true у 6 индивидов']],[120,190,175]),
 code('Character SubClassOf hasWeapon exactly 1 Weapon\nWeapon SubClassOf counters min 1 Enemy'),
 p('Character, Weapon и Enemy попарно disjoint; Melee и Ranged также disjoint. Роли Damage, Tank и Support совместимы. Все 20 предметных индивидов объявлены различными (AllDifferent), чтобы два разных оружия нельзя было неявно отождествить при проверке cardinality.'),
 p('В открытом мире отсутствие явно записанной связи не всегда вызывает ошибку: reasoner может допускать неизвестное значение. Поэтому фактическое наличие одного оружия отдельно проверяется тестами Prolog. Ограничения OWL проверяют логическую согласованность.'),
 h('5.2. Семь правил SWRL'),
 code('\n\n'.join(f'R{i}: {s}' for i,s in enumerate(SWRL,1))),
 p('Правила R1-R7 соответствуют семи правилам Prolog. SWRL-импликация задает достаточное условие принадлежности классу; она не является объявлением эквивалентности класса.')),
 page('5. Онтология в Protégé\nКомпетентностные запросы и проверки',
 table(['№','Компетентностный вопрос','Ожидаемый и полученный ответ'],SPARQL_ROWS,[25,240,220]),
 code(SPARQL_CODE),
 p('Шесть запросов выполнены через RDFLib над rpg_inferred.owl; все ответы совпали с ожидаемыми. HermiT и Pellet независимо запущены на исходном rpg.owl: онтология согласована, все семь наборов выводных типов совпали с Prolog.'),
 p('Файл подходит для открытия в Protégé; сценарий GUI-проверки приведен в lab2/PROTEGE.md. HermiT запускался программно, а сам GUI Protégé не проверен из-за блокировки установки Gatekeeper. Скриншоты редактора не заявляются.'))]

pipeline='''ПРОЧИТАТЬ строку ключ=значение; ключ=значение
РАЗОБРАТЬ поля; проверить ключи, значения и дубликаты
НОРМАЛИЗОВАТЬ регистр, пробелы и «ё»
ЕСЛИ нет опыта или противника: задать 1-2 уточнения
ЕСЛИ все поля есть: подтвердить выдачу рекомендации
СФОРМИРОВАТЬ конъюнкцию предикатов Prolog
ВЫПОЛНИТЬ запрос в SWI-Prolog, получить JSON
УДАЛИТЬ дубликаты; сохранить всех допустимых кандидатов
ВЫВЕСТИ персонажей, оружие и доказанные свойства'''
dss_pages=[
 page('6. DSS на базе знаний\nЛР2: архитектура и реализация',
 h('6.1. Формат ввода и конвейер'),
 code('роль=урон; дистанция=дальняя\n\nУточнение 1: Ваш опыт? новичок\nУточнение 2: Основной противник? любой'),
 p('Роль и дистанция обязательны. Поля опыт и противник можно сразу включить в строку или сообщить в ходе диалога. Если отсутствует одно поле, задается один вопрос; если оба - два. Для полной строки запрашивается подтверждение выдачи результата. Рекомендация не выдается до завершения диалога.'),
 table(['Поле','Допустимые значения'],[['роль','урон / защита / поддержка'],['дистанция','ближняя / дальняя / любая'],['опыт','новичок / опытный'],['противник','любой / зверь / летающий / бронированный / маг / нежить']],[110,375]),
 code(pipeline),
 p('Система выполняет точный отбор по обязательным условиям. Агрегация - findall/3 и sort/2: повторы удаляются, возвращаются все совпадения без оценочного ранжирования. Сортировка имеет технический смысл и не означает, что первый персонаж лучше.'),
 p('Python управляет диалогом и отображает ответ. Предметные признаки и выводы запрашиваются у Prolog. Подпроцесс запускается без shell; значения проходят белые списки. JSON содержит идентификатор, оружие и свойства, доказанные семью правилами.'),
 code('python3 lab3/app.py --fixed'),
 p('Также сохранен простой режим с четырьмя отдельными вопросами: python3 lab3/app.py.')),
 page('6. DSS на базе знаний\nСценарии 1-3',*scenario(0),*scenario(1),*scenario(2),
 p('Данные примеров получены реальными вызовами recommend и диалогового режима --fixed. Машиночитаемая запись: evidence/dss_scenarios.json; полные журналы: evidence/dialog_beginner.txt, dialog_support.txt, dialog_armor.txt.')),
 page('6. DSS на базе знаний\nСценарии 4-5 и нештатные ситуации',*scenario(3),*scenario(4),
 h('6.7. Ошибки входа и конфликт признаков'),
 table(['Ситуация','Поведение'],[['Неизвестная роль: роль=маг','Ошибка словаря; ввод строки повторяется'],['Нет обязательной дистанции','Сообщение об обязательных полях'],['Поле задано дважды','Отклонение неоднозначной строки'],['tank + ranged','Корректный пустой результат в этой модели'],['Пустая строка / лишний разделитель','Сообщение о фиксированном формате'],['выход / конец stdin','Корректное завершение диалога'],['swipl отсутствует / процесс не ответил','Понятная ошибка; тайм-аут 15 секунд']],[230,255]),
 p('Конфликтом здесь считается сочетание пожеланий, для которого в текущем каталоге нет кандидата. Оно не превращается в ложный факт или произвольную рекомендацию. Значение «опытный» снимает ограничение beginner_choice, а не запрещает персонажей для новичка.'),
 p('Предметные знания не дублируются в Python. Изменение фактов Prolog влияет на рекомендации без переписывания правил интерфейса.'))]

TEST_PROLOG=[
 ['character(X)','10 уникальных персонажей','пройден'],
 ['frontliner(X)','guardian, paladin, warrior','пройден'],
 ['protector(X)','paladin','пройден'],
 ['ranged_damage(X)','druid, mage, necromancer, ranger','пройден'],
 ['beginner_choice(X)','bard, cleric, guardian, paladin, ranger, warrior','пройден'],
 ['armored_hunter(X)','druid, mage, necromancer','пройден'],
 ['ranged_support(X)','bard, druid','пройден'],
 ['versatile(X)','druid, paladin','пройден'],
 ['tank(X), ranged(X)','пустой список','пройден'],
 ['character(X), \\+ beginner(X)','assassin, druid, mage, necromancer','пройден'],
 ['Структурные проверки (4)','Одно оружие; валидные связи; одна дистанция','пройдены']]
TEST_DSS=[
 ['Пять предметных сценариев','Ответы совпали с разделом 6'],
 ['Нормализация и полное совпадение','Пробелы/регистр обработаны; свободная фраза отклонена'],
 ['Неверные параметры и фрагменты Prolog','Исключены белыми списками'],
 ['Повтор вопроса и отложенный результат','Результат только после допустимых ответов'],
 ['Выход и отсутствующий swipl','Корректное завершение / сообщение'],
 ['Фиксированный формат','Парсинг, ошибки, 1 и 2 уточнения, подтверждение, повтор строки']]
testing_pages=[
 page('7. Тестирование и отладка\nПроверки Prolog и онтологии',
 table(['Тест / группа','Ожидаемый ответ','Результат'],TEST_PROLOG,[170,260,55]),
 p('Выполнено 14 тестов PL-Unit; все пройдены. Ожидаемые множества заданы в тестах, фактические вычисляет интерпретатор. Проверки отношений дополнительно исключают ссылки на несуществующие оружие и противника.'),
 table(['Проверка OWL','Ожидание и результат'],[['Перенос фактов','Все 50 унарных и 15 бинарных фактов найдены'],['Состав правил','Ровно 7 правил, выводных типов до reasoner нет'],['HermiT и Pellet','Оба подтверждают согласованность исходной модели'],['Выводные типы','Все 7 наборов равны ответам Prolog'],['DataProperty','6 литералов true, соответствует beginner/1'],['C1-C6 (SPARQL)','Все 6 ожидаемых ответов подтверждены']],[185,300]),
 p('Для проверки reasoner используется исходный OWL, а не файл с готовыми выводами. В отдельный rpg_inferred.owl сохраняются результаты Pellet; SPARQL работает с этим снимком и не выполняет SWRL самостоятельно.')),
 page('7. Тестирование и отладка\nDSS и отрицательные проверки',
 table(['Группа тестов DSS','Полученный результат'],TEST_DSS,[205,280]),
 p('Выполнено 18 тестов Python unittest. Положительные тесты обращаются к реальному SWI-Prolog; модульные проверки дополнительно покрывают обработку строк и управление диалогом. Сценарий с ошибочной первой строкой завершается корректной рекомендацией после повторного ввода.'),
 h('7.1. Проверка нарушений ограничений OWL'),
 table(['Изменение в копии модели','Ожидаемое поведение HermiT','Факт'],[['warrior дополнительно типизирован Ranged','Нарушение disjoint Melee/Ranged','обнаружено'],['Воину добавлен второй, отличный вид оружия','Нарушение exactly 1 / Functional + AllDifferent','обнаружено'],['beginnerFriendly = "unknown"','Строка недопустима для xsd:boolean','обнаружено']],[185,235,65]),
 p('Каждый отрицательный тест выполняется на новой копии онтологии в памяти. Основной rpg.owl остается согласованным. Проверка ожидает исключение о противоречивости, а не аварийно завершившийся запуск Java.'),
 h('7.2. Воспроизведение проверок'),
 code('python tools/run_checks.py\npython tools/capture_examples.py'),
 p('Журналы находятся в evidence/: prolog_tests.txt, python_tests.txt, ontology_check.txt; структурированные результаты - ontology_results.json и dss_scenarios.json. При отладке закреплена версия Owlready2 0.48, совместимая с используемой Java 17.'))]
EVALUATION=[
 table(['Критерий','Prolog','OWL / Protégé'],[['Правила','Короткие исполняемые предложения','SWRL плюс типизация и ограничения'],['Отрицание','Неуспех доказательства \\+','Отсутствие факта обычно означает неизвестность'],['Расширение схемы','Новые предикаты и правила','Классы, свойства, наследование и ограничения'],['Использование в DSS','Прямой вызов цели','DL/SPARQL, для SWRL нужен reasoner'],['Проверяемость','Тесты запросов и целостности','Согласованность и выведенные типы']],[105,175,205]),
 p('Для небольшого рекомендателя проще непосредственно сформулировать запрос на Prolog. OWL удобнее для общей схемы знаний, повторного использования терминов и проверки ограничений. Семь положительных правил дают одинаковые результаты; это проверенная эквивалентность на данной БЗ, а не утверждение о полном равенстве языков.'),
 p('Отрицание как неуспех не переносится в OWL автоматически: отсутствие beginner(assassin) не доказывает отрицательный класс. Согласованность онтологии также не гарантирует, что все желаемые значения явно записаны; полноту каталога проверяют отдельно.'),
 p('Развитие: добавить классы заклинаний и экипировки, правила совместимости команды, ранжирование по мягким предпочтениям, уточнение причин пустого результата и хранилище версий БЗ. При подключении внешнего хранилища следует сохранять источники и версии фактов, чтобы объяснения оставались воспроизводимыми.'),
 p('Граница проверки: каталог небольшой, нагрузочные испытания не проводились. Программный HermiT-вывод проверен; работа интерфейса Protégé в этой среде не подтверждена.')]
CONCLUSION=[
 p('Реализован полный программный конвейер: БЗ Prolog, ее OWL/SWRL-представление и DSS с фиксированным форматом строки и уточняющими вопросами. Требования к числу фактов, отношений и правил выполнены. Система выводит всех персонажей, удовлетворяющих условиям, и объясняет выбор через доказанные свойства.'),
 p('Работоспособность подтверждают 14 тестов Prolog, 18 тестов Python, шесть компетентностных запросов и независимые проверки HermiT и Pellet. Ограничения модели: авторский каталог из десяти архетипов, отсутствие оценки боевого баланса и ранжирования. Для демонстрации непосредственно в Protégé нужно открыть подготовленную онтологию по приложенной инструкции.'),
 p('Подход полезен там, где правила должны быть прозрачными, знания - пригодными для повторного использования, а результат - проверяемым. Разделение модели и интерфейса позволяет расширять предметную область без переписывания диалога.')]

full=[cover('Отчёт по модулю 1'),
 page('2. Аннотация',p(ANNOTATION),h('3. Введение'),*INTRO,
 p('Нумерация соответствует присланному шаблону: Prolog и онтология - ЛР1, части 1 и 2; DSS - ЛР2. Каталоги lab1, lab2 и lab3 сохранены для совместимости с ранее подготовленными исходниками.'),
 p('Отчет содержит по три страницы на каждый практический раздел, две страницы тестирования, отдельные разделы оценки и заключения. Фактические журналы приложены в архиве.')),
 *prolog_pages,*ontology_pages,*dss_pages,*testing_pages,
 page('8. Оценка и интерпретация',*EVALUATION),
 page('9. Заключение',*CONCLUSION,h('Источники'),p('1. «Системы ИИ.pdf» - предоставленный шаблон отчета по модулю 1, 4 страницы.'),
 *[p(s.replace('1. Бессмертный','2. Бессмертный').replace('2. SWI','3. SWI').replace('3. Owlready2','4. Owlready2').replace('4. Protégé','5. Protégé')) for s in SOURCES])]

# Краткие отчеты используют общие заголовки шаблона, сохраняя нумерацию частей.
def brief(kind,ann,goal,practical,checks,conclusion):
    return [cover(kind),page('2. Аннотация',p(ann),h('3. Введение'),p(goal),h('Результат работы'),*practical),
            page('7. Тестирование и отладка',*checks,h('8. Оценка и интерпретация'),p(conclusion),h('9. Заключение'),p('Полученные результаты и исходники включены в общий комплект модуля. Подробные листинги, трассируемость и сценарии проверки приведены в расширенном отчете.'))]
short1=brief('ЛР1, часть 1\nБаза знаний в Prolog',
 'Разработана база знаний для подбора персонажа фэнтезийной RPG. В ней представлены десять архетипов, роли, дистанции боя, оружие и противники. Созданы 50 унарных фактов, 15 бинарных фактов и семь правил. Подготовлены десять запросов разной сложности. Результаты проверены средствами SWI-Prolog и PL-Unit.',
 'Цель - освоить факты, отношения, логические операции и композицию правил. БЗ используется в онтологии и рекомендательной программе, что обеспечивает повторное использование знаний.',
 [h('4. База знаний: дизайн и реализация'),table(['Объект','Реализация'],[['Факты','50 унарных; 15 бинарных'],['Правила','7; композиция R1 → R2'],['Логические операции','И в правилах; ИЛИ и НЕ в запросах'],['Файлы','knowledge_base.pl; queries.pl']],[175,310]),code(RULE_CODE),
 p('Запрос character(X), \\+ beginner(X) связывает X до отрицания. sort/2 устраняет дубли доказательств. Файлы разделены на комментированные группы.')],
 [table(['Запрос','Фактический ответ'],Q_ROWS,[258,227]),p('Все 14 тестов PL-Unit пройдены. Полный журнал: evidence/prolog_tests.txt; десять запросов и ответы: evidence/prolog_queries.txt.'),code('swipl -q -s lab1/queries.pl -g main -t halt')],
 'Prolog позволяет кратко выразить отбор и объяснить его цепочкой доказательства. Отрицание как неуспех действует относительно данной БЗ; каталог остается конечной учебной моделью.')
short2=brief('ЛР1, часть 2\nОнтология в Protégé',
 'База знаний переведена в OWL/SWRL для работы в Protégé. Созданы 16 классов и 20 предметных индивидов. Добавлены два объектных свойства, одно типизированное свойство данных и ограничения cardinality. Семь правил SWRL воспроизводят положительные правила Prolog. HermiT и Pellet подтвердили согласованность модели и совпадение выводов.',
 'Цель - освоить онтологическое моделирование, ограничения и логический вывод. Онтология делает схему данных явной и позволяет повторно использовать знания вне Prolog.',
 [h('5. Моделирование и трассируемость'),table(['Prolog','OWL','Комментарий'],TRACE,[170,175,140]),
 code('Character SubClassOf hasWeapon exactly 1 Weapon\nWeapon SubClassOf counters min 1 Enemy'),
 p('beginnerFriendly имеет domain Character, range xsd:boolean и значение true у шести новичковых персонажей. Character, Weapon, Enemy несовместимы; Melee и Ranged несовместимы; все предметные индивиды различны.')],
 [table(['№','Вопрос','Проверенный ответ'],SPARQL_ROWS,[25,240,220]),p('Проверены 65 исходных фактов, семь правил, шесть запросов и три отрицательных сценария нарушения ограничений. HermiT и Pellet независимо вывели одинаковые типы.'),
 p('Файл lab2/rpg.owl подготовлен для открытия в Protégé. Проверка GUI не выполнена: установка заблокирована Gatekeeper. Программный reasoner запускался на исходной онтологии, без готовых выводов.')],
 'OWL удобен для схемы, наследования и ограничений. Открытый мир отличается от отрицания Prolog: отсутствующий факт остается неизвестным. Для GUI-демонстрации подготовлена инструкция lab2/PROTEGE.md.')
short3=brief('ЛР2\nDSS на базе знаний',
 'Разработана консольная система выбора персонажа RPG. Программа принимает строку фиксированного формата. При нехватке данных она задает один или два уточняющих вопроса. Предпочтения превращаются в запрос к настоящему SWI-Prolog. Рекомендации сопровождаются оружием и свойствами, выведенными из БЗ. Корректность проверена пятью предметными сценариями и тестами ошибок ввода.',
 'Цель - использовать логические знания для принятия решения после диалога с пользователем. Python отвечает за ввод и отображение, а Prolog - за предметные факты и доказательство условий.',
 [h('6. Архитектура и реализация'),code('роль=урон; дистанция=дальняя\nУточнения: новичок; любой'),code(pipeline),
 p('Допустимые роли: урон, защита, поддержка. Дистанции: ближняя, дальняя, любая. Опыт: новичок, опытный. Противники: любой, зверь, летающий, бронированный, маг, нежить.'),code('python3 lab3/app.py --fixed')],
 [table(['Входные предпочтения','Результат'],SCENARIOS,[310,175]),p('Пройдены 18 тестов Python: рекомендации, нормализация, неизвестные значения, пустые ответы, дубликаты полей, уточнения, подтверждение, повтор строки и отсутствие swipl. Полные входы, запросы и объяснения пяти сценариев находятся в расширенном отчете и evidence/dss_scenarios.json.'),
 p('Неизвестная роль и неполная обязательная часть вызывают повтор ввода. Конфликт пожеланий дает пустую выборку. Агрегация удаляет дубли; рейтинга кандидатов нет.')],
 'DSS объясняет результат через факты и выведенные свойства. Для расширения достаточно изменять БЗ. Ограничение - небольшая учебная модель без количественной оценки силы персонажей.')


def draw_schema():
    d=Drawing(485,228)
    def box(x,y,w,hh,title,body=''):
        d.add(Rect(x,y,w,hh,rx=5,fillColor=colors.HexColor('#f2f2f2'),strokeColor=colors.HexColor('#606060')))
        d.add(String(x+w/2,y+hh-18,title,fontName='Bold',fontSize=10,textAnchor='middle',fillColor=colors.HexColor('#000000')))
        for i,line in enumerate(body.split('\n') if body else []):
            d.add(String(x+9,y+hh-35-i*14,line,fontName='Body',fontSize=8.2))
    def arrow(x1,y1,x2,y2,label=''):
        d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor('#303030')))
        if x2>x1:
            pts=[x2,y2,x2-6,y2+3,x2-6,y2-3]
        else: pts=[x2,y2,x2-3,y2-6,x2+3,y2-6]
        d.add(Polygon(pts,fillColor=colors.HexColor('#303030'),strokeColor=None))
        if label:d.add(String((x1+x2)/2,(y1+y2)/2+8,label,fontName='Body',fontSize=8,textAnchor='middle'))
    box(0,160,140,47,'Character')
    box(210,160,105,47,'Weapon')
    box(385,160,100,47,'Enemy')
    arrow(140,183,210,183,'hasWeapon')
    arrow(315,183,385,183,'counters')
    box(0,12,190,119,'Исходные классы','Melee, Ranged\nDamage, Tank, Support\nBeginner')
    box(215,12,270,119,'Выводные классы','Frontliner, Protector, RangedDamage\nBeginnerChoice, ArmoredHunter\nRangedSupport, Versatile')
    arrow(90,131,90,160)
    d.add(Line(350,131,350,144,strokeColor=colors.HexColor('#303030')))
    d.add(Line(350,144,110,144,strokeColor=colors.HexColor('#303030')))
    arrow(110,144,110,160)
    return d

def footer(canvas,doc):
    # По требованию пользователя: без колонтитулов и номеров страниц.
    pass

def render(name,pages):
    story=[]; md=[]
    for i,(title,items) in enumerate(pages):
        if i:story.append(PageBreak())
        if items and items[0][0]=='cover':
            kind=items[0][1]
            centered=ParagraphStyle('Cover',parent=ST['TextRU'],alignment=TA_CENTER,fontSize=13,leading=19)
            story += [Spacer(1,25),Paragraph('Университет ИТМО',centered),Spacer(1,95),
                      Paragraph('СИСТЕМЫ ИСКУССТВЕННОГО ИНТЕЛЛЕКТА',centered),Spacer(1,22),
                      Paragraph(escape(kind).replace('\n','<br/>'),ParagraphStyle('CoverTitle',parent=centered,fontName='Bold',fontSize=18,leading=24)),
                      Spacer(1,22),Paragraph('Модуль 1. Базы знаний и онтологии',centered),
                      Spacer(1,15),Paragraph('Тема: «Подбор персонажа фэнтезийной RPG»',centered),Spacer(1,75),
                      P('Выполнил: Бирюков Ян'),P('Группа: 3321'),
                      P('Проверила: Королева Ю.А.'),Spacer(1,65),Paragraph('Санкт-Петербург, 2026',centered)]
            md += ['# '+kind.replace('\n',' '),'','Университет ИТМО. Системы искусственного интеллекта.',
                   'Модуль 1. Базы знаний и онтологии. Тема: подбор персонажа фэнтезийной RPG.',
                   'Выполнил: Бирюков Ян; группа: 3321; проверила: Королева Ю.А.','Санкт-Петербург, 2026.','']
            continue
        story.append(P(title,'HeadingRU'))
        md += ['# '+title.replace('\n',' '),'']
        for item in items:
            kind=item[0]
            if kind in ('p','h'):
                story.append(P(item[1],'TextRU' if kind=='p' else 'SubRU'))
                md += [('## ' if kind=='h' else '')+item[1],'']
            elif kind=='code':
                # Делим длинные строки кода по запятой для печатной ширины.
                lines=[]
                for line in item[1].splitlines():
                    while len(line)>88:
                        pos=line.rfind(', ',0,83)
                        if pos<25:pos=82
                        else:pos+=1
                        lines.append(line[:pos]);line='  '+line[pos:].lstrip()
                    lines.append(line)
                story.append(Preformatted('\n'.join(lines),ST['CodeRU']))
                md += ['```',item[1],'```','']
            elif kind=='table':
                _,headers,rows,widths=item
                data=[[P(c,'SmallRU') for c in headers]]+[[P(c,'SmallRU') for c in row] for row in rows]
                tab=Table(data,colWidths=widths or [485/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
                tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5e5e5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#606060')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f5f5')])]))
                story.extend([tab,Spacer(1,10)])
                md += ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']
                md += ['| '+' | '.join(map(str,row))+' |' for row in rows];md.append('')
            elif kind=='diagram':
                story.extend([draw_schema(),Spacer(1,10)])
                md += ['```mermaid','graph LR','Character -->|hasWeapon| Weapon','Weapon -->|counters| Enemy','BaseTraits -->|subClassOf| Character','DerivedClasses -->|subClassOf| Character','```','']
    path=OUT/f'{name}.pdf'
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=55,leftMargin=55,topMargin=55,bottomMargin=48,title=name,author='Учебный проект',allowSplitting=1).build(story,onFirstPage=footer,onLaterPages=footer)
    (ROOT/'reports'/f'{name}.md').write_text('\n'.join(md))
    print(path)
for name,pages in [('lab1_report',short1),('lab2_report',short2),('lab3_report',short3),('module1_report',full)]:
    render(name,pages)
