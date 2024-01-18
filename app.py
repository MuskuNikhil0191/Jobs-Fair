import certifi
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask import Flask,flash, render_template, request, redirect, send_from_directory, session, url_for
from flask_pymongo import PyMongo
import hashlib


import os
from bson import ObjectId
import bson
from random import randint  # Import the randint function from the random module

from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta


app = Flask(__name__)

app.secret_key = 'your_secret_key'  
try:
   
  CONNECTION_STRING = "mongodb+srv://nick:nick@data.kvylfse.mongodb.net/?retryWrites=true&w=majority"
  client = MongoClient(CONNECTION_STRING,tlsCAFile=certifi.where())
  print("Database connected")
  db = client.get_database('job-fair')

  client.server_info() #trigger exception if cannot connect to db
except Exception as e:
  print(e)
  print("Error -connect to db")
bcrypt = Bcrypt(app)


UPLOAD_FOLDER = 'resumes'


ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ... Other configurations and routes ...

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/',  methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        collection = db[role]
        print(role)
        user = collection.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = {'email': user['email'], 'role': role}
            if role == 'recruiters':
                return redirect(url_for('recruiter_dashboard'))
            elif role == 'companies':
                return redirect(url_for('company_dashboard'))
            elif role == 'applicants':
                return redirect(url_for('applicant_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
             flash('invalid details', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get user input from the form
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user_type = request.form.get('user_type')


        # Validate the user input
        if not name or not email or not mobile or not password or not confirm_password:
            return "Invalid input. Please fill in all fields."

        if password != confirm_password:
            return "Password and Confirm Password do not match."

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        if user_type == 'applicant':
                    applicants_collection = db['applicants']
                    applicants_collection.insert_one({
                        'name': name,
                        'email': email,
                        'mobile': mobile,
                        'password': hashed_password
                    })
        elif user_type == 'company':
                    applicants_collection = db['tem_companies']
                    applicants_collection.insert_one({
                        'name': name,
                        'email': email,
                        'mobile': mobile,
                        'password': hashed_password,
                        'status':'pending',
                    })
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/withdraw_applicant', methods=['POST'])
def withdraw_applicant():
    applications_collection = db['applications']
    if request.method == 'POST':
        application_id = request.form['application_id']
        print(application_id)
        application = applications_collection.find_one({'_id': ObjectId(application_id)})
        if application:
            applications_collection.update_one(
                {'_id': ObjectId(application_id)},
                {'$set': {'status': 'withdrawn'}}
            )

            # Redirect to a success page or any other page as needed
            return redirect('/view_history')  # Update the URL to your success page

    # Redirect to an error page if the application is not found or any other error occurs
    return redirect('/error')


@app.route('/profile_update')
def profile_update():
    return render_template('profile.html')



@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')



@app.route('/add_recruiter', methods=['POST'])
def add_recruiter():
    if request.method == 'POST':
        companies_collection=db['companies']
        user_email = session['user']['email']
        company = companies_collection.find_one({'email': user_email})
        print(company)
        user_name = company['name']

        # Get user input from the form
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate the user input
        if not name or not email or not password:
            return "Invalid input. Please fill in all fields."

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert the recruiter data into the recruiters collection
        recruiters_collection = db['recruiters']
        recruiters_collection.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'company' : user_name,
        })

        # Redirect to a success page or another route
        return redirect(url_for('company_dashboard'))

    # Handle other HTTP methods or redirect to the registration page
    return render_template('add_recruiter.html') 


@app.route('/adm_add_recruiter/<string:job_id>', methods=['POST'])
def adm_add_recruiter(job_id):
    if request.method == 'POST':
        companies_collection=db['companies']
        company = companies_collection.find_one({'_id': ObjectId(job_id)})
        user_name = company['name']
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate the user input
        if not name or not email or not password:
            return "Invalid input. Please fill in all fields."

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert the recruiter data into the recruiters collection
        recruiters_collection = db['recruiters']
        recruiters_collection.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'company' : user_name,
        })

        # Redirect to a success page or another route
        return redirect(url_for('admin_dashboard'))

    # Handle other HTTP methods or redirect to the registration page
    return render_template('add_recruiter.html')  # Assuming you have an HTML template for the form


@app.route('/add_recs')
def add_recs():
    return render_template('add_recs.html')


