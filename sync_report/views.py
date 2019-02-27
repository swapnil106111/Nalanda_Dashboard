from django.shortcuts import render, HttpResponse
from .sync_report import getCities, getSyncData, get_user_content, get_bit
from .mail_send import sample
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
import json
from account.views import construct_response
import logging

logger = logging.getLogger(__name__)

@login_required(login_url='/account/login/')
def get_sync_report_school(request):
	try:
		if request.method == 'POST':
			user = request.user
			body_unicode = request.body.decode('utf-8')
			data = json.loads(body_unicode)
			parent_level = data.get('parentLevel', -2)
			cities = getCities()
			response = construct_response(0, '', '', cities)
			
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
		else:
			response = construct_response(1111,'wrong request','wrong request','')
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
	except Exception as e:
		logger.error(e)


@login_required(login_url='/account/login/')
def get_sync_data(request):
	try:
		if request.method == 'POST':
			user = request.user
			body_unicode = request.body.decode('utf-8')
			data = json.loads(body_unicode)
			user_id = request.user.id
			print("user_id",user_id)
			selected_city = data.get('selected_city')
			# startTimestamp = data.get('startTimestamp', 0)
			# endTimestamp = data.get('endTimestamp', 0)

			# if not user_id:
			# 	print("ALLLLLL")
			# 	response = construct_response(2001, '', '', {});
			# 	response_text = json.dumps(response,ensure_ascii=False)
			# 	return HttpResponse(response_text,content_type='application/json')
			temp_data = getSyncData(selected_city,user_id)
			# print(temp_data)
			data['rows'] = temp_data[0] 
			data['columns'] = get_user_content()
			data['bit'] = get_bit(user_id)
			print(str(temp_data[1]).replace("'","").replace("[","").replace("]","")+" school servers has not been synced last from 20 days.")
			if len(temp_data[1]) == 0:
				data['alert'] = "All servers are synced successfully."
			else:
				data['alert'] = (str(temp_data[1]).replace("'","").replace("[","").replace("]","")+" school servers has not been synced last from 20 days.")
			response = construct_response(0, '', '', data)
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
		else:
			response = construct_response(1111,'wrong request','wrong request','')
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
	except Exception as e:
		logger.error(e)


# Create your views here.
@login_required(login_url='/account/login/')
def get_sync_report(request):
	if request.method == 'GET':
		return render(request,'sync_report.html',{})
	else:
		return HttpResponse()

# @login_required(login_url='/account/login/')
def send_mail_alert(request):
	try:
		sample()
		# res = send_mail("hello swap", "how are you? Do sync.", "nalandamande@gmail.com", ["swap106111@gmail.com"])
		return HttpResponse("yes")
	except Exception as e:
		logger.error(e)
		print(e)
