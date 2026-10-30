"""Questionário-base do Programa de Renovação de Frota, integralmente preservado."""
ORIGINAL=[
 ("full_name","Nome Completo","text",1,[],1),
 ("cpf","CPF","cpf",1,[],1),
 ("rg","R.G","text",1,[],1),
 ("birth_date","Data de Nascimento","date",1,[],1),
 ("email","E-mail","email",1,[],1),
 ("address_cep","Endereço Completo com CEP","textarea",1,[],1),
 ("gross_income","Renda Mensal Bruta","money",1,[],0),
 ("other_job","Atua em outra função, além de motorista de app?","select",1,["CLT","Autônomo","Outro","Não"],0),
 ("whatsapp","Celular - Número com Whats","phone",1,[],1),
 ("platform","Qual sua plataforma principal?","select",1,["LEVA EU","99","UBER","URBANO NORTE","IN DRIVE","Outro"],0),
 ("since","Trabalha há quanto tempo de motorista de app?","text",1,[],0),
 ("team","Qual a sua Equipe?","text",1,[],0),
 ("banks","Tem conta corrente em quais destes bancos?","multi",1,["CAIXA ECONOMICA FEDERAL","BANCO DO BRASIL","SICOOB","Outro"],0),
 ("main_bank","Qual banco você mais movimenta?","select",1,["BRADESCO","SANTANDER","NU","Outro"],0),
 ("bid_resources","Recurso para Lance - Capital próprio","select",1,["não tenho","dinheiro","carro/moto"],0),
 ("bid_cash","Dinheiro - Valor em R$?","money",1,[],0),
 ("vehicle_plate","Entrada: carro/moto - digite a placa","text",0,[],1),
 ("vehicle_finance","Entrada: carro/moto - esta financiado ? caso sim - valor da parcela e saldo devedor","textarea",0,[],0),
 ("cpf_bank_restriction","CPF tem restrição em banco","select",1,["SIM","NAO"],0),
 ("cpf_store_restriction","CPF tem restrição em lojas (EX:. gazin/ havan/riachuelo)","select",1,["SIM","Não"],0),
 ("move_brasil","Já se cadastrou Move Brasil?","select",1,["APROVADO","RECUSADO","AINDA NÃO ME CADASTREI","AGUARDANDO RESPOSTA"],0),
 ("car_model_interest","Carro que tem interesse?","select",1,["BYD - DOLPHIN MINI GL","BYD - DOLPHIN GS","GEELY EX2","Outro"],0),
 ("cnh_upload","Arquivo CNH - foto ou pdf","file",1,[],1),
]
EXTRA=[
 ("weekly_hours","Quantas horas trabalha por semana?","number",0,[],0),
 ("weekly_days","Quantos dias trabalha por semana?","number",0,[],0),
 ("daily_km","Quantos quilômetros roda por dia?","number",0,[],0),
 ("daily_revenue","Quanto ganha em um dia normal (R$)?","money",0,[],0),
 ("daily_fuel","Quanto gasta com combustível por dia (R$)?","money",0,[],0),
 ("monthly_maintenance","Reserva mensal para manutenção (R$)?","money",0,[],0),
 ("vehicle_type","Seu veículo é...","select",0,["Próprio quitado","Financiado","Alugado","Emprestado","Outro"],0),
 ("vehicle_installment","Parcela mensal do carro (R$)?","money",0,[],0),
 ("vehicle_outstanding","Saldo devedor aproximado do veículo (R$)?","money",0,[],0),
 ("household_expenses","Despesas mensais da família (R$)?","money",0,[],0),
 ("other_debts","Parcelas mensais de outras dívidas (R$)?","money",0,[],0),
 ("monthly_saving_goal","Quanto deseja guardar por mês (R$)?","money",0,[],0),
 ("monthly_income_goal","Meta de renda mensal (R$)?","money",0,[],0),
 ("car_change_horizon","Quando pretende trocar de carro?","select",0,["Até 6 meses","6 a 12 meses","1 a 2 anos","Mais de 2 anos","Sem prazo definido"],0),
 ("uses_other_apps","Trabalha em mais de um aplicativo?","select",0,["Sim","Não"],0),
]
ALL=ORIGINAL+EXTRA
MAP={f[0]:f for f in ALL}
SENSITIVE={f[0] for f in ALL if f[5]}
FIELDS=[f[0] for f in ALL]
def describe(f):
 k,label,typ,required,opts,restricted=f
 return {"key":k,"label":label,"type":typ,"required_in_source":bool(required),"options":opts,
         "protected":bool(restricted),"source":"original" if f in ORIGINAL else "complementar"}
def active_fields(profile):
 out=[f for f in ALL if f[0]!="cnh_upload"]
 resource=profile.get("bid_resources")
 if resource and resource!="dinheiro":out=[f for f in out if f[0]!="bid_cash"]
 # A placa é pedida em todos os cadastros de motorista com consentimento para identificação;
 # o financiamento do veículo continua condicional ao recurso indicado no lance.
 if resource and resource!="carro/moto":out=[f for f in out if f[0]!="vehicle_finance"]
 return out
def progress(profile,enabled_sensitive=False):
 rows=[f for f in active_fields(profile) if enabled_sensitive or not f[5]]
 done=sum(profile.get(f[0]) not in (None,"",[]) for f in rows)
 return {"completed":done,"total":len(rows),"percent":round(100*done/len(rows)) if rows else 0,
         "pending":len(rows)-done,"requires_secure_documents":bool("cnh_upload" not in profile)}
