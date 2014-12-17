# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.core.exceptions import PermissionDenied
import e89_sql_integration.integration_tools
import sys

@csrf_exempt
def update_local_db(request):
	''' Para atualizar o banco, fazer post com cUrl:
		curl --data-urlencode 'secret=jt(p2f7%!4eqq@62=7ykc6_yk-**dz6-a2ym)ci)hc^++nkh*1' http://127.0.0.1:8000/cron/update-local-db/

		ATENÇÃO: os dados do post DEVEM estar entre aspas simples e não aspas duplas, caso contrário há erro para símbolos como !.
	'''

	if request.method == "POST":
		if request.POST.get('secret','') != settings.SECRET_KEY:
			raise PermissionDenied()

		tempo_total = e89_sql_integration.integration_tools.update_models()

		return HttpResponse('Tempo total = %f s'%(tempo_total))

	return HttpResponse('')
