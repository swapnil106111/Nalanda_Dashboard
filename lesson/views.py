from django.shortcuts import render, HttpResponse
from .lessonmastery import LessonDetails, LessonMastery
import json
# Create your views here.
from account.views import construct_response
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

@login_required(login_url='/account/login/')
def get_lessons(request):
	try:
		if request.method == 'POST':
			user = request.user
			body_unicode = request.body.decode('utf-8')
			data = json.loads(body_unicode)
			parent_level = data.get('parentLevel', -2)
			objSchoolDetails = LessonDetails(user, parent_level)
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


@login_required(login_url='/account/login/')
def get_lesson_page_data(request):
	try:
		if request.method == 'POST':
			user = request.user
			body_unicode = request.body.decode('utf-8')
			data = json.loads(body_unicode)
			lesson_id = data.get('lessonID')
			startTimestamp = data.get('startTimestamp', 0)
			endTimestamp = data.get('endTimestamp', 0)
			if not lesson_id:
				response = construct_response(2001, '', '', {});
				response_text = json.dumps(response,ensure_ascii=False)
				return HttpResponse(response_text,content_type='application/json')
			objlesson_mastery = LessonMastery(lesson_id, startTimestamp, endTimestamp)
			objlesson_mastery_data = objlesson_mastery.get_lesson_mastery_data()
			response = construct_response(0, '', '', objlesson_mastery_data);
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
		else:
			response = construct_response(1111,'wrong request','wrong request','')
			response_text = json.dumps(response,ensure_ascii=False)
			return HttpResponse(response_text,content_type='application/json')
	except Exception as e:
		logger.error(e)

@login_required(login_url='/account/login/')
def get_lesson_mastery(request):
	if request.method == 'GET':
		return render(request,'lessonmasteryreport.html',{})
	else:
		return HttpResponse()
