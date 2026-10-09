#!/usr/bin/env python3
"""Реальный Pellet-вывод, сверка всех фактов и 7 правил с SWI-Prolog."""
import json
from pathlib import Path
import subprocess
from owlready2 import World, sync_reasoner_pellet, sync_reasoner, OwlReadyInconsistentOntologyError
from rdflib import Graph, Namespace, RDF
from build_ontology import BASE, CLASS_MAP, RULES, read_facts
ROOT=Path(__file__).resolve().parents[1]

def prolog_answers(pred):
    goal=f'use_module(library(http/json)),findall(X,{pred}(X),Xs),sort(Xs,Ys),json_write_dict(current_output,Ys)'
    r=subprocess.run(['swipl','-q','-s',str(ROOT/'lab1/knowledge_base.pl'),'-g',goal,'-t','halt'],capture_output=True,text=True,check=True)
    return json.loads(r.stdout)

def main():
    path=ROOT/'lab2/rpg.owl'
    graph=Graph().parse(path)
    ns=Namespace(BASE)
    facts=read_facts()
    for pred,args in facts:
        if len(args)==1:
            assert (ns[args[0]],RDF.type,ns[CLASS_MAP[pred]]) in graph,(pred,args)
        else:
            prop='hasWeapon' if pred=='has_weapon' else 'counters'
            assert (ns[args[0]],ns[prop],ns[args[1]]) in graph,(pred,args)
    swrl=Namespace('http://www.w3.org/2003/11/swrl#')
    assert len(list(graph.subjects(RDF.type,swrl.Imp)))==7
    world=World()
    onto=world.get_ontology(path.as_uri()).load()
    # До reasoner ни один выводной тип явно не присвоен персонажам.
    for cls,_ in RULES.values():
        assert not list(onto[cls].instances()),cls
    with onto:
        sync_reasoner_pellet([onto],infer_property_values=True,debug=1)
    assert not list(world.inconsistent_classes()),'Несовместимые классы'
    result={'consistent':True,'unary_facts':sum(len(a)==1 for _,a in facts),
            'binary_facts':sum(len(a)==2 for _,a in facts),'swrl_rules':7,
            'classes':len(list(onto.classes())),'domain_individuals':len(set(a[0] for _,a in facts if len(a)==1)),
            'named_entities_including_rules':len(list(onto.individuals())),
            'rules':{}}
    for pred,(cls,_) in RULES.items():
        owl=sorted(x.name for x in onto[cls].instances())
        prolog=prolog_answers(pred)
        assert owl==prolog,(pred,owl,prolog)
        result['rules'][pred]={'class':cls,'prolog':prolog,'owl':owl,'equal':True}
    result['data_property_values'] = {
        x.name:x.beginnerFriendly for x in onto.Character.instances()
        if x.beginnerFriendly is not None
    }
    assert sorted(result['data_property_values']) == prolog_answers('beginner')
    assert all(v is True for v in result['data_property_values'].values())
    # HermiT стартует с исходного OWL, а не с материализованных результатов Pellet.
    hermit_world=World()
    hermit=hermit_world.get_ontology(path.as_uri()).load()
    with hermit:
        sync_reasoner([hermit],infer_property_values=True,debug=1)
    assert not list(hermit_world.inconsistent_classes())
    result['hermit']={}
    for pred,(cls,_) in RULES.items():
        values=sorted(x.name for x in hermit[cls].instances())
        assert values==prolog_answers(pred),(pred,values)
        result['hermit'][pred]=values
    # Отрицательные тесты выполняются только на независимых копиях в памяти.
    result['negative_ontology_tests']={}
    for scenario in ['disjoint_ranges', 'two_distinct_weapons', 'invalid_boolean']:
        bad_world=World()
        bad=bad_world.get_ontology(path.as_uri()).load()
        with bad:
            if scenario=='disjoint_ranges': bad.warrior.is_a.append(bad.Ranged)
            elif scenario=='two_distinct_weapons':
                bad.hasWeapon[bad.warrior].append(bad.bow)
            else: bad.warrior.beginnerFriendly='unknown'
            try:
                sync_reasoner([bad],debug=0)
            except OwlReadyInconsistentOntologyError:
                result['negative_ontology_tests'][scenario]='inconsistency_detected'
            else:
                raise AssertionError('Не обнаружено противоречие: '+scenario)
    # Сохраняем отдельно, чтобы исходную онтологию можно было проверить заново.
    onto.save(file=str(ROOT/'lab2/rpg_inferred.owl'),format='rdfxml')
    inferred=Graph().parse(ROOT/'lab2/rpg_inferred.owl')
    queries=[
        ('characters', 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT DISTINCT ?x WHERE {?x a/rdfs:subClassOf* rpg:Character} ORDER BY ?x', 'character'),
        ('ranged_damage', 'SELECT ?x WHERE {?x a rpg:RangedDamage} ORDER BY ?x', 'ranged_damage'),
        ('protector', 'SELECT ?x WHERE {?x a rpg:Protector} ORDER BY ?x', 'protector'),
        ('armor', 'SELECT ?x WHERE {?x a rpg:Damage; rpg:hasWeapon ?w. ?w rpg:counters rpg:armored} ORDER BY ?x', 'armored_hunter'),
        ('beginner_ranged', 'SELECT ?x WHERE {?x a rpg:RangedDamage, rpg:BeginnerChoice} ORDER BY ?x', None),
    ]
    result['sparql']={}
    for label,query,pred in queries:
        values=[str(row[0]).split('#')[-1] for row in inferred.query(f'PREFIX rpg: <{BASE}> '+query)]
        expected=prolog_answers(pred) if pred else ['ranger']
        assert values==expected,(label,values,expected)
        result['sparql'][label]=values
    values=[str(row[0]).split('#')[-1] for row in inferred.query(f'PREFIX rpg: <{BASE}> SELECT ?x WHERE {{ ?x rpg:beginnerFriendly true }} ORDER BY ?x')]
    assert values==prolog_answers('beginner')
    result['sparql']['beginner_friendly']=values
    (ROOT/'evidence/ontology_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
