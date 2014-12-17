# -*- coding: utf-8 -*-/
#   Para poder ser atualizado, cada model precisa estar listado como um dicionário na variável SYNC_CONFIG.
# Cada dicionário deverá possuir dois atributos:
#
#           EXTERNAL_VIEW: nome da view no banco externo à qual o model se refere
#
#           FIELD_MAP: dicionário que relaciona um campo do model com um campo
#                      da view no banco de dados externo.
#
#
# Existem 5 formas de apresentar a relação utilizada para sincronização.
#
# 1) Para os casos em que a correspondência entre os campos é direta, a lógica do dicionário
# FIELD_MAP é montada da seguinte forma:
#
#   {
#       "<campo_local>":"<campo_view>"
#   }
#
# 2) Para os casos em que a correspondência entre os campos é direta, porém é necessária alguma
# forma de conversão dos dados, a lógica do dicionário FIELD_MAP é montada da seguinte forma:
#
#   {
#       "<campo_local>":{
#                           "campo_view":"<campo_view>",
#                           "func_convert": lambda v: return v
#   }
#
#   A função de conversão deverá receber um único parâmetro, o qual é o valor do campo como representado
# no banco de dados, e deve retornar a nova representação do campo.
#
# 3) Para os casos em que é preciso buscar dados em outras tabelas para encontrar o valor do
# campo local, a lógica é montada da seguinte forma:
#
#   {
#       "<campo_local>":{
#                           "campo_view":"<campo_view>",
#                           "model_fk":"<model_fk>",
#                           "campo_fk":"<campo_fk>",
#                           "campo_fk_format":"[^,]%s[$,]", # Opcional
#                           "if_null":82 # Opcional
#       }
#   }
#
# Para esse terceiro formato, seria feita a seguinte query:
#   SELECT
#       <campo_view> AS <campo_fk>
#   FROM
#       EXTERNAL_VIEW
#
#
# Em seguida seria buscada a instância do modelo <model_fk> pelo parâmetro <campo_fk>. Caso o parâmetro
# "campo_fk_format" for fornecido, o valor utilizado para a busca será formatado pela string passada (útil
# para utilizar regular expressions. O parâmetro "if_null" é utilizado da seguinte forma: caso o valor encontrado
# para a coluna "campo_view" seja nulo, a busca pelo foreign key é feita utilizando o valor do parâmetro <if_null>.
# Sendo assim, é executado o seguinte código:
#
# <model_fk>.objects.get(<campo_fk>=<valor_campo_view>) ou <model_fk>.objects.get(<campo_fk>="<campo_fk_format>"%<valor_campo_view>)
#
# Essa instância seria então atribuída no parâmetro <campo_local> da instância sendo criada.
# No parâmetro campo_fk, é possível utilizar operações de query do django como __contains ou __regex.
#
# ATENÇÃO: Para fields que são foreign keys, sempre colocar "_id" junto ao nome do campo, pois o campo com
# nome igual ao foreign key não é um atributo do objeto em si, mas apenas uma property.
#
# 4) Para casos em que o model possui uma foreign key para uma view do banco remoto que não é representada
# internamente por nenhum model, a lógica é a seguinte:
#
# {
#   "<campo_local>":{
#                       "campo_view":"<campo_view>",
#                       "view_join":"<view_join>",
#                       "campo_join":"<campo_fk>",
#                       "campo_desejado":"<campo_desejado>"
#                   }
# }
#
# Nesse caso, será feita uma query da seguinte forma:
#
#   SELECT
#       <view_join>.<campo_desejado> as <campo_local>
#   FROM
#       EXTERNAL_VIEW
#   INNER JOIN
#       <view_join>
#   ON
#       EXTERNAL_VIEW.<campo_view> = <view_join>.<campo_join>
#
# 5) Para casos em que é necessária uma query específica, a especificação deve ser
# no seguinte formato:
#
# {
#   "<campo_local>":{
#                       "select":"",
#                       "from":"",
#                       "where":"",
#                       "group_by":"",
#                        "model_fk":"",
#                        "campo_fk":"",
#                   }
# }
#
# Nesse caso, nenhum dos parâmetros deve incluir o comando SQL ao qual se refere.
# Por exemplo, os parâmetros devem ser passados dessa forma:
#
# {
#   "delegacia":{
#                "select":"pr_tab_delegacia.id_tab_delegacia",
#                "from":"pr_tab_delegacia INNER JOIN br_tab_cidade ON br_tab_cidade.fk_id_tab_delegacia = pr_tab_delegacia.id_tab_delegacia, pr_pfj_endereco",
#                "where": "pr_pfj_endereco.cep between br_tab_cidade.cep and br_tab_cidade.cepfim AND pr_pfj_endereco.fk_id_pj_registro = pr_pj_registro.id_pj_registro",
#                "model_fk":"Delegacia",
#                "campo_fk":"id_federal"
#    }
# }
#
# No parâmetro "from", não é preciso passar a EXTERNAL_VIEW, pois a mesma já será incluída.




# Ordem com que é feito o update
# A ordem dos models listada faz diferença. Os models estão listados de acordo com a dependência que possuem.
# Os models listados só podem ter foreign key com models posicionados à sua esquerda.
SYNC_ORDER = ["Ramo","Classe","Delegacia", "InfoPJ","Empresa","EmpresaRamo","EmpresaInfoPJ","EmpresaDelegacia","UserProfissional","EmpresaProfissional"]

