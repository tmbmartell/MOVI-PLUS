"""Teste isolado de formulário socioeconômico V5, sem dados pessoais reais."""
import tempfile,os,sys
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory(prefix='novagente-socio-test-') as path:
 os.environ['CLUBE_DATA']=path
 os.environ['CLUBE_ENABLE_SENSITIVE']='0'
 sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
 import app
 from schema import ORIGINAL,EXTRA,SENSITIVE
 from fastapi import HTTPException
 with app.db() as c:
  for i,role in ((11,'admin'),(12,'driver')):
   c.execute('INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)',
    (i,'qa'+str(i),'dummy',role,'active','Participante Fictício',app.now()))
   if role=='driver':
    c.execute('INSERT INTO consents(uid,updated_at) VALUES(?,?)',(i,app.now()))
    app.save_profile(c,i,{})
  c.commit()
 principal={'id':12,'role':'driver','name':'Participante Fictício','status':'active','must_change':0}
 app.app.dependency_overrides[app.auth]=lambda:principal
 client=TestClient(app.app,base_url='https://example.test')
 headers={'X-Requested-With':'NOVAGENTE-V5'}
 def put(endpoint,obj):
  return client.put('/api/'+endpoint,json=obj,headers=headers)
 def get(endpoint):
  return client.get('/api/'+endpoint)
 def assertstatus(res,status):
  assert res.status_code==status,(res.status_code,res.text[:300])
 info=get('schema').json()
 assert info['original']==23 and info['extra']==15 and len(info['fields'])==38
 assert sum(f['protected'] for f in info['fields'])==9
 print('01: 38 original + new fields accounted for; nine protected: OK')
 step1={'gross_income':2400,'other_job':'CLT','platform':'UBER','since':'2 anos','team':'Teste','weekly_days':5,'daily_fuel':65}
 r=put('profile',step1);assertstatus(r,200)
 step2={'banks':['SICOOB'],'main_bank':'NU','bid_resources':'não tenho','cpf_bank_restriction':'NAO','cpf_store_restriction':'Não'}
 r=put('profile',step2);assertstatus(r,200)
 step3={'move_brasil':'AINDA NÃO ME CADASTREI','car_model_interest':'GEELY EX2'}
 r=put('profile',step3);assertstatus(r,200)
 step4={'household_expenses':1500,'monthly_saving_goal':400}
 r=put('profile',step4);assertstatus(r,200)
 after=get('profile').json()
 assert after['answers']['platform']=='UBER' and after['answers']['main_bank']=='NU'
 assert after['answers']['household_expenses']==1500 and after['progress']['completed']>=len(step1)+len(step2)+len(step3)+len(step4)
 print('02: Independent saves, previous data preserved, incomplete form allowed: OK')
 fail=put('profile',{'weekly_days':9});assertstatus(fail,422)
 assert 'Quantos dias' in fail.json()['detail']
 assertstatus(put('profile',{'cpf':'11122233344'}),403)
 print('03: Errors identify field; protected identifiers not allowed: OK')
 cons=get('consents').json()['choices']
 assert cons['assisted_entry']==0
 person=principal.copy()
 principal.update({'id':11,'role':'admin'})
 assertstatus(get('admin/assisted-profile/12'),403)
 assertstatus(put('admin/assisted-profile/12',{'platform':'99'}),403)
 print('04: Admin assisted write requires explicit authorizations: OK')
 principal.clear();principal.update(person)
 choices={'insights':True,'marketing':False,'sharing':False,'documents':False,'assisted_entry':True}
 assertstatus(put('consents',choices),200)
 assert get('consents').json()['choices']['assisted_entry']==1
 principal.update({'id':11,'role':'admin'})
 r=get('admin/assisted-profile/12');assertstatus(r,200)
 assert r.json()['answers']['platform']=='UBER'
 assertstatus(put('admin/assisted-profile/12',{'cpf':'fake'}),403)
 r=put('admin/assisted-profile/12',{'platform':'99','daily_revenue':220})
 assertstatus(r,200)
 print('05: Admin with opt-in can edit only nonprotected fields: OK')
 principal.clear();principal.update(person)
 assert get('profile').json()['answers']['platform']=='99'
 choices['assisted_entry']=False
 assertstatus(put('consents',choices),200)
 principal.update({'id':11,'role':'admin'})
 assertstatus(get('admin/assisted-profile/12'),403)
 print('06: Revocation promptly denies assisted access: OK')
 principal.clear();principal.update(person)
 assertstatus(put('consents',{'insights':True,'marketing':False,'sharing':False,'documents':False}),200)
 assert get('consents').json()['choices']['assisted_entry']==0
 print('07: Legacy 4-choice clients remain compatible: OK')
 app.app.dependency_overrides.clear()
print('ALL SEVEN SOCIOECONOMIC TESTS PASS; data disposed with temporary DB.')