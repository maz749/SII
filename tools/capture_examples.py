"""Записывает реальные ответы и диалоги для пяти сценариев отчета."""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lab3.app import recommend
cases=[
 ('beginner','роль=урон; дистанция=дальняя','новичок','любой',('damage','ranged','beginner','any')),
 ('support','роль=поддержка; дистанция=дальняя','опытный','любой',('support','ranged','any','any')),
 ('armor','роль=урон; дистанция=дальняя','опытный','бронированный',('damage','ranged','any','armored')),
 ('undead','роль=поддержка; дистанция=любая','новичок','нежить',('support','any','beginner','undead')),
 ('empty','роль=защита; дистанция=дальняя','новичок','любой',('tank','ranged','beginner','any')),
]
results=[]
for name,profile,experience,enemy,args in cases:
 query,rows=recommend(*args)
 r=subprocess.run([sys.executable,str(ROOT/'lab3/app.py'),'--fixed'],input='\n'.join([profile,experience,enemy])+'\n',capture_output=True,text=True,check=True)
 (ROOT/f'evidence/dialog_{name}.txt').write_text('Вход:\n'+ '\n'.join([profile,experience,enemy])+'\n\nФактический stdout:\n'+r.stdout)
 results.append(dict(name=name,profile=profile,experience=experience,enemy=enemy,query=query,rows=rows))
(ROOT/'evidence/dss_scenarios.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
r=subprocess.run([sys.executable,str(ROOT/'lab3/app.py'),'--fixed'],input='ошибка\nроль=урон; дистанция=дальняя\nновичок\nлюбой\n',capture_output=True,text=True,check=True)
(ROOT/'evidence/dialog_invalid.txt').write_text('Вход: ошибка; затем корректная строка и два уточнения.\n\n'+r.stdout)
print('Записаны 5 сценариев и пример исправления ошибки.')
