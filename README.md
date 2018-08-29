# Nalanda Dashboard

## What is Nalanda Dashboard?
    A software system called Nalnanda Visualizer(dashboard) is used to track the progress of the Nalanda project 
    using the data gathered from Kolibri server. It's used to show the progress of student,class and schools 
    based on the different metrics e,g. correct questions, masterd topics, attempted questions etc.. 
    In Nalanda visualizer we are showing role based data, based on the user who have access the school or class.
    Currently we are done with different metrics as mentioned below:-
    
      1. Mastery Level Metrics
      2. Content Usage Metrics
      3. User Session Metrics
      4. Lesson Metrics
      
## Steps to setup Nalanda Dashboard:
1. Clone repo into your directory:

    https://github.com/nalandaproject/Nalanda_Dashboard.git
    
2. Create virtual envirinment using python3

    `virtualenv -p python3 envname`
    
3. Activate the virtual environment you have created
4. Install packages using `pip install -r requirement.txt`
5. Then create a local_setting.py file for your Django application which has the database settings.
    
    Please refer this link to install mysql database for Django application
    https://dev.mysql.com/doc/refman/8.0/en/installing.html
6. Then try to run the application : `python manage.py runserver`
7. You directly access it using http://127.0.0.1:8000/account/login/