@app.route('/adm_add_recs/<string:job_id>')
def adm_add_recs(job_id):
    return render_template('adm_add_recs.html',job_id=job_id)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    applications_collection = db['applicants']
    
    if 'user' in session:
        user_email = session['user']['email']
        print(user_email)
        experience_years = request.form['experience_years']
        experience_sector = request.form['experience_sector']
        masters = request.form['masters']
        bachelors = request.form['bachelors']
        high_school = request.form['high_school']
        programming_languages_2 = request.form.getlist('programming_languages_2')
        certifications = request.form['certifications']
        awards = request.form['awards']
        if 'resume' in request.files:
            resume = request.files['resume']
            if resume and allowed_file(resume.filename):
                filename = secure_filename(resume.filename)
                resume.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                # Handle invalid file format or no file provided
                return "Invalid file format or no file provided."


        applications_collection.update_one(
            {'email': user_email},
            {
                '$set': {
                    'experience_years': experience_years,
                    'experience_sector': experience_sector,
                    'masters': masters,
                    'bachelors': bachelors,
                    'high_school': high_school,
                    'programming_languages_2': programming_languages_2,
                    'certifications': certifications,
                    'awards': awards,
                    'resume_filename': filename  # Add the filename to the update
                }
            }
        )

        return redirect(url_for('applicant_dashboard'))
    else:
        return redirect(url_for('login')) 

@app.route('/comp_register', methods=['POST'])
def comp_register():
    companies_collection = db['tem_companies']
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        location = request.form['location']
        industry = request.form['industry']
        password = request.form['password']
        user_type = request.form['user_type']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')


        # Create a document with the form data
        company_data = {
            'name': name,
            'email': email,
            'mobile': mobile,
            'location': location,
            'industry': industry,
            'password': hashed_password,
            'user_type': user_type
        }

        # Insert the document into the companies collection
        companies_collection.insert_one(company_data)
        return redirect('/')


@app.route('/browse')
def browse():
    jobs_collection =db['jobs']
    job_openings = jobs_collection.find({'openings': {'$gt': 0}})
    return render_template('browse.html',job_openings=job_openings)

@app.route('/register_company')
def register_company():
    return render_template('register_company.html')


@app.route('/approve_comp', methods=['POST'])
def approve_comp():
    tem_comp=db['tem_companies']
    companies=db['companies']
    tem_id = request.form['application_id']
    company_to_approve = tem_comp.find_one({'_id': ObjectId(tem_id)})
    companies.insert_one(company_to_approve)
    return render_template('register_company.html')

@app.route('/admin_app_comp')
def admin_app_comp():
    companies_collection=db['tem_companies']
    all_companies = list(companies_collection.find())
    return render_template('approve_comp.html',all_companies=all_companies)



@app.route('/manage_recs')
def manage_recs():
    companies_collection=db['companies']
    recruiters_col=db['recruiters']
    user_email = session['user']['email']
    company = companies_collection.find_one({'email': user_email})
    name=company['name']
    company = recruiters_col.find({'company': name})
    return render_template('manage_recs.html',company=company)

@app.route('/adm_manage_recs/<string:job_id>')
def adm_manage_recs(job_id):
    print(job_id)
    companies_collection=db['companies']
    recruiters_col=db['recruiters']
    company = companies_collection.find_one({'_id': ObjectId(job_id)})
    name=company['name']
    company = recruiters_col.find({'company': name})
    return render_template('manage_recs.html',company=company)



@app.route('/del_rec', methods=['POST'])
def del_rec():
    recruiters_collection = db['recruiters']
    if request.method == 'POST':
        recruiter_id = request.form['application_id']
        recruiter = recruiters_collection.find_one({'_id': ObjectId(recruiter_id)})
        if recruiter:
            recruiters_collection.delete_one({'_id': ObjectId(recruiter_id)})
            role=session['user']['role']
            if role=='admin':
                return redirect('/adm_view_comp')
            return redirect('/manage_recs')
        


@app.route('/logout')
def logout():
    # Clear the session data
    session.pop('user', None)

    # Redirect to the login page or any other desired page after logout
    return redirect(url_for('home'))


@app.route('/job_details/<string:job_id>')
def job_details(job_id):
    jobs_collection =db['jobs']
    job_object_id = ObjectId(job_id)
    job_details = jobs_collection.find_one({'_id': job_object_id})
    return render_template('job_application.html',job_details=job_details)



