% Запуск: swipl -q -s lab1/queries.pl -g main -t halt
:- ensure_loaded('knowledge_base.pl').

% Все ответы печатаются самим интерпретатором, а не зашиты в примеры.
show(Label, Template, Goal) :-
    findall(Template, Goal, Raw), sort(Raw, Answers),
    format('~w~n~q~n~n', [Label, Answers]).
main :-
    show('Q1 character(X) - все персонажи', X, character(X)),
    show('Q2 has_weapon(X, staff) - поиск по связи', X, has_weapon(X, staff)),
    show('Q3 tank(X), support(X) - И', X, (tank(X), support(X))),
    show('Q4 (tank(X); support(X)) - ИЛИ, без повторов', X, (tank(X); support(X))),
    show('Q5 character(X), \\+ beginner(X) - НЕ после связывания X', X,
         (character(X), \+ beginner(X))),
    show('Q6 protector(X) - цепочка из двух правил', X, protector(X)),
    show('Q7 armored_hunter(X) - правило со связями', X, armored_hunter(X)),
    show('Q8 ranged_damage(X), beginner_choice(X) - два правила', X,
         (ranged_damage(X), beginner_choice(X))),
    show('Q9 ranged_support(X), has_weapon(X, W) - два результата', X-W,
         (ranged_support(X), has_weapon(X, W))),
    show('Q10 tank(X), ranged(X) - нет подходящих объектов', X,
         (tank(X), ranged(X))).
