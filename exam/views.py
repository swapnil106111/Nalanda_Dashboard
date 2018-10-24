from django.shortcuts import render, HttpResponse
from .exammetric import Exam_details, Exammetric
import json
from account.views import construct_response
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def get_exams(request):
	try:
		if request.method == 'POST':
			user = request.user
			body_unicode = request.body.decode('utf-8')
			data = json.loads(body_unicode)
			parent_level = data.get('parentLevel', -2)
			objSchoolDetails = Exam_details(user, parent_level)
			objSchoolData = objSchoolDetails.getPageData()
			response = construct_response(0, '', '', objSchoolData);
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
		else:
			response = construct_response(1111,'wrong request','wrong request','')
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
	except Exception as e:
		logger.error(e)

def get_exam_page_data(request):
	try:
		if request.method == 'POST':
			user = request.user
			body_unicode = request.body.decode('utf-8')
			data = json.loads(body_unicode)
			user_id = data.get('userID')
			startTimestamp = data.get('startTimestamp', 0)
			endTimestamp = data.get('endTimestamp', 0)
			if not user_id:
				response = construct_response(2001, '', '', {});
				response_text = json.dumps(response,ensure_ascii=False)
				return HttpResponse(response_text,content_type='application/json')
			objexam_metric = Exammetric(user_id, startTimestamp, endTimestamp)
			objexam_metric_data = objexam_metric.get_exam_metric_data()
			response = construct_response(0, '', '', objexam_metric_data);
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
		else:
			response = construct_response(1111,'wrong request','wrong request','')
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
	except Exception as e:
		logger.error(e)

def get_exam_metrics(request):
	if request.method == 'GET':
		return render(request,'exammetric.html',{})
	else:
		return HttpResponse()

