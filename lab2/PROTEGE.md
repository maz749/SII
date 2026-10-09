# Открытие и проверка в Protégé

Онтология создана программно из БЗ Prolog и сохранена в стандартном RDF/XML.
В этой среде автоматические проверки выполнены через Owlready2/HermiT и Pellet. Сам GUI
Protégé не запускался: Homebrew отказал в установке из-за проверки Gatekeeper.
Скриншоты GUI не подменяются рисунками. Ниже - сценарий демонстрации в установленном редакторе.

1. Откройте `rpg.owl` через **File → Open**. Это исходные факты и правила, без материализованных выводов.
2. Во вкладке **Entities → Classes** раскройте `Character`: видны свойства-типизации
   `Melee`, `Ranged`, `Damage`, `Tank`, `Support`, `Beginner` и семь выводных классов.
   `Weapon` и `Enemy` находятся рядом с `Character`, под `owl:Thing`.
3. В **Object properties** проверьте `hasWeapon`: domain `Character`, range `Weapon`,
   характеристика Functional и у Character ограничение exactly 1; `counters`: domain `Weapon`, range `Enemy`, у Weapon ограничение min 1.
   В **Data properties** проверьте `beginnerFriendly`: domain Character, range xsd:boolean, Functional;
   у шести персонажей указан литерал true. У остальных значение неизвестно.
4. В **Individuals** откройте `paladin`: типы `Character`, `Melee`, `Damage`, `Tank`,
   `Support`, `Beginner`; связь `hasWeapon sword`.
5. Через **Window → Tabs → SWRLTab** (если плагин доступен) проверьте семь правил
   `R1_frontliner` ... `R7_versatile`. Текст правил также приведен в отчете.
6. Выберите reasoner с поддержкой используемых SWRL-правил (например HermiT), затем
   **Reasoner → Start reasoner**. Если выбранный reasoner не поддерживает правила,
   используйте воспроизводимую проверку Pellet: `python lab2/verify_ontology.py`.
7. Включите **Window → Tabs → DL Query**, отметьте **Instances** и выполните:

| Выражение Manchester | Ожидаемые экземпляры после вывода |
|---|---|
| `Protector` | `paladin` |
| `RangedDamage and BeginnerChoice` | `ranger` |
| `ArmoredHunter` | `druid, mage, necromancer` |
| `RangedSupport` | `bard, druid` |
| `Character and hasWeapon value staff` | `druid, mage, necromancer` |

`rpg_inferred.owl` - отдельная копия с уже материализованными результатами Pellet;
ее можно использовать для просмотра результатов и SPARQL без повторного SWRL-вывода.
Это не доказательство работы выбранного GUI-reasoner: для такого доказательства
нужно начинать с `rpg.owl`.

## Семантика

- Роли совместимы: паладин одновременно наносит урон, защищает и поддерживает.
- `Melee` и `Ranged` объявлены несовместимыми в рамках упрощенной модели.
- `Character`, `Weapon` и `Enemy` несовместимы между собой.
- SWRL-правила являются импликациями, а не определениями эквивалентных классов.
- Отсутствие `Beginner(x)` в OWL не доказывает `not Beginner(x)`.
  Поэтому Prolog-запрос с `\+ beginner(X)` не переводится буквально в OWL-отрицание.
- Functional `hasWeapon` означает не более одного различного значения; ограничение exactly 1
  дополнительно требует существования значения в логической модели. Отсутствие явной связи
  при открытом мире не обязательно вызывает противоречие, поэтому явную полноту проверяют тесты БЗ.
- У Weapon задано counters min 1 Enemy; все 20 предметных индивидов объявлены AllDifferent.
- Три отрицательные проверки HermiT подтверждают обнаружение несовместимых дистанций,
  двух разных оружий у одного персонажа и строкового значения вместо xsd:boolean.

Источники: [DL Query](https://protegewiki.stanford.edu/wiki/DLQueryTab),
[правила SWRL в Owlready2](https://owlready2.readthedocs.io/en/latest/rule.html).
