# -*- coding: utf-8 -*-/
from django.db.models import get_model
from django.conf import settings
import MySQLdb
import MySQLdb.cursors
import datetime as dt
import time
import sys
from multiprocessing import Process

def update_models():
    print 'INICIANDO ATUALIZACAO E89-SQL-INTEGRATION'
    t1 = time.time()
    for model in settings.INTEGRATION_SYNC_ORDER:
        updater = ModelUpdater(get_model(settings.INTEGRATION_APP_SYNC,model))
        p = Process(target=updater.run_update) # Novo processo para evitar alocação excessiva de memória
        p.start()
        p.join()

    total = time.time() - t1
    print "ATUALIZACAO BANCO DE DADOS FINALIZADA. TEMPO TOTAL: %f s " % (total)
    return total

def print_queries():
    for model in settings.INTEGRATION_SYNC_ORDER:
        updater = ModelUpdater(get_model(settings.INTEGRATION_APP_SYNC,model))
        updater.build_query()
        print
        print ">>> " + model
        print
        print updater.query
        print




class ModelUpdater(object):

    def __init__(self, model):
        self.model = model
        self.db = None
        self.cursor = None
        self.query = None

        self.FIELD_MAP = settings.INTEGRATION_SYNC_CONFIG[self.model.__name__]["FIELD_MAP"]
        self.EXTERNAL_VIEW = settings.INTEGRATION_SYNC_CONFIG[self.model.__name__]["EXTERNAL_VIEW"]
        self.EXTERNAL_VIEW_ID = self.FIELD_MAP[settings.INTEGRATION_VIEW_ID_FIELD]

    def run_update(self):
        t1 = time.time()
        self.connect_to_database()
        self.build_query()
        self.execute_changes()
        if self.model.__name__ in settings.INTEGRATION_DELETE_ORDER:
            self.deleteIfNeeded()
        self.cursor.close()
        self.db.close()
        print "Update finalizado. Tempo total: %d s."%(time.time()-t1)

    def connect_to_database(self):
        self.db = MySQLdb.connect(host=settings.INTEGRATION_EXTERNAL_DB_HOST,
                                  user=settings.INTEGRATION_EXTERNAL_DB_USER,
                                  passwd=settings.INTEGRATION_EXTERNAL_DB_PASSWORD,
                                  port=int(settings.INTEGRATION_EXTERNAL_DB_PORT),
                                  db=settings.INTEGRATION_EXTERNAL_DB_NAME,
                                  use_unicode=True,
                                  cursorclass=MySQLdb.cursors.DictCursor)
        self.cursor = self.db.cursor()

    def build_query(self):

        # Montagem da query
        selects = []
        froms = []
        wheres = []
        group_bys = []
        for local_field,config in self.FIELD_MAP.items():

            if type(config) == type(""): # 1) Correspondência direta entre os campos
                field_query = config
                field_as = local_field

                selects.append("v.%s as %s"%(field_query,field_as))

            elif config.has_key("func_convert"): # 1.1) Correspondência direta com conversão de valor
                field_query = config["campo_view"]
                field_as = local_field

                selects.append("v.%s as %s"%(field_query,field_as))

            elif config.has_key("model_fk") and config.has_key("campo_view"): # 2) Foreign key com model representado internamente. Não há inner join.

                field_query = config["campo_view"]
                field_as = local_field

                selects.append("v.%s as %s"%(field_query,field_as))

            elif config.has_key("view_join"): # 3) Foreign key com model não representado internamente. Há inner join.

                query_data = config.copy()
                query_data["campo_local"] = local_field
                query_data["EXTERNAL_VIEW"] = self.EXTERNAL_VIEW
                query_data["EXTERNAL_VIEW_ID"] = self.EXTERNAL_VIEW_ID

                select = """(SELECT
                                %(view_join)s.%(campo_desejado)s
                            FROM
                                %(EXTERNAL_VIEW)s v2
                                INNER JOIN
                                %(view_join)s ON v2.%(campo_view)s = %(view_join)s.%(campo_join)s
                            WHERE
                                v2.%(EXTERNAL_VIEW_ID)s = v.%(EXTERNAL_VIEW_ID)s LIMIT 1) as %(campo_local)s"""%(query_data)


                selects.append(select.replace("\n",""))

            elif config.has_key("select"): # 4) Query específica
                query_data = config.copy()
                query_data["campo_local"] = local_field
                query_data["EXTERNAL_VIEW"] = self.EXTERNAL_VIEW
                query_data["EXTERNAL_VIEW_ID"] = self.EXTERNAL_VIEW_ID
                query_data["where"] = query_data.get("where","").replace(self.EXTERNAL_VIEW,"v") # Aplicando alias
                if not query_data.get("from"):
                    query_data["group_by"] = "v." + query_data["group_by"] # Aplicando alias

                select = """%(select)s AS %(campo_local)s"""%(query_data)
                selects.append(select)

                for param,clause_list in [["from",froms],["where",wheres],["group_by",group_bys]]:
                    if query_data.get(param):
                        clause_list.append(query_data[param])


        select_clause = "SELECT DISTINCT " + ", ".join(selects)
        from_clause = " FROM %s v"%(self.EXTERNAL_VIEW) + ((", " + ", ".join(froms)) if len(froms) > 0 else "")
        where_clause = (" WHERE " + " AND ".join(wheres)) if len(wheres) > 0 else ""
        group_by_clause = (" GROUP BY " + ", ".join(group_bys)) if len(group_bys) > 0 else ""

        self.query =  select_clause + from_clause + where_clause + group_by_clause + ";"

    def execute_query(self,query):
        try:
            self.cursor.execute(query)
        except MySQLdb.OperationalError as e:
            error_code = e.args[0]
            if error_code == 2006 or error_code == 2013:
                self.connect_to_database()
                self.execute_query(query)
            else:
                raise e

    def execute_changes(self):
        self.execute_query(self.query)

        # Obtendo resultados
        count_new = 0
        count_update = 0
        all_data = self.cursor.fetchall()
        for data in all_data:
            new_data = {}
            ignore = False # Flag para ignorar o objeto caso não seja possível satisfazer a foreign key
            for key,value in data.items():
                if type(self.FIELD_MAP[key]) == type({}): # Buscando foreign keys e conversões

                    if self.FIELD_MAP[key].has_key("func_convert"): # Conversão de valor. Ex: datas
                        func_convert = self.FIELD_MAP[key]["func_convert"]
                        new_data[key] = func_convert(value)

                    elif self.FIELD_MAP[key].has_key("model_fk"): # Foreign key para model interno
                        model_fk = self.FIELD_MAP[key]["model_fk"]
                        campo_fk = self.FIELD_MAP[key]["campo_fk"]
                        model_fk = get_model(settings.INTEGRATION_APP_SYNC,model_fk)
                        assert model_fk is not None, "O model %s passado como fk do atributo %s nao foi encontrado. Confira se a grafia esta correta."%(self.FIELD_MAP[key]["model_fk"],key)

                        if not value and self.FIELD_MAP[key].get("if_null"): # Opção de valor caso nulo
                            value = self.FIELD_MAP[key].get("if_null")

                        if self.FIELD_MAP[key].get("campo_fk_format") and value: # Opção de formatação do valor buscado
                            value = self.FIELD_MAP[key]["campo_fk_format"] % value

                        elif not value: # Foreign key nulo e não há opção if_null
                            ignore = True
                            continue
                        try:
                            new_data[key] = model_fk.objects.values("id").get(**{campo_fk:value})["id"]
                        except model_fk.MultipleObjectsReturned:
                            raise model_fk.MultipleObjectsReturned("Nao foi possivel montar a foreign key do atributo %s do model %s para o model %s. A filtragem pelo campo %s com valor %s retornou multiplos resultados."%(key,self.model.__name__,model_fk, campo_fk, str(value)))
                        except model_fk.DoesNotExist:
                            # A foreign key não pode ser encontrada pelo id_federal
                            # Isso pode ocorrer em casos que o fk no banco externo é nulo ou refere-se a um objeto não disponível para o UF
                            ignore = True
                            print 'Valor nao encontrado',model_fk.__name__,campo_fk,value

                    else: # Foreign key para VIEW não representada internamente
                        new_data[key] = value
                else:
                    new_data[key] = value

            if not ignore:
                kwargs={settings.INTEGRATION_VIEW_ID_FIELD:data[settings.INTEGRATION_VIEW_ID_FIELD]}
                if (self.model.objects.filter(**kwargs).count() == 0): # Criando nova instância
                    instance = self.model()
                    for attr,val in new_data.items(): setattr(instance,attr,val)
                    instance.save()
                    count_new += 1
                else: # Atualizando instância existente
                    try:
                        instance = self.model.objects.get(**kwargs)
                    except self.model.MultipleObjectsReturned as e:
                        print 'Erro ao atualizar uma instancia existente. A busca pelos parametros %s retornou dois valores.'%str(kwargs)
                        raise e
                    cur_vals = dict([[key, getattr(instance,key)] for key in new_data.keys()])
                    if cur_vals != new_data:
                        for attr,val in new_data.items(): setattr(instance,attr,val)
                        instance.save()
                        count_update += 1


        print "Foram criadas %d novas instancias do model %s"%(count_new,self.model.__name__)
        print "Foram atualizadas %d instâncias do model %s"%(count_update,self.model.__name__)

    def deleteIfNeeded(self):
        pks_local = set(list(self.model.objects.exclude(**{settings.INTEGRATION_VIEW_ID_FIELD+ "__lt":0}).values_list(settings.INTEGRATION_VIEW_ID_FIELD,flat=True)))

        self.execute_query('SELECT %s FROM %s;'%(self.EXTERNAL_VIEW_ID,self.EXTERNAL_VIEW))
        pks_external = set([item[self.EXTERNAL_VIEW_ID] for item in self.cursor.fetchall()])

        pks_delete = list(pks_local.difference(pks_external))
        print pks_delete,len(pks_local),len(pks_external)

        kwargs = {settings.INTEGRATION_VIEW_ID_FIELD + "__in":pks_delete}
        if pks_delete:
            self.model.objects.filter(**kwargs).delete()
            print "Foram excluidas %d instancias do model %s"%(len(pks_delete),self.model.__name__)