@app.route('/view_resume/<string:can_id>')
def view_resume(can_id):
    applicants=db['applicants']
    candidate = applicants.find_one({"_id": ObjectId(can_id)})
    filename=candidate['resume_filename']
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/submit_application', methods=['POST'])
def submit_application():

    applications = db['applications']
    applicants = db['applicants']
    if request.method == 'POST':
        full_name = request.form['fullName']
        jobid = request.form['jobid']
        cv = request.form['coverLetter']
        user_email = session['user']['email']
        print(user_email)
        if not user_email:
            return redirect(url_for('login')) 
        user = applicants.find_one({'email': user_email})
        if not user:
            return "User not found!"
        user_id = str(user['_id'])
        application_data = {
                    'user_id': user_id,
                    'jobid': jobid,
                    'full_name': full_name,
                    'status': 'applied',
                    'cv':cv,
        }
        applications.insert_one(application_data)
        return redirect(url_for('browse'))


@app.route('/submit_job', methods=['POST'])
def submit_job():
    jobs_collection=db['jobs']
    companies_collection =db['companies']
    job_title = request.form.get('jobTitle')
    job_description = request.form.get('jobDescription')
    experience = request.form.get('experience')
    skills = request.form.getlist('skills[]')
    pay_per_hour = request.form.get('payPerHour')
    location = request.form.get('location')
    openings = int(request.form.get('openings'))
    user_email = session['user']['email']
    company = companies_collection.find_one({'email': user_email})
    user_name = company['name']
    job_posting = {
        'jobTitle': job_title,
        'jobDescription': job_description,
        'experience': experience,
        'skills': skills,
        'payPerHour': pay_per_hour,
        'location': location,
        'openings': openings,
        'usermail': user_email,
        'username': user_name,

    }
    jobs_collection.insert_one(job_posting)
    return redirect(url_for('comp_view_applications'))

@app.route('/post_job')
def post_job():
    return render_template('post_job.html')



@app.route('/view_comp_appl')
def view_comp_appl():
    companies_collection = db['temp_companies']
    all_companies = list(companies_collection.find())
    return render_template('view_comp_appl.html',all_companies=all_companies)

@app.route('/company_details/<company_id>')
def company_details(company_id):
       return render_template('adm_viw_comp.html', company_id=company_id)

@app.route('/adm_view_comp')
def adm_view_comp():
    companies_collection = db['companies']
    all_companies = list(companies_collection.find())
    print(all_companies)
    return render_template('adm_view_companies.html', companies=all_companies)



@app.route('/view_history')
def view_history():
    user_email = session['user']['email']
    user = db['applicants'].find_one({'email': user_email})
    user_id = str(user['_id'])
    user_applications = db['applications'].find({'user_id': user_id})

    applications_data = []
    for application in user_applications:
        job_id = str(application['jobid'])

        # Find the job details from the 'jobs' collection
        job_details = db['jobs'].find_one({'_id': ObjectId(job_id)})

        if job_details:
            # Combine application and job details into a dictionary
            app_data = {
                'application': application,
                'job': job_details
            }
            
            # Append the combined data to the list
            applications_data.append(app_data)

    # Pass the list to the HTML template
    return render_template('application_history.html',applications_data=applications_data)


@app.route('/comp_view_applications')
def comp_view_applications():
    jobs_collection=db['jobs']
    companies_collection =db['companies']
    user_email = session['user']['email']
    company = companies_collection.find_one({'email': user_email})
    user_name = company['name']
    jobs_with_username = jobs_collection.find({'username': user_name})
    num = randint(1, 5)

    return render_template('comp_posted_jobs.html',job_openings=jobs_with_username,num=num)


@app.route('/adm_comp_view_applications/<string:job_id>')
def adm_comp_view_applications(job_id):
    jobs_collection=db['jobs']
    companies_collection =db['companies']
    company = companies_collection.find_one({'_id': ObjectId(job_id)})
    user_name = company['name']
    jobs_with_username = jobs_collection.find({'username': user_name})
    num = randint(1, 5)

    return render_template('comp_posted_jobs.html',job_openings=jobs_with_username,num=num)


@app.route('/rec_view_applications')
def rec_view_applications():
    jobs_collection=db['jobs']
    recruiters =db['recruiters']
    user_email = session['user']['email']
    recr = recruiters.find_one({'email': user_email})
    comp = recr['company']
    jobs_with_username = jobs_collection.find({'username': comp})
    return render_template('rec_posted_jobs.html',job_openings=jobs_with_username)

