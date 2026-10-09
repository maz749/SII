:- begin_tests(rpg).
:- ensure_loaded('../lab1/knowledge_base.pl').
test(characters, true(N=10)) :- findall(X,character(X),Xs), length(Xs,N).
test(frontliner, set(X == [guardian,paladin,warrior])) :- frontliner(X).
test(protector, set(X == [paladin])) :- protector(X).
test(ranged_damage, set(X == [druid,mage,necromancer,ranger])) :- ranged_damage(X).
test(beginner_choice, set(X == [bard,cleric,guardian,paladin,ranger,warrior])) :- beginner_choice(X).
test(armored_hunter, set(X == [druid,mage,necromancer])) :- armored_hunter(X).
test(ranged_support, set(X == [bard,druid])) :- ranged_support(X).
test(versatile, set(X == [druid,paladin])) :- versatile(X).
test(empty, fail) :- tank(X),ranged(X).
test(negation, set(X == [assassin,druid,mage,necromancer])) :- character(X), \+ beginner(X).
test(every_character_has_one_weapon) :-
    forall(character(X), (findall(W,has_weapon(X,W),[_]))).
test(valid_weapons) :- forall(has_weapon(X,W),(character(X),weapon(W))).
test(valid_enemies) :- forall(counters(W,E),(weapon(W),enemy(E))).
test(one_range) :- forall(character(X), (findall(R,(member(R,[melee,ranged]),call(R,X)),[_]))).
:- end_tests(rpg).