# Ordem com que são excluídos itens removidos.
# Models que não estejam nessa lista nunca serão excluídos.
DELETE_ORDER = ["EmpresaRamo","EmpresaInfoPJ","EmpresaDelegacia","EmpresaProfissional"]

# Nome do campo nos models internos que reflete o pk da view externa
VIEW_ID_FIELD = "id_federal"

# Nome da aplicação sendo sincronizada
APP_SYNC = "accounts"

# Mapeamento de integração
SYNC_CONFIG = {
    "Ramo": {
        "EXTERNAL_VIEW":"br_tab_ramo3",
        "FIELD_MAP": {
                       "id_federal":{"select":"GROUP_CONCAT(id_tab_ramo3)","group_by":"descricao"},# "id_federal":"id_tab_ramo3",
                       "descricao":"descricao"
        }
    },
    "Classe": {
        "EXTERNAL_VIEW":"br_tab_classe",
        "FIELD_MAP":{
                       "id_federal":"id_tab_classe",
                       "sigla":"sigla",
                       "descricao":"descricao"
        }
    },
    "Delegacia":{
         "EXTERNAL_VIEW":"pr_tab_delegacia",
         "FIELD_MAP":{
                       "id_federal":"id_tab_delegacia",
                       "descricao":"descricao"
          }

    },
    "InfoPJ":{
         "EXTERNAL_VIEW":"pr_pfj_endereco",
         "FIELD_MAP":{
                       "id_federal":"id_pfj_endereco",
                       "cidade":"cidade",
                       "email_empresa":"email"
          }

    },
    "Empresa":{
        "EXTERNAL_VIEW":"pr_pj_registro",
        "FIELD_MAP":{
                       "id_federal":"id_pj_registro",
                       "cnpj":"cnpj",
                       "nro_crmv":"pj_registro",
                       "nome_fantasia":"nome_fantasia",
                       "razao_social":"razao_social",
                       "classe_id":{
                                    "campo_view":"pj_classe",
                                    "model_fk":"Classe",
                                    "campo_fk":"sigla"
                       }
        }
    },
    "EmpresaRamo":{
        "EXTERNAL_VIEW":"pr_pj_ramo_atividade",
        "FIELD_MAP":{
                       "id_federal":"id_pfj_ramo_atividade",
                       "empresa_id":{
                                    "campo_view":"fk_id_pj_registro",
                                    "model_fk":"Empresa",
                                    "campo_fk":"id_federal"
                       },
                       "ramo_id":{
                                "campo_view":"fk_id_tab_ramo3",
                                "model_fk":"Ramo",
                                "campo_fk":"id_federal__regex",
                                "campo_fk_format":"(^|,)%d($|,)",
                                "if_null":82

                       }
        }
    },
    "EmpresaInfoPJ":{
        "EXTERNAL_VIEW":"pr_pfj_endereco",
        "FIELD_MAP":{
                       "id_federal":"id_pfj_endereco",
                       "empresa_id":{
                                    "campo_view":"fk_id_pj_registro",
                                    "model_fk":"Empresa",
                                    "campo_fk":"id_federal"
                       },
                       "infopj_id":{
                                "campo_view":"id_pfj_endereco",
                                "model_fk":"InfoPJ",
                                "campo_fk":"id_federal"
                       }
        }
    },
    "EmpresaDelegacia":{
        "EXTERNAL_VIEW":"pr_pj_registro",
        "FIELD_MAP":{
                       "id_federal":"id_pj_registro",
                       "empresa_id":{
                                    "campo_view":"id_pj_registro",
                                    "model_fk":"Empresa",
                                    "campo_fk":"id_federal"
                       },
                       "delegacia_id":{
                                    "select":"pr_tab_delegacia.id_tab_delegacia",
                                    "from":"pr_tab_delegacia INNER JOIN br_tab_cidade ON br_tab_cidade.fk_id_tab_delegacia = pr_tab_delegacia.id_tab_delegacia, pr_pfj_endereco",
                                    "where": "pr_pfj_endereco.cep between br_tab_cidade.cep and br_tab_cidade.cepfim AND pr_pfj_endereco.fk_id_pj_registro = pr_pj_registro.id_pj_registro",
                                    "model_fk":"Delegacia",
                                    "campo_fk":"id_federal",
                                    "if_null":298
                        }
        }
    },
    "UserProfissional":{
        "EXTERNAL_VIEW":"pr_pf_inscricao",
        "FIELD_MAP":{
                        "id_federal":"id_pf_inscricao",
                        "nro_crmv":"pf_inscricao",
                        "first_name":"nome",
                        "classe_id":{
                                    "campo_view":"pf_classe",
                                    "model_fk":"Classe",
                                    "campo_fk":"sigla",
                        },
                        "cpf":"cpf"
        }
    },
    "EmpresaProfissional":{
        "EXTERNAL_VIEW":"pr_pj_rt",
        "FIELD_MAP":{
                        "id_federal":"id_pj_rt",
                        "dt_homologacao":"dt_homologacao",
                        "dt_final": "dt_final",
                        "empresa_id":{
                                    "campo_view":"fk_id_pj_registro",
                                    "model_fk":"Empresa",
                                    "campo_fk": "id_federal"
                        },
                        "profissional_id":{
                                            "campo_view":"fk_id_pf_inscricao",
                                            "model_fk":"UserProfissional",
                                            "campo_fk": "id_federal"
                        }
        }
    }
}