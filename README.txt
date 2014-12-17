
===================================================================================================================================================================================

E89 - SQL INTEGRATION

==================================================================================================================================================================================

O plugin E89 - SQL INTEGRATION permite sincronizar o banco de dados local de uma aplicação django com um banco de dados SQL externo. Isso é feito através de um mapeamento de cada campo dos models do banco de dados local com colunas de tabelas do banco de dados externo.

==================================================================================================================================================================================

Para utilizar o plugin de integração SQL, seguir os passos:

1) Instalar o plugin com pip

2) No arquivo settings.py, adicionar "e89_sql_integration" na lista de INSTALLED_APPS.

3) Inserir no arquivo settings.py as opções de configuração explicadas em sequência.

4) Inserir urls no arquivo urls.py:

    url(r'', include("e89_sql_integration.urls")),

A única url que será incluída é cron/update-local-db/.

5) Programar cronjob para realizar sincronização. A sincronização é ativada através de um post na view cron/update-local-db/. Para não permitir posts não autorizados, é necessário passar como parâmetro do post o "secret" da aplicação django. O "secret" é um código de números e letras único para cada aplicação e pode ser visto no arquivo settings.py. Assim, para ativar a sincronização, seria necessário executar o seguinte comando com curl:

    curl --data-urlencode 'secret=jt(p2f7%!4eqq@62=7ykc6_yk-**dz6-a2ym)ci)hc^++nkh*1' http://127.0.0.1:8000/cron/update-local-db/

ATENÇÃO: os dados do post DEVEM estar entre aspas simples e não aspas duplas, caso contrário há erro para símbolos como !.



