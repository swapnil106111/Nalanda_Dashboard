from contentusage.contentusagereport import BaseRoleAccess
from account.models import *
from account.constants import *
from sync_report.models import last_sync_date
from .sync_report import all_selected_data_mail, get_bit
from django.db.models import Max
import datetime
import json, time
from itertools import *
from datetime import date
from django.core.mail import send_mail
from django.contrib.auth.models import User



def sample():
	temp = UserRoleCollectionMapping.objects.values('user_id')
	temp = list(set([i['user_id'] for i in temp ]))
	for i in temp:
		if get_bit(i) != 1:
			temp.remove(i)

	for i in temp:
		data = User.objects.values('username','email').filter(id=i)
		email = data[0]['email']
		username = data[0]['username']
		t = all_selected_data_mail(i)
		text = 'Hello '+username+',\n'+"Please sync below servers which are not synced last from 20 days:\n\n"	
		for j in range(0,len(t),2):
			text = text + t[j] +" : "+ t[j+1] + "\n"
		text = text + "\n" + "Regards,\n" + "Nalanda"

		send_mail("Sync remainder mail", text, "nalandamande@gmail.com", [email])
		# send_mail("Sync remainder mail", text, "nalandamande@gmail.com", ["swap106111@gmail.com"])