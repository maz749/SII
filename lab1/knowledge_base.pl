% character/1: доступные персонажи-архетипы.
character(warrior).
character(paladin).
character(guardian).
character(ranger).
character(assassin).
character(mage).
character(cleric).
character(druid).
character(bard).
character(necromancer).

% melee/1 и ranged/1: основная дистанция боя (в этой модели ровно одна).
melee(warrior).
melee(paladin).
melee(guardian).
melee(assassin).
melee(cleric).
ranged(ranger).
ranged(mage).
ranged(druid).
ranged(bard).
ranged(necromancer).

% damage/1, tank/1, support/1: роли могут пересекаться.
damage(warrior).
damage(paladin).
damage(ranger).
damage(assassin).
damage(mage).
damage(druid).
damage(necromancer).
tank(warrior).
tank(paladin).
tank(guardian).
support(paladin).
support(cleric).
support(druid).
support(bard).

% beginner/1: персонаж подходит новичку. Отсутствие факта не равно
% объективной сложности: это только отсутствие подтверждения в нашей БЗ.
beginner(warrior).
beginner(paladin).
beginner(guardian).
beginner(ranger).
beginner(cleric).
beginner(bard).

% weapon/1 и enemy/1: словари оружия и противников.
weapon(sword).
weapon(bow).
weapon(staff).
weapon(dagger).
weapon(mace).
enemy(beast).
enemy(flying).
enemy(armored).
enemy(caster).
enemy(undead).

% has_weapon/2: основное оружие персонажа (10 бинарных фактов).
has_weapon(warrior, sword).
has_weapon(paladin, sword).
has_weapon(guardian, mace).
has_weapon(ranger, bow).
has_weapon(assassin, dagger).
has_weapon(mage, staff).
has_weapon(cleric, mace).
has_weapon(druid, staff).
has_weapon(bard, bow).
has_weapon(necromancer, staff).

% counters/2: оружие эффективно против указанного типа (5 фактов).
% Это условные правила учебной игры, а не универсальные правила RPG.
counters(sword, beast).
counters(bow, flying).
counters(staff, armored).
counters(dagger, caster).
counters(mace, undead).

% R1 frontliner/1: боец ближнего боя, способный принимать урон.
frontliner(X) :- melee(X), tank(X).
% R2 protector/1: боец первой линии с поддержкой; цепочка вывода R1 -> R2.
protector(X) :- frontliner(X), support(X).
% R3 ranged_damage/1: персонаж дальнего боя с ролью нанесения урона.
ranged_damage(X) :- ranged(X), damage(X).
% R4 beginner_choice/1: доступный персонаж, рекомендованный новичку.
beginner_choice(X) :- character(X), beginner(X).
% R5 armored_hunter/1: атакующий персонаж с оружием против брони.
armored_hunter(X) :- damage(X), has_weapon(X, W), counters(W, armored).
% R6 ranged_support/1: поддержка на дальней дистанции.
ranged_support(X) :- ranged(X), support(X).
% R7 versatile/1: совмещает нанесение урона и поддержку.
versatile(X) :- damage(X), support(X).
