# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

urlpatterns = patterns('e89_sql_integration.views',
	(r'^cron/update-local-db/$', 'update_local_db'),
)