@app.route('/comp_view_applications_2/<string:job_id>')
def comp_view_applications_2(job_id):
    jobs_collection = db['jobs']
    applications = db['applications']
    job_object_id = ObjectId(job_id)
    job_applications = applications.find({
    'jobid': str(job_object_id),
    'status': {'$in': ['shortlisted', 'hired']}
})
    job_applications = list(job_applications)

    return render_template('comp_view_applications.html', job_applications=job_applications)


@app.route('/adm_comp_view_applications_2/<string:job_id>')
def adm_comp_view_applications_2(job_id):
    jobs_collection = db['jobs']
    applications = db['applications']
    job_object_id = ObjectId(job_id)
    job_applications = applications.find({
    'jobid': str(job_object_id),
    'status': {'$in': ['shortlisted', 'hired']}
})
    job_applications = list(job_applications)

    return render_template('comp_view_applications.html', job_applications=job_applications)



@app.route('/rec_view_applications_2/<string:job_id>')
def rec_view_applications_2(job_id):
    jobs_collection = db['jobs']
    applications = db['applications']
    job_object_id = ObjectId(job_id)
    job_applications = applications.find({'jobid': str(job_object_id)})
    job_applications = list(job_applications)

    return render_template('rec_view_applications.html', job_applications=job_applications)




@app.route('/hire_applicant', methods=['POST'])
def hire_applicant():
    applications = db['applications']
    if request.method == 'POST':
        application_id = request.form.get('application_id')
        job_id = request.form.get('job_id')
        user_id = request.form.get('user_id')

        # Update the application status to 'hired'
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': 'hired'}}
        )

        jobs = db['jobs']
        job = jobs.find_one({'_id': ObjectId(job_id)})

        if job and job['openings'] > 0:
            jobs.update_one(
                {'_id': ObjectId(job_id)},
                {'$inc': {'openings': -1}}
            )

        role = session['user']['role']
        if role == 'admin':
            return redirect(url_for('adm_view_comp'))
        # Add additional logic if needed, e.g., update job openings, notify the user, etc.

        return redirect(url_for('comp_view_applications'))  # Redirect to a success page or update job openings

    return render_template('error_page.html', message='Invalid request')



@app.route('/short_applicant', methods=['POST'])
def short_applicant():
    applications = db['applications']
    if request.method == 'POST':
        application_id = request.form.get('application_id')
        job_id = request.form.get('job_id')
        user_id = request.form.get('user_id')

        # Update the application status to 'hired'
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': 'shortlisted'}}
        )


        # Add additional logic if needed, e.g., update job openings, notify the user, etc.

        return redirect(url_for('rec_view_applications'))  # Redirect to a success page or update job openings

    return render_template('error_page.html', message='Invalid request')

@app.route('/reject_applicant', methods=['POST'])
def reject_applicant():
    applications = db['applications']
    if request.method == 'POST':
        application_id = request.form.get('application_id')
        job_id = request.form.get('job_id')
        user_id = request.form.get('user_id')

        # Update the application status to 'rejected'
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': 'rejected'}}
        )
        role = session['user']['role']
        if role == 'admin':
            return redirect(url_for('adm_view_comp'))
    
        return redirect(url_for('comp_view_applications'))  # Redirect to a success page or perform additional actions

    return render_template('error_page.html', message='Invalid request')

@app.route('/rec_reject_applicant', methods=['POST'])
def rec_reject_applicant():
    applications = db['applications']
    if request.method == 'POST':
        application_id = request.form.get('application_id')
        job_id = request.form.get('job_id')
        user_id = request.form.get('user_id')

        # Update the application status to 'rejected'
        applications.update_one(
            {'_id': ObjectId(application_id)},
            {'$set': {'status': 'rejected'}}
        )
    
        return redirect(url_for('rec_view_applications'))  # Redirect to a success page or perform additional actions

    return render_template('error_page.html', message='Invalid request')


@app.route('/view-Candidate/<string:can_id>')
def view_candidate(can_id):
    applicants=db['applicants']
    candidate = applicants.find_one({"_id": ObjectId(can_id)})
    return render_template('view_candidate.html',candidate=candidate)

@app.route('/recruiter-dashboard')
def recruiter_dashboard():
    return render_template('recruiter_dashboard.html')

@app.route('/applicant-dashboard')
def applicant_dashboard():
    return render_template('applicant_dashboard.html')

@app.route('/company-dashboard')
def company_dashboard():
    return render_template('company_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)



#flask --app app.py --debug run 