OPÇÕES NO ARQUIVO settings.py
===============================


    INTEGRATION_EXTERNAL_DB_HOST
    -----------------------------

    IP de acesso ao banco de dados externo.

    Ex: INTEGRATION_EXTERNAL_DB_HOST = "156.220.84.117"


    INTEGRATION_EXTERNAL_DB_USER
    ----------------------------

    Usuário de acesso no banco de dados externo.

    Ex: INTEGRATION_EXTERNAL_DB_USER = "db_user"


    INTEGRATION_EXTERNAL_DB_PASSWORD
    --------------------------------

    Senha de acesso ao banco de dados externo.

    Ex: INTEGRATION_EXTERNAL_DB_PASSWORD = "minhasenha"


    INTEGRATION_EXTERNAL_DB_PORT
    ----------------------------

    Porta de acesso ao banco de dados externo.

    Ex: INTEGRATION_EXTERNAL_DB_PORT = 3306


    INTEGRATION_EXTERNAL_DB_NAME
    ----------------------------

    Nome do banco de dados que será acessado.

    Ex: INTEGRATION_EXTERNAL_DB_NAME = "database"


    INTEGRATION_SYNC_ORDER
    ----------------------

    Ordem com que é feito o update dos models envolvidos na integração. Essa deverá ser uma lista de strings com o nome de cada model na ordem em que deverão ser atualizados.
    A ordem dos models na lista faz diferença, de forma que devem ser listados de acordo com a dependência que possuem. Assim, cada model na lista só pode ter foreign key com models posicionados à sua esquerda.

    Ex: INTEGRATION_SYNC_ORDER = ["Ramo","Classe","Delegacia", "InfoPJ","Empresa","EmpresaRamo","EmpresaInfoPJ","EmpresaDelegacia","UserProfissional","EmpresaProfissional"]


    INTEGRATION_DELETE_ORDER
    ------------------------

    Ordem com que são excluídos itens de cada model. Models que não estejam nessa lista nunca são excluídos.

    Ex: INTEGRATION_DELETE_ORDER = ["EmpresaRamo","EmpresaInfoPJ","EmpresaDelegacia","EmpresaProfissional"]


    INTEGRATION_VIEW_ID_FIELD
    -------------------------

    Essa opção deve ser uma string que indica qual é o atributo presente em cada model a ser sincronizado que representa seu primary key na tabela do banco de dados externo.

    Ex: INTEGRATION_VIEW_ID_FIELD = "id_federal"


    INTEGRATION_APP_SYNC
    --------------------

    Nome da aplicação cujos models serão sincronizados com o banco externo.

    Ex: INTEGRATION_APP_SYNC = 'accounts'


    INTEGRATION_SYNC_CONFIG
    ------------------------

    Essa opção é mais complexa de ser especificada e define como é feito o mapeamento entre os models do banco de dados da aplicação django e do banco de dados externo. Esse é um dicionário que mapeia os campos de cada model com colunas de tabelas do banco de dados externo.

    O dicionário deverá ser montado da seguinte forma:

    {
      "Model_1": { < Mapeamento - Model_1 >},
      "Model_2": { < Mapeamento - Model_2 >},
      "Model_3": { < Mapeamento - Model_3 >},
      ...
    }

    O mapeamento de cada model também é um dicionário, o qual deverá possuir dois keys:

        EXTERNAL_VIEW: nome da view (ou tabela) que contém os dados que serão acessados para popular o model.
        FIELD_MAP: mapeamento propriamente dito entre os campos do model e colunas da view (ou tabela).

    Existem 5 formas distintas para mapear os campos entre os bancos de dados, cada uma deve ser utilizada de acordo com a estrutura dos dados no banco de dados externo. Abaixo são explicadas cada uma das formas separadamente:

        1) Para os casos em que a correspondência entre os campos é direta, a lógica do dicionário
        FIELD_MAP é montada da seguinte forma:

            {
                "<campo_local>":"<campo_view>"
            }

        Nessa configuração, a string <campo_local> refere-se a um atributo de um model e a string <campo_view> refere-se a uma coluna na view ou tabela sendo pesquisada (a qual foi definida no key EXTERNAL_VIEW). Essa forma de mapeamento é convertida em uma query como abaixo:

            SELECT
                <campo_view> AS <campo_local>
            FROM
                EXTERNAL_VIEW


        EXEMPLO:
        --------
            Por exemplo, considere a situação em que se deseja sincronizar um model chamado "Car", sabendo que o atributo "brand" do model é armazenado no banco externo em uma view denominada "CAR_DATA" na coluna "car_brand" e, além disso, o primary key do objeto no banco externo ("pk_car") é armazenado no atributo "id_ext" do model django. Nesse caso, o mapeamento seria feito da seguinte forma:

                INTEGRATION_SYNC_CONFIG = {
                    ...
                    "Car": {
                        "EXTERNAL_VIEW":"CAR_DATA",
                        "FIELD_MAP":{
                            "id_ext":"pk_car",
                            "brand":"car_brand"
                        }
                    }
                }

        2) Para os casos em que a correspondência entre os campos é direta, porém é necessária alguma forma de conversão dos dados, o dicionário FIELD_MAP deve ser montado da seguinte forma:

            {
                "<campo_local>":{
                    "campo_view":"<campo_view>",
                    "func_convert": lambda v: return v
                }
            }

        A função de conversão deverá receber um único parâmetro, o qual é o valor do campo como representado no banco de dados externo, e deve retornar a nova representação do campo.

        EXEMPLO
        -------
            Retomando o exemplo anterior do model "Car", caso queiramos converter o ano de fabricação do automóvel (armazenado na coluna "car_year" no banco externo) em um objeto datetime, poderíamos realizar o mapeamento da seguinte forma:

                INTEGRATION_SYNC_CONFIG = {
                    ...
                    "Car": {
                        "EXTERNAL_VIEW":"CAR_DATA",
                        "FIELD_MAP":{
                            "id_ext":"pk_car",
                            "brand":"car_brand",
                            "year":{
                                "campo_view":"car_year",
                                "func_convert": lambda v: return dt.datetime(v,1,1)
                            }
                        }
                    }
                }

        3) Para os casos em que é há uma foreign key entre dois models, é preciso buscar o id (no banco de dados local) da foreign key representada no banco de dados externo. Nesse caso, o mapeamento é feito da seguinte forma:

            {
                "<campo_local>":{
                    "campo_view":"<campo_view>",
                    "model_fk":"<model_fk>",
                    "campo_fk":"<campo_fk>",
                    "campo_fk_format":"[^,]%s[$,]",  # (Opcional)
                    "if_null":82  $ (Opcional)
                }
            }
        Nesse caso, tem se os seguintes parâmetros:
            <campo_local>: atributo que representa a foreign key. Esse atributo deve terminar com "_id".
            <campo_view>: coluna da tabela do banco de dados externo que representa a foreign key.
            <model_fk>: nome do model com o qual se tem uma foreign key.
            <campo_fk>: normalmente é o atributo que representa o primary key da foreign key no banco de dados externo.
            <campo_fk_format>: string de formatação para alterar o valor armazenado na coluna do banco de dados externo (<campo_view>) antes que seja feita uma query no banco local (útil para utilizar regular expressions - nesse caso o <campo_fk> deve terminar em "__regex"). Parâmetro opcional.
            <if_null>: caso o valor encontrado para a coluna "campo_view" seja nulo, a busca pelo foreign key é feita utilizando o valor do parâmetro <if_null>.

        Para esse terceiro formato, seria feita a seguinte query:

            SELECT
                <campo_view> AS <campo_fk>
            FROM
                EXTERNAL_VIEW


        Em seguida seria buscado o id da instância do modelo <model_fk> pelo parâmetro <campo_fk>. Caso o parâmetro "campo_fk_format" for fornecido, o valor utilizado para a busca será formatado pela string passada.

        Sendo assim, em seguida é executado o seguinte código:

        <campo_local> = <model_fk>.objects.values("id").get(<campo_fk>=<valor_select>) ou <model_fk>.objects.values("id").get(<campo_fk>="<campo_fk_format>"%<valor_campo_view>)

        Como mencionado, no parâmetro <campo_fk> é possível utilizar operações de query do django como __contains ou __regex.

        ATENÇÃO: Sempre colocar "_id" junto ao nome do campo local, pois o campo com nome igual ao foreign key não é um atributo do objeto em si, mas apenas uma property.

        EXEMPLO
        -------

            Considere a situação a seguir, em que estamos sincronizando os dados do Model_1, o qual possui uma foreign key com o Model_2. No banco de dados local, a estrutura dos dois models pode ser representada da seguinte forma:

                Model_1         |    Model_2
                ----------------|-------------
                id              |    id
                id_ext          |    id_ext
                model2_id       |

            Já no banco de dados externo, a mesma estrutura é representada da seguinte maneira:

                Externo_1       |    Externo_2
                ----------------|-------------
                pk              |    pk
                fk_ext2         |

            Para poder mapear essa relação corretamente, a configuração deve ser feita da seguinte forma:

                INTEGRATION_SYNC_CONFIG = {
                    ...
                    "Model_1": {
                        "EXTERNAL_VIEW":"Externo_1",
                        "FIELD_MAP":{
                            "id_ext":"pk",
                            "model2_id":{
                                "campo_view":"fk_ext2",
                                "model_fk":"Model_2",
                                "campo_fk":"id_ext",
                            }
                        }
                    }
                }


        4) Para casos em que o model possui uma foreign key para uma view (ou tabela) do banco remoto que não é representada internamente por nenhum model, o FIELD_MAP deve ser montado da seguinte maneira:

            {
                "<campo_local>":{
                    "campo_view":"<campo_view>",
                    "view_join":"<view_join>",
                    "campo_join":"<campo_fk>",
                    "campo_desejado":"<campo_desejado>"
                }
            }

        Nesse caso, o mapeamento será convertido em uma query da seguinte forma:

        SELECT
            <view_join>.<campo_desejado> as <campo_local>
        FROM
            EXTERNAL_VIEW
        INNER JOIN
            <view_join>
        ON
            EXTERNAL_VIEW.<campo_view> = <view_join>.<campo_join>


        EXEMPLO
        -------
            Retomando o exemplo do model "Car", considere a situação em que, no banco de dados externo, existe uma outra tabela denominada "CAR_PARTS". As duas tabelas são conectadas através da coluna "fk_parts" na tabela "CAR_DATA". Queremos extrair o valor da coluna "tires" na tabela "CAR_PARTS", a qual indica a marca dos pneus do automóvel. Em nosso model da aplicação django, esse valor é salvo como um atributo do model e, assim, a tabela "CAR_DATA" não é representada internamente.

                 BANCO LOCAL                            BANCO EXTERNO

                     Car        |                  CAR_DATA     |    CAR_PARTS
                ----------------|                -------------- | ---------------
                id              |                 pk_car        | pk_part
                id_ext          |                 fk_parts      | tires
                tires           |                               |


            Nessa situação, a configuração seria feita da seguinte forma:

                INTEGRATION_SYNC_CONFIG = {
                    ...
                    "Car": {
                        "EXTERNAL_VIEW":"CAR_DATA",
                        "FIELD_MAP":{
                            "id_ext":"pk_car",
                            "tires": {
                                "campo_view":"fk_parts",
                                "view_join":"CAR_PARTS",
                                "campo_join":"pk_part",
                                "campo_desejado":"tires"
                            }
                        }
                    }
                }


        5) Para casos em que é necessária uma query específica para obter um dado do banco externo, a especificação deve ser no seguinte formato:

            {
                "<campo_local>":{
                    "select":"",
                    "from":"",
                    "where":"",
                    "group_by":"",
                    "model_fk":"",
                    "campo_fk":"",
                }
            }

        Nesse caso, nenhum dos parâmetros deve incluir o comando SQL ao qual se refere. Além disso, no parâmetro "from" não é preciso passar a EXTERNAL_VIEW, pois a mesma já será incluída. Nos casos em que os valores <model_fk> e <campo_fk> são fornecidos, o valor obtido através da query é utilizado para buscar o id do model <model_fk> através de uma busca através do <campo_fk>. Essa forma de configuração é utilizada quando no banco local existe uma foreign key entre 2 models que não possuem uma foreign key representada no banco externo e, assim, é necessário explicitar uma query que identifique a relação entre os objetos.


        EXEMPLO
        -------
            Considerando o exemplo do model "Car", vamos considerar a situação em que desejamos obter o número de vezes que cada automóvel foi vendido e armazenar esse valor no atributo "number_sales" em nosso model. No banco de dados externo, uma tabela chamada "CAR_SALES" armazena os dados de vendas de cada automóvel, sendo cada linha da tabela correspondente a uma venda. O que queremos é obter a contagem das linhas nessa tabela que se referem a um determinado automóvel.

                 BANCO LOCAL                            BANCO EXTERNO

                     Car        |                  CAR_DATA     |    CAR_SALES
                ----------------|                -------------- | ---------------
                id              |                 pk_car        | pk_sales
                id_ext          |                               | fk_car
                tires           |                               | price

            Nesse caso, a configuração seria feita da seguinte forma:

                INTEGRATION_SYNC_CONFIG = {
                    ...
                    "Car": {
                        "EXTERNAL_VIEW":"CAR_DATA",
                        "FIELD_MAP":{
                            "id_ext":"pk_car",
                            "number_sales": {
                                "select":"COUNT(CAR_SALES.pk_sales)",
                                "from":"CAR_SALES",
                                "where":"CAR_SALES.fk_car = CAR_DATA.pk_car",
                                "group_by":"CAR_SALES.pk_sales"
                            }
                        }
                    }
                }


