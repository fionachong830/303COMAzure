from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, make_response, send_file
import pdfkit
from flask_bootstrap import Bootstrap
import pymysql
import os
from flask_mail import Mail, Message
import pandas as pd
import mysql.connector 
from distutils.log import debug
from fileinput import filename
from datetime import date
from mysql.connector import errorcode
from azure.storage.fileshare import ShareServiceClient, ShareFileClient
from azure.storage.blob import BlobServiceClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pymysql.err import InterfaceError

app = Flask(__name__)

connect_str = os.environ.get('AZURE_STORAGEFILE_CONNECTIONSTRING')
# retrieve the connection string from the environment variable

container_incomeexpenses = "incomeexpenses" # container name in which images will be store in the storage account

blob_service_client_incomeexpenses = BlobServiceClient.from_connection_string(conn_str=connect_str) # create a blob service client to interact with the storage account
try:
    container_client_incomeexpenses = blob_service_client_incomeexpenses.get_container_client(container=container_incomeexpenses) # get container client to interact with the container in which images will be stored
    container_client_incomeexpenses.get_container_properties() # get properties of the container to force exception to be thrown if container does not exist
except Exception as e:
    container_client_incomeexpenses = blob_service_client_incomeexpenses.create_container(container_incomeexpenses) # create a container in the storage account if it does not exist

container_inventory = "inventory" # container name in which images will be store in the storage account

blob_service_client_inventory = BlobServiceClient.from_connection_string(conn_str=connect_str) # create a blob service client to interact with the storage account
try:
    container_client_inventory = blob_service_client_inventory.get_container_client(container=container_inventory) # get container client to interact with the container in which images will be stored
    container_client_inventory.get_container_properties() # get properties of the container to force exception to be thrown if container does not exist
except Exception as e:
    container_client_inventory = blob_service_client_inventory.create_container(container_inventory) # create a container in the storage account if it does not exist
container_project = "project" # container name in which images will be store in the storage account

blob_service_client_project = BlobServiceClient.from_connection_string(conn_str=connect_str) # create a blob service client to interact with the storage account
try:
    container_client_project = blob_service_client_project.get_container_client(container=container_project) # get container client to interact with the container in which images will be stored
    container_client_project.get_container_properties() # get properties of the container to force exception to be thrown if container does not exist
except Exception as e:
    container_client_project = blob_service_client_project.create_container(container_project) # create a container in the storage account if it does not exist

app.config['SECRET_KEY'] = 'top-secret!'
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = os.environ.get('SENDGRID_API_KEY')
app.config['MAIL_DEFAULT_SENDER'] = 'testingtestinguat2@gmail.com'
os.environ.get('MAIL_DEFAULT_SENDER')
mail = Mail(app)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2324 Sem2/303COM/303 try/static/Project'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOAD_FOLDER_INVENTORY = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2324 Sem2/303COM/303 try/static/Inventory'
app.config['UPLOAD_FOLDER_INVENTORY'] = UPLOAD_FOLDER_INVENTORY
UPLOAD_FOLDER_IE = '/Users/fionachong/Library/CloudStorage/OneDrive-個人/2324 Sem2/303COM/303 try/static/IE'
app.config['UPLOAD_FOLDER_IE'] = UPLOAD_FOLDER_IE

bootstrap = Bootstrap(app)

try:
   connection = pymysql.connect(user=os.environ.get('AZURE_MYSQL_USER'), password=os.environ.get('AZURE_MYSQL_PASSWORD'), host=os.environ.get('AZURE_MYSQL_HOST'), port=3306, database="FYP_FIONA", ssl_ca="DigiCertGlobalRootCA.crt.pem", ssl_disabled=False, local_infile = 1, cursorclass=pymysql.cursors.DictCursor)
   print("Connection established")
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with the user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  cursor = connection.cursor()
'''
connection = pymysql.connect(host = 'localhost', 
    user = 'root',
    password = 'fiona0830', 
    db = 'FYP_FIONA', 
    local_infile = 1,
    cursorclass=pymysql.cursors.DictCursor)
'''
conn = mysql.connector.connect (
    user = os.environ.get('AZURE_MYSQL_USER'), 
    password = os.environ.get('AZURE_MYSQL_PASSWORD'), 
    host = os.environ.get('AZURE_MYSQL_HOST'),
    db = 'FYP_FIONA', 
    ssl_ca="DigiCertGlobalRootCA.crt.pem")

def sendemail(email, subject, message):
    msg = Message(
        subject=subject,
        recipients=[email],
        html=message
        )
    mail.send(msg)    

def send_email(subject, sender, recipient, content):
    message = Mail(
       from_email=sender,
       to_emails=recipient,
       subject=subject,
       html_content=content
       )
    try:
       sg = SendGridAPIClient(app.config['SENDGRID_API_KEY'])
       response = sg.send(message)
       print('Email sent successfully')
    except Exception as e:
        print('Error sending email:', e)

def checkLoginStatus(id): #new
    with connection.cursor() as cursor:    
        sql = 'SELECT LoginStatus from tbl_UserManagement WHERE UserID={id}'
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall()
        for e in data:
            if e['LoginStatus']== 1:
                return True
            else: 
                return False 

def checkCustomerLoginStatus(id): #new
    with connection.cursor() as cursor:   
        sql = 'SELECT LoginStatus from tbl_Customer WHERE CustomerID={id}'
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall()
        for e in data:
            if e['LoginStatus']== 1:
                return True
            else: 
                return False 

def getUserInfo(id): #new
    with connection.cursor() as cursor:
        sql = 'SELECT * from tbl_UserManagement WHERE UserID={id}'
        cursor.execute(sql.format(id=id))
        user = cursor.fetchall()
        return user

def getRole(id):
    with connection.cursor() as cursor:
        sql = 'SELECT Role from tbl_UserManagement WHERE UserID={id}'
        cursor.execute(sql.format(id=id))
        data = cursor.fetchall()
        for i in data:
            Role = i['Role']
        return Role

def getCustomerInfo(id): #new
    with connection.cursor() as cursor:
        sql = 'SELECT * from tbl_Customer WHERE CustomerID={id}'
        cursor.execute(sql.format(id=id))
        user = cursor.fetchall()
        return user

def getProjectStatus(ProjectID):
    with connection.cursor() as cursor:
        sql = 'SELECT ProjectStatus from tbl_Project WHERE ProjectID={ProjectID}'
        cursor.execute(sql.format(ProjectID=ProjectID))
        data = cursor.fetchall()
        for i in data:
            ProjectStatus = i['ProjectStatus']
        return ProjectStatus

def updateActivityStatus():
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM tbl_Activity WHERE ActivityStatus="New" or ActivityStatus="In Progress"')
        activity = cursor.fetchall()
        for i in activity:
            if i["ActivityStartDate"] <= date.today():
                updatesql='UPDATE tbl_Activity SET ActivityStatus="In Progress" WHERE ActivityID={ActivityID}'
                cursor.execute(updatesql.format(ActivityID=i["ActivityID"]))
                connection.commit()
            if i["ActivityEndDate"] < date.today():
                updatesql='UPDATE tbl_Activity SET ActivityStatus="Finished" WHERE ActivityID={ActivityID}'
                cursor.execute(updatesql.format(ActivityID=i["ActivityID"]))
                connection.commit()

@app.route('/send_email')
def send_test_email():
    messages = Mail(
        from_email='testingtestinguat2@gmail.com',
        to_emails='fionachong830@gmail.com',
        subject='Sending with Twilio SendGrid is Fun',
        html_content='<strong>and easy to do anywhere, even with Python</strong>')
    try:
        sg = SendGridAPIClient('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')
        response = sg.send(messages)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

@app.route("/") #new 
def root():
    return render_template('LoginPage.html')

"Staff app route"
@app.route("/staff") #new 
def staffLogin():
    return render_template('staffLogin.html')

@app.route("/staff/login", methods=['POST', 'GET']) #new
def staffLoginValidation():
    with connection.cursor() as cursor:
        if request.method == 'POST':
            Email = request.form['Email']
            password = request.form['password']
            sql = 'SELECT UserID, Password from tbl_UserManagement WHERE Email="{Email}"'
            cursor.execute(sql.format(Email=Email))
            result = cursor.fetchall()
            for i in result: 
                if i['Password'] == password:
                    Email = Email
                    id = i["UserID"]
                    sql = 'UPDATE tbl_UserManagement set loginStatus=1 where Email="{Email}";'
                    cursor.execute(sql.format(Email=Email))
                    connection.commit()
                    return redirect('/staff/{id}/home'.format(id=id))
                else: 
                    return render_template('staffLogin.html', status='fail')
            return render_template('staffLogin.html', status='fail')
        else:
            return render_template('staffLogin.html')

@app.route("/staff/forgotPassword")
def staffForgotPassword():
    return render_template('staffForgotPassword.html')

@app.route("/staff/forgotPassword/email", methods=['GET', 'POST'])
def staffPassword():
    with connection.cursor() as cursor:
        if request.method =='POST':
            PhoneNo = request.form['PhoneNo'].strip()
            Email = request.form['Email'].strip()
            cursor.execute('SELECT * from tbl_UserManagement')
            result = cursor.fetchall()
            message = 0 
            for i in result: 
                if int(i['PhoneNo']) == int(PhoneNo):   
                    if i['Email'] == Email:
                        subject = 'Forgot password'
                        sender = 'testingtestinguat2@gmail.com'
                        recipient = Email
                        content = 'Your UserID: {UserID} <br> <br>' \
                            'Your Password: {Password}<br> <br>'. format(UserID=i['UserID'] , Password=i['Password'] )
                        send_email(subject, sender, recipient, content)
                        return render_template('staffForgotPassword.html', status='sent')  
            return render_template('staffForgotPassword.html', status='fail')
        else: 
            return redirect('/staff/forgotPassword')

@app.route("/staff/<int:id>/home", methods=['POST', 'GET']) #new
def staffHome(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            updateActivityStatus()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity, tbl_ActivityAssign WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND tbl_ActivityAssign.ActivityID = tbl_Activity.ActivityID AND UserID={UserID} AND ActivityEndDate>=curdate() AND ActivityStatus <> "Deleted"'
            cursor.execute(sql.format(UserID=id))
            activity = cursor.fetchall()
            return render_template('home.html', user=user, activity=activity, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/customer", methods=['POST', 'GET']) #new
def staffCustomer(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Customer')
            customer = cursor.fetchall()
            return render_template('staffCustomer.html', user=user, customer=customer, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/customer/<int:cusid>/edit", methods=['POST', 'GET']) #new
def editcustomer(id, cusid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Customer WHERE CustomerID={cusid}'
            cursor.execute(sql.format(cusid=cusid))
            customer = cursor.fetchall()
            if request.method == 'POST':
                Password = request.form['Password']
                CompanyName = request.form['CompanyName']
                ContactPerson = request.form['ContactPerson']
                PhoneNo = request.form['PhoneNo']
                Email = request.form['Email']
                SecondContact = request.form['SecondContact']
                SecondContactEmail = request.form['SecondContactEmail']
                SecondContactPhone = request.form['SecondContactPhone']
                BillingAddress = request.form['BillingAddress']
                PrimaryAddress = request.form['PrimaryAddress']
                CompanyType = request.form['CompanyType']
                sql = 'SELECT * FROM tbl_Customer WHERE CustomerID!={cusid}'
                cursor.execute(sql.format(cusid=cusid))
                result = cursor.fetchall()
                for i in result:
                    if int(i['PhoneNo']) == int(PhoneNo):
                        return render_template('staffCustomerEdit.html', user=user, customer=customer, status='phoneNodup', role=role)
                    if i['Email'] == Email:
                        return render_template('staffCustomerEdit.html', user=user, customer=customer, status='emaildup', role=role)   
                if SecondContact == ('' or 'None'):
                    updatesql='UPDATE tbl_Customer SET Password="{Password}", CompanyName="{CompanyName}", ContactPerson="{ContactPerson}", PhoneNo={PhoneNo}, Email="{Email}", BillingAddress="{BillingAddress}",PrimaryAddress="{PrimaryAddress}", CompanyType="{CompanyType}" WHERE CustomerID={cusid}'
                    cursor.execute(updatesql.format(Password=Password, CompanyName=CompanyName, ContactPerson=ContactPerson, PhoneNo=PhoneNo, Email=Email, BillingAddress=BillingAddress, PrimaryAddress=PrimaryAddress, CompanyType=CompanyType, cusid=cusid))
                    connection.commit()
                else:
                    updatesql='UPDATE tbl_Customer SET Password="{Password}", CompanyName="{CompanyName}", ContactPerson="{ContactPerson}", PhoneNo={PhoneNo}, Email="{Email}", SecondContact="{SecondContact}", SecondContactEmail="{SecondContactEmail}",SecondContactPhone="{SecondContactPhone}", BillingAddress="{BillingAddress}",PrimaryAddress="{PrimaryAddress}", CompanyType="{CompanyType}" WHERE CustomerID={cusid}'
                    cursor.execute(updatesql.format(Password=Password, CompanyName=CompanyName, ContactPerson=ContactPerson, PhoneNo=PhoneNo, Email=Email, SecondContact=SecondContact, SecondContactEmail=SecondContactEmail, SecondContactPhone=SecondContactPhone, BillingAddress=BillingAddress, PrimaryAddress=PrimaryAddress, CompanyType=CompanyType, cusid=cusid))
                    connection.commit() 
                sql = 'SELECT * FROM tbl_Customer WHERE CustomerID={cusid}'
                cursor.execute(sql.format(cusid=cusid))
                customer = cursor.fetchall()            
                return render_template('staffCustomerEdit.html', user=user, customer=customer, status='success', role=role)
            else: 
                return render_template('staffCustomerEdit.html', user=user, customer=customer, status=None, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/customer/<int:cusid>/view", methods=['POST', 'GET']) #new
def viewcustomer(id, cusid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Customer WHERE CustomerID={cusid}'
            cursor.execute(sql.format(cusid=cusid))
            customer = cursor.fetchall()
            return render_template('staffCustomerView.html', user=user, customer=customer, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addCustomer", methods=['POST', 'GET']) #new
def addCustomer(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                Password = request.form['Password']
                ConfirmPassword = request.form['ConfirmPassword']
                CompanyName = request.form['CompanyName']
                ContactPerson = request.form['ContactPerson']
                PhoneNo = request.form['PhoneNo']
                Email = request.form['Email']
                SecondContact = request.form['SecondContact']
                SecondContactEmail = request.form['SecondContactEmail']
                SecondContactPhone = request.form['SecondContactPhone']
                BillingAddress = request.form['BillingAddress']
                PrimaryAddress = request.form['PrimaryAddress']
                CompanyType = request.form['CompanyType']
                if ConfirmPassword == Password:
                    cursor.execute('SELECT * FROM tbl_Customer')
                    result = cursor.fetchall()
                    for i in result:
                        if int(i['PhoneNo']) == int(PhoneNo):
                            return render_template('staffCustomerAdd.html', user=user, status='phoneNodup', role=role)
                        if i['Email'] == Email:
                            return render_template('staffCustomerAdd.html', user=user, status='emaildup', role=role)   
                    if SecondContact == '':
                        insertsql='INSERT INTO tbl_Customer(Password, CompanyName, ContactPerson, PhoneNo, Email, BillingAddress, PrimaryAddress, CompanyType, LoginStatus) VALUES ("{Password}", "{CompanyName}", "{ContactPerson}", "{PhoneNo}", "{Email}", "{BillingAddress}","{PrimaryAddress}", "{CompanyType}", 0)'
                        cursor.execute(insertsql.format(Password=Password, CompanyName=CompanyName, ContactPerson=ContactPerson, PhoneNo=PhoneNo, Email=Email, BillingAddress=BillingAddress, PrimaryAddress=PrimaryAddress, CompanyType=CompanyType))
                        connection.commit()
                    else:
                        insertsql='INSERT INTO tbl_Customer(Password, CompanyName, ContactPerson, PhoneNo, Email, SecondContact, SecondContactEmail, SecondContactPhone, BillingAddress, PrimaryAddress, CompanyType, LoginStatus) VALUES ("{Password}", "{CompanyName}", "{ContactPerson}", "{PhoneNo}", "{Email}", "{SecondContact}", "{SecondContactEmail}","{SecondContactPhone}", "{BillingAddress}","{PrimaryAddress}", "{CompanyType}", 0)'
                        cursor.execute(insertsql.format(Password=Password, CompanyName=CompanyName, ContactPerson=ContactPerson, PhoneNo=PhoneNo, Email=Email, SecondContact=SecondContact, SecondContactEmail=SecondContactEmail, SecondContactPhone=SecondContactPhone, BillingAddress=BillingAddress, PrimaryAddress=PrimaryAddress, CompanyType=CompanyType))
                        connection.commit()
                    return render_template('staffCustomerAdd.html', user=user, status='success', role=role)
                else:
                    return render_template('staffCustomerAdd.html', user=user, status='invalidConfirmPassword', role=role)
            else: 
                return render_template('staffCustomerAdd.html', user=user, status=None, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/project", methods=['POST', 'GET']) #new
def project(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID')
            project = cursor.fetchall()
            return render_template('staffProject.html', user=user, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addProject", methods=['POST', 'GET']) #new
def addProject(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Customer')
            customer = cursor.fetchall()
            if request.method == 'POST':
                CustomerID = request.form['CustomerID']
                ProjectName = request.form['ProjectName']
                Description = request.form['Description']
                Location = request.form['Location']
                ProjectAttachment = request.files['ProjectAttachment']
                StartDate = request.form['StartDate']
                EndDate = request.form['EndDate']
                WarrantyStart = request.form['WarrantyStart']
                WarrantyEnd = request.form['WarrantyEnd']
                if WarrantyStart == '':
                    insertsql='INSERT INTO tbl_Project(CustomerID, ProjectName, Description, Location, ProjectAttachment, StartDate, EndDate) VALUES ("{CustomerID}", "{ProjectName}", "{Description}", "{Location}", "{ProjectAttachment}", "{StartDate}", "{EndDate}")'
                    cursor.execute(insertsql.format(CustomerID=CustomerID, ProjectName=ProjectName, Description=Description, Location=Location, ProjectAttachment=ProjectAttachment.filename, StartDate=StartDate, EndDate=EndDate))
                    connection.commit()
                else:
                    insertsql='INSERT INTO tbl_Project(CustomerID, ProjectName, Description, Location, ProjectAttachment, StartDate, EndDate, WarrantyStart, WarrantyEnd) VALUES ("{CustomerID}", "{ProjectName}", "{Description}", "{Location}", "{ProjectAttachment}", "{StartDate}", "{EndDate}", "{WarrantyStart}", "{WarrantyEnd}")'
                    cursor.execute(insertsql.format(CustomerID=CustomerID, ProjectName=ProjectName, Description=Description, Location=Location, ProjectAttachment=ProjectAttachment.filename, StartDate=StartDate, EndDate=EndDate, WarrantyStart=WarrantyStart, WarrantyEnd=WarrantyEnd))
                    connection.commit()
                for file in request.files.getlist("ProjectAttachment"):
                    try:
                        container_client_project.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                        status='NameDup'
                #ProjectAttachment.save(os.path.join(app.config['UPLOAD_FOLDER'], ProjectAttachment.filename))
                return redirect('/staff/{id}/project'.format(id=id))
            else: 
                return render_template('staffProjectAdd.html', user=user, customer=customer, status=None, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/project/<int:pid>/view", methods=['POST', 'GET']) #new
def viewProject(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND tbl_Project.ProjectID = {pid}'
            cursor.execute(sql.format(pid=pid))
            activity = cursor.fetchall()
            return render_template('staffProjectView.html', user=user, project=project,activity=activity, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/project/<int:pid>/edit/projectEnd", methods=['POST', 'GET']) #new
def projectEnd(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            canClosed = True
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND tbl_Project.ProjectID = {pid}'
            cursor.execute(sql.format(pid=pid))
            activity = cursor.fetchall()
            for i in project: 
                ProjectStatus = i['ProjectStatus']
                Invoiced = i['Invoiced']
                AmountReceived = i['AmountReceived']
                TotalAmount = i['TotalAmount']
                WarrantyEnd = i['WarrantyEnd']
                EndDate = i['EndDate']
            for i in activity:
                if i['ActivityStatus'] == "New" or i['ActivityStatus'] == "In Progress":
                    canClosed = False
            if canClosed == True: 
                if ProjectStatus == 'Warranty Start':
                    if EndDate < date.today():
                        if WarrantyEnd < date.today():
                            if Invoiced == AmountReceived == TotalAmount:
                                updateProjectSQL = 'UPDATE tbl_Project SET ProjectStatus="Project End" WHERE ProjectID={pid}'
                                cursor.execute(updateProjectSQL.format(pid=pid))
                                connection.commit()
                                return redirect('/staff/{id}/project/{pid}/edit'.format(id=id, pid=pid))
                            else:
                                return render_template('staffProjectEdit.html', user=user, project=project,activity=activity, status='Invalid Amount', role=role)
                        else: 
                            return render_template('staffProjectEdit.html', user=user, project=project,activity=activity, status='Warranty not yet end', role=role)
                    else: 
                        return render_template('staffProjectEdit.html', user=user, project=project,activity=activity, status='Project not yet end', role=role)
                else:
                    return render_template('staffProjectEdit.html', user=user, project=project,activity=activity, status='Invalid Project Status', role=role)
            else: 
                return render_template('staffProjectEdit.html', user=user, project=project,activity=activity, status='Invalid activity Status', role=role)
    else: 
        return render_template('404.html'), 404

'''
@app.route("/staff/<int:id>/project/<int:pid>/download", methods=['POST', 'GET']) #new
def projectDownload(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT ProjectAttachment FROM tbl_Project WHERE ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            for i in project: 
                return send_from_directory(app.config['UPLOAD_FOLDER'], i['ProjectAttachment'], as_attachment=True)
    else: 
        return render_template('404.html'), 404
'''

@app.route("/staff/<int:id>/project/<int:pid>/edit", methods=['POST', 'GET']) #new
def editProject(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND tbl_Project.ProjectID = {pid}'
            cursor.execute(sql.format(pid=pid))
            activity = cursor.fetchall()
            if request.method == 'POST':
                ProjectName = request.form['ProjectName']
                Description = request.form['Description']
                Location = request.form['Location']
                StartDate = request.form['StartDate']
                EndDate = request.form['EndDate']
                WarrantyStart = request.form['WarrantyStart']
                WarrantyEnd = request.form['WarrantyEnd']
                if WarrantyStart == '' or None:
                    updatesql='UPDATE tbl_Project SET ProjectName="{ProjectName}", Description="{Description}", Location="{Location}", StartDate="{StartDate}", EndDate="{EndDate}" WHERE ProjectID={pid}'
                    cursor.execute(updatesql.format(ProjectName=ProjectName, Description=Description, Location=Location, StartDate=StartDate, EndDate=EndDate, pid=pid))
                    connection.commit()
                else:
                    updatesql='UPDATE tbl_Project SET ProjectName="{ProjectName}", Description="{Description}", Location="{Location}", StartDate="{StartDate}", EndDate="{EndDate}", WarrantyStart="{WarrantyStart}", WarrantyEnd="{WarrantyEnd}" WHERE ProjectID={pid}'
                    cursor.execute(updatesql.format(ProjectName=ProjectName, Description=Description, Location=Location, StartDate=StartDate, EndDate=EndDate, WarrantyStart=WarrantyStart, WarrantyEnd=WarrantyEnd, pid=pid))
                    connection.commit()
                user = getUserInfo(id)
                sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
                cursor.execute(sql.format(pid=pid))
                project = cursor.fetchall()
                return render_template('staffProjectEdit.html', user=user, project=project,activity=activity, status='success', role=role)
            else: 
                return render_template('staffProjectEdit.html', user=user, project=project, activity=activity, status=None, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/project/<int:pid>/closeProject", methods=['POST', 'GET']) #new
def closeProject(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            deletesql='UPDATE tbl_Project SET ProjectStatus="Closed", ClosedBy={UserID} WHERE ProjectID="{ProjectID}"'
            cursor.execute(deletesql.format(UserID=id, ProjectID=pid))
            updatesql='UPDATE tbl_Activity SET ActivityStatus="Deleted", DeletedBy={UserID} WHERE ProjectID="{ProjectID}"'
            cursor.execute(updatesql.format(UserID=id, ProjectID=pid))
            connection.commit()
            return redirect('/staff/{id}/project'.format(id=id))
    else: 
        return render_template('404.html'), 404
  
@app.route("/staff/<int:id>/project/<int:pid>/edit/startWarranty", methods=['POST', 'GET']) #new
def startWarranty(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            ProjectStatus = getProjectStatus(pid)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            if ProjectStatus == "Project Start":
                if request.method == 'POST':
                    WarrantyStart = request.form['WarrantyStart']
                    WarrantyEnd = request.form['WarrantyEnd']
                    updatesql='UPDATE tbl_Project SET ProjectStatus="Warranty Start", WarrantyStart="{WarrantyStart}", WarrantyEnd="{WarrantyEnd}" WHERE ProjectID={pid}'
                    cursor.execute(updatesql.format(WarrantyStart=WarrantyStart, WarrantyEnd=WarrantyEnd, pid=pid))
                    connection.commit()
                    return redirect('/staff/{id}/project/{ProjectID}/edit'.format(id=id, ProjectID=pid))
                else: 
                    return render_template('staffProjectEdit.html', user=user, project=project, status=None, role=role)
            else: 
                return render_template('staffProjectEdit.html', user=user, project=project, status='Invalid Status for Start Warranty', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/project/<int:pid>/edit/submitpic", methods=['POST', 'GET']) #new
def editProjectSubmitPic(id, pid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                ProjectAttachment = request.files['ProjectAttachment']
                for file in request.files.getlist("ProjectAttachment"):
                    try:
                        container_client_project.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                        status='NameDup'
                #ProjectAttachment.save(os.path.join(app.config['UPLOAD_FOLDER'], ProjectAttachment.filename))
                sql = 'UPDATE tbl_Project SET ProjectAttachment="{ProjectAttachment}" WHERE ProjectID={ProjectID}'
                cursor.execute(sql.format(ProjectAttachment=ProjectAttachment.filename, ProjectID=pid))
                connection.commit()
                sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
                cursor.execute(sql.format(pid=pid))
                project = cursor.fetchall()
                return redirect('/staff/{id}/project/{ProjectID}/edit'.format(id=id, ProjectID=pid))
            else:
                sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
                cursor.execute(sql.format(pid=pid))
                project = cursor.fetchall()
                return render_template('staffProjectEdit.html', user=user, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote", methods=['POST', 'GET']) #new
def quote(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID')
            quote = cursor.fetchall()
            return render_template('staffQuote.html', user=user, quote=quote, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addQuote", methods=['POST', 'GET']) #new
def addQuote(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus="Pending for Quotation" or ProjectStatus="Quotation Pending for Confirmation"')
            project = cursor.fetchall()
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                QuotationTitle = request.form['QuotationTitle']
                ToField = request.form['ToField']
                Attn = request.form['Attn']
                Remarks = request.form['Remarks']
                ProjectStatus = getProjectStatus(ProjectID)
                if ProjectStatus == ('Pending for Quotation' or 'Quotation Pending for Confirmation'):
                    insertsql='INSERT INTO tbl_Quotation(ProjectID, QuotationTitle, ToField, Attn, GrantTotal, Remarks, QuotationStatus) VALUES ("{ProjectID}", "{QuotationTitle}", "{ToField}", "{Attn}", 0, "{Remarks}", "New")'
                    cursor.execute(insertsql.format(ProjectID=ProjectID, QuotationTitle=QuotationTitle, ToField=ToField, Attn=Attn, Remarks=Remarks))
                    connection.commit()
                    cursor.execute('SELECT QuotationID FROM tbl_Quotation ORDER BY QuotationID DESC LIMIT 1')
                    data = cursor.fetchall()
                    for i in data:
                        QuotationID = i['QuotationID']
                    return redirect('/staff/{id}/quote/{QuotationID}/edit'.format(id=id, QuotationID=QuotationID))
                else: 
                    return render_template('staffQuoteAdd.html', user=user, project=project, status='Invalid Status', role=role)
            else: 
                return render_template('staffQuoteAdd.html', user=user, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/edit", methods=['POST', 'GET']) #new
def editQuote(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotation = cursor.fetchall()
            for i in quotation: 
                QuotationStatus = i['QuotationStatus']
                ProjectStatus = i['ProjectStatus']
            sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotationLine = cursor.fetchall()
            if ProjectStatus == 'Pending for Quotation' or ProjectStatus == 'Quotation Pending for Confirmation':
                if QuotationStatus == 'New':
                    if request.method == 'POST':
                        ProjectID = request.form['ProjectID']
                        QuotationTitle = request.form['QuotationTitle']
                        ToField = request.form['ToField']
                        Attn = request.form['Attn']
                        Remarks = request.form['Remarks']
                        sql = 'SELECT SUM(Amount) as GrantTotal FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                        cursor.execute(sql.format(QuotationID=qid))
                        data = cursor.fetchall()
                        for i in data:
                            GrantTotal = i['GrantTotal']
                        if GrantTotal == None:
                            GrantTotal = 0
                        updatesql='UPDATE tbl_Quotation SET QuotationTitle="{QuotationTitle}", ToField="{ToField}", Attn="{Attn}", GrantTotal="{GrantTotal}", Remarks="{Remarks}" WHERE QuotationID={QuotationID}'
                        cursor.execute(updatesql.format(QuotationTitle=QuotationTitle, ToField=ToField, Attn=Attn, GrantTotal=GrantTotal, Remarks=Remarks, QuotationID=qid))
                        connection.commit()
                        sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
                        cursor.execute(sql.format(QuotationID=qid))
                        quotation = cursor.fetchall()
                        sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                        cursor.execute(sql.format(QuotationID=qid))
                        quotationLine = cursor.fetchall()
                        return render_template('staffQuoteEdit.html', user=user, quotation=quotation, quotationLine=quotationLine, status='success', role=role)
                    else: 
                        return render_template('staffQuoteEdit.html', user=user, quotation=quotation, quotationLine=quotationLine, role=role)
                else: 
                    return render_template('staffQuoteEdit.html', user=user, status='Invalid Quotation Status', role=role)
            else: 
                return render_template('staffQuoteEdit.html', user=user, status='Invalid Project Status', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/edit/add", methods=['POST', 'GET']) #new
def addQuotationLine(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                WorkDescription = request.form['WorkDescription']
                UnitRate = request.form['UnitRate']
                Quantity = request.form['Quantity']
                Quantifier = request.form['Quantifier']
                Amount = float(UnitRate) * int(Quantity)
                Amount = format(Amount, '.2f')
                ProjectStatus = getProjectStatus(ProjectID)
                if ProjectStatus == 'Pending for Quotation' or ProjectStatus == 'Quotation Pending for Confirmation':
                    sql = 'SELECT WorkID+1 FROM tbl_QuotationLine WHERE QuotationID = {QuotationID} ORDER BY WorkID DESC LIMIT 1'
                    cursor.execute(sql.format(QuotationID=qid))
                    Number = cursor.fetchall()
                    WorkID=1
                    for i in Number:
                        WorkID=i['WorkID+1']
                        if WorkID == None:
                            WorkID = 1
                    insertsql='INSERT INTO tbl_QuotationLine VALUES ({QuotationID}, {WorkID}, "{WorkDescription}", {UnitRate}, {Quantity}, "{Quantifier}", {Amount})'
                    cursor.execute(insertsql.format(QuotationID=qid, WorkID=WorkID, WorkDescription=WorkDescription, UnitRate=UnitRate, Quantity=Quantity, Quantifier=Quantifier, Amount=Amount))
                    sql = 'SELECT SUM(Amount) as GrantTotal FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                    cursor.execute(sql.format(QuotationID=qid))
                    data = cursor.fetchall()
                    for i in data:
                        GrantTotal = i['GrantTotal']
                    updatesql='UPDATE tbl_Quotation SET GrantTotal="{GrantTotal}" WHERE QuotationID={QuotationID}'
                    cursor.execute(updatesql.format(GrantTotal=GrantTotal, QuotationID=qid))
                    connection.commit()
                    return redirect('/staff/{id}/quote/{qid}/edit'.format(id=id, qid=qid))
                else:
                    return redirect('/staff/{id}/quote/{qid}/edit'.format(id=id, qid=qid))
            else: 
                return redirect('/staff/{id}/quote/{qid}/edit'.format(id=id, qid=qid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/edit/<int:wid>", methods=['POST', 'GET']) #new
def editQuotationLine(id, qid, wid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                WorkDescription = request.form['WorkDescription']
                UnitRate = request.form['UnitRate']
                Quantity = request.form['Quantity']
                Quantifier = request.form['Quantifier']
                Amount = float(UnitRate) * int(Quantity)
                Amount = format(Amount, '.2f')
                ProjectStatus = getProjectStatus(ProjectID)
                if ProjectStatus == 'Pending for Quotation' or ProjectStatus == 'Quotation Pending for Confirmation':
                    updatesql='UPDATE tbl_QuotationLine SET WorkDescription="{WorkDescription}", UnitRate={UnitRate}, Quantity={Quantity}, Quantifier="{Quantifier}", Amount={Amount} WHERE WorkID={WorkID}'
                    cursor.execute(updatesql.format(WorkID=wid, WorkDescription=WorkDescription, UnitRate=UnitRate, Quantity=Quantity, Quantifier=Quantifier, Amount=Amount))
                    sql = 'SELECT SUM(Amount) as GrantTotal FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                    cursor.execute(sql.format(QuotationID=qid))
                    data = cursor.fetchall()
                    for i in data:
                        GrantTotal = i['GrantTotal']
                    updatesql='UPDATE tbl_Quotation SET GrantTotal="{GrantTotal}" WHERE QuotationID={QuotationID}'
                    cursor.execute(updatesql.format(GrantTotal=GrantTotal, QuotationID=qid))
                    connection.commit()
                    return redirect('/staff/{id}/quote/{qid}/edit'.format(id=id, qid=qid))
                else: 
                    return redirect('/staff/{id}/quote/{qid}/edit'.format(id=id, qid=qid))
            else: 
                return redirect('/staff/{id}/quote/{qid}/edit'.format(id=id, qid=qid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/view", methods=['POST', 'GET']) #new
def viewQuote(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotation = cursor.fetchall()
            sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotationLine = cursor.fetchall()
            return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/view/submit", methods=['POST', 'GET']) #new
def submitQuotation(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotation = cursor.fetchall()
            sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotationLine = cursor.fetchall()
            for i in quotation: 
                ProjectID = i['ProjectID']
                ProjectStatus = i['ProjectStatus']
                QuotationStatus = i['QuotationStatus']
            if ProjectStatus == 'Pending for Quotation':
                if QuotationStatus == 'New':
                    updateQuotationSQL = 'UPDATE tbl_Quotation SET QuotationStatus="Pending for Confirmation", QuotationDate=curdate() WHERE QuotationID={QuotationID}'
                    cursor.execute(updateQuotationSQL.format(QuotationID=qid))
                    updateProjectSQL = 'UPDATE tbl_Project SET ProjectStatus="Quotation Pending for Confirmation" WHERE ProjectID={ProjectID}'
                    cursor.execute(updateProjectSQL.format(ProjectID=ProjectID))
                    connection.commit()
                    return redirect('/staff/{id}/quote/{qid}/view'.format(id=id, qid=qid))
                else:
                    return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, status='Invalid Submit Quotation Status', role=role)
            else:
                return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, status='Invalid Submit Project Status', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/view/confirm", methods=['POST', 'GET']) #new
def confirmQuotation(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                ConfirmedWith = request.form['ConfirmedWith']
                ConfirmedTime = request.form['ConfirmedTime']
                sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotation = cursor.fetchall()
                sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotationLine = cursor.fetchall()
                for i in quotation: 
                    ProjectID = i['ProjectID']
                    ProjectStatus = i['ProjectStatus']
                    QuotationStatus = i['QuotationStatus']
                    TotalAmount = i['GrantTotal']
                if ProjectStatus == 'Quotation Pending for Confirmation':
                    if QuotationStatus == 'Pending for Confirmation':
                        updateQuotationSQL = 'UPDATE tbl_Quotation SET QuotationStatus="Confirmed", ConfirmedBy="{ConfirmedBy}", ConfirmedWith="{ConfirmedWith}", ConfirmedTime="{ConfirmedTime}" WHERE QuotationID={QuotationID}'
                        cursor.execute(updateQuotationSQL.format(ConfirmedBy=id, ConfirmedWith=ConfirmedWith, ConfirmedTime=ConfirmedTime, QuotationID=qid))
                        updateProjectSQL = 'UPDATE tbl_Project SET ProjectStatus="Project Start", TotalAmount={TotalAmount} WHERE ProjectID={ProjectID}'
                        cursor.execute(updateProjectSQL.format(ProjectID=ProjectID, TotalAmount=TotalAmount))
                        connection.commit()
                        return redirect('/staff/{id}/quote/{qid}/view'.format(id=id, qid=qid))
                    else:
                        return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, status='Invalid Confirm Quotation Status', role=role)
                else:
                    return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, status='Invalid Confirm Project Status', role=role)
            else: 
                return redirect('/staff/{id}/quote/{qid}/view'.format(id=id, qid=qid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/view/reject", methods=['POST', 'GET']) #new
def rejectQuotation(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                ConfirmedWith = request.form['ConfirmedWith']
                ConfirmedTime = request.form['ConfirmedTime']
                sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotation = cursor.fetchall()
                sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotationLine = cursor.fetchall()
                for i in quotation: 
                    ProjectID = i['ProjectID']
                    ProjectStatus = i['ProjectStatus']
                    QuotationStatus = i['QuotationStatus']
                if ProjectStatus == 'Quotation Pending for Confirmation':
                    if QuotationStatus == 'Pending for Confirmation':
                        updateQuotationSQL = 'UPDATE tbl_Quotation SET QuotationStatus="Rejected", ConfirmedBy="{ConfirmedBy}", ConfirmedWith="{ConfirmedWith}", ConfirmedTime="{ConfirmedTime}" WHERE QuotationID={QuotationID}'
                        cursor.execute(updateQuotationSQL.format(ConfirmedBy=id, ConfirmedWith=ConfirmedWith, ConfirmedTime=ConfirmedTime, QuotationID=qid))
                        updateProjectSQL = 'UPDATE tbl_Project SET ProjectStatus="Pending for Quotation" WHERE ProjectID={ProjectID}'
                        cursor.execute(updateProjectSQL.format(ProjectID=ProjectID))
                        connection.commit()
                        return redirect('/staff/{id}/quote/{qid}/view'.format(id=id, qid=qid))
                    else:
                        return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, status='Invalid Confirm Quotation Status', role=role)
                else:
                    return render_template('staffQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, status='Invalid Confirm Project Status', role=role)
            else: 
                return redirect('/staff/{id}/quote/{qid}/view'.format(id=id, qid=qid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/quote/<int:qid>/view/report", methods=['POST', 'GET']) #new
def viewQuoteReport(id, qid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotation = cursor.fetchall()
            sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotationLine = cursor.fetchall()
            rendered = render_template('staffQuoteReport.html', quotation=quotation, quotationLine=quotationLine)
            responsestring = pdfkit.from_string(rendered, False, options={"enable-local-file-access": ""})
            response = make_response(responsestring)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment;filename=quotation.pdf'      
            return response
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice", methods=['POST', 'GET']) 
def invoice(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID')
            invoice = cursor.fetchall()
            return render_template('staffInvoice.html', user=user, invoice=invoice, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addInvoice", methods=['POST', 'GET']) #new
def addInvoice(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus="Project Start" or ProjectStatus="Warranty Start"')
            project = cursor.fetchall()
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                InvoiceTitle = request.form['InvoiceTitle']
                ToField = request.form['ToField']
                Attn = request.form['Attn']
                Remarks = request.form['Remarks']
                DueDate = request.form['DueDate']
                BankAccountNo = request.form['BankAccountNo']
                ProjectStatus = getProjectStatus(ProjectID)
                if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                    insertsql='INSERT INTO tbl_Invoice(ProjectID, InvoiceTitle, ToField, Attn, GrantTotal, Remarks, InvoiceStatus, DueDate, BankAccountNo) VALUES ("{ProjectID}", "{InvoiceTitle}", "{ToField}", "{Attn}", 0, "{Remarks}", "New", "{DueDate}", "{BankAccountNo}")'
                    cursor.execute(insertsql.format(ProjectID=ProjectID, InvoiceTitle=InvoiceTitle, ToField=ToField, Attn=Attn, Remarks=Remarks, DueDate=DueDate, BankAccountNo=BankAccountNo))
                    connection.commit()
                    cursor.execute('SELECT InvoiceID FROM tbl_Invoice ORDER BY InvoiceID DESC LIMIT 1')
                    data = cursor.fetchall()
                    for i in data:
                        InvoiceID = i['InvoiceID']
                    return redirect('/staff/{id}/invoice/{InvoiceID}/edit'.format(id=id, InvoiceID=InvoiceID))
                else: 
                    return render_template('staffInvoiceAdd.html', user=user, project=project, status='Invalid Status', role=role)
            else: 
                return render_template('staffInvoiceAdd.html', user=user, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/edit", methods=['POST', 'GET']) #new
def editInvoice(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            for i in invoice: 
                InvoiceStatus = i['InvoiceStatus']
                ProjectStatus = i['ProjectStatus']
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                if InvoiceStatus == "New":
                    if request.method == 'POST':
                        ProjectID = request.form['ProjectID']
                        InvoiceTitle = request.form['InvoiceTitle']
                        ToField = request.form['ToField']
                        Attn = request.form['Attn']
                        Remarks = request.form['Remarks']
                        DueDate = request.form['DueDate']
                        BankAccountNo = request.form['BankAccountNo']
                        sql = 'SELECT SUM(Amount) as GrantTotal FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
                        cursor.execute(sql.format(InvoiceID=iid))
                        data = cursor.fetchall()
                        for i in data:
                            GrantTotal = i['GrantTotal']
                        if GrantTotal == None:
                            GrantTotal = 0
                        updatesql='UPDATE tbl_Invoice SET InvoiceTitle="{InvoiceTitle}", ToField="{ToField}", Attn="{Attn}", GrantTotal="{GrantTotal}", Remarks="{Remarks}", DueDate="{DueDate}", BankAccountNo="{BankAccountNo}" WHERE InvoiceID={InvoiceID}'
                        cursor.execute(updatesql.format(InvoiceTitle=InvoiceTitle, ToField=ToField, Attn=Attn, GrantTotal=GrantTotal, Remarks=Remarks, DueDate=DueDate, BankAccountNo=BankAccountNo, InvoiceID=iid))
                        connection.commit()
                        sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
                        cursor.execute(sql.format(InvoiceID=iid))
                        invoice = cursor.fetchall()
                        sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
                        cursor.execute(sql.format(InvoiceID=iid))
                        invoiceLine = cursor.fetchall()
                        return render_template('staffInvoiceEdit.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='success', role=role)
                    else: 
                        return render_template('staffInvoiceEdit.html', user=user, invoice=invoice, invoiceLine=invoiceLine, role=role)
                else: 
                    return render_template('staffInvoiceEdit.html', user=user, status='Invalid Invoice Status', role=role)    
            else: 
                return render_template('staffInvoiceEdit.html', user=user, status='Invalid Project Status', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/edit/add", methods=['POST', 'GET']) #new
def addInvoiceLine(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                WorkDescription = request.form['WorkDescription']
                UnitRate = request.form['UnitRate']
                Quantity = request.form['Quantity']
                Quantifier = request.form['Quantifier']
                Amount = float(UnitRate) * int(Quantity)
                Amount = format(Amount, '.2f')
                ProjectStatus = getProjectStatus(ProjectID)
                if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                    sql = 'SELECT WorkID+1 FROM tbl_InvoiceLine WHERE InvoiceID = {InvoiceID} ORDER BY WorkID DESC LIMIT 1'
                    cursor.execute(sql.format(InvoiceID=iid))
                    Number = cursor.fetchall()
                    WorkID=1
                    for i in Number:
                        WorkID=i['WorkID+1']
                        if WorkID == None:
                            WorkID = 1
                    insertsql='INSERT INTO tbl_InvoiceLine VALUES ({InvoiceID}, {WorkID}, "{WorkDescription}", {UnitRate}, {Quantity}, "{Quantifier}", {Amount})'
                    cursor.execute(insertsql.format(InvoiceID=iid, WorkID=WorkID, WorkDescription=WorkDescription, UnitRate=UnitRate, Quantity=Quantity, Quantifier=Quantifier, Amount=Amount))
                    sql = 'SELECT SUM(Amount) as GrantTotal FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
                    cursor.execute(sql.format(InvoiceID=iid))
                    data = cursor.fetchall()
                    for i in data:
                        GrantTotal = i['GrantTotal']
                    updatesql='UPDATE tbl_Invoice SET GrantTotal="{GrantTotal}" WHERE InvoiceID={InvoiceID}'
                    cursor.execute(updatesql.format(GrantTotal=GrantTotal, InvoiceID=iid))
                    connection.commit()
                    return redirect('/staff/{id}/invoice/{iid}/edit'.format(id=id, iid=iid))
                else:
                    return redirect('/staff/{id}/invoice/{iid}/edit'.format(id=id, iid=iid))
            else: 
                return redirect('/staff/{id}/invoice/{iid}/edit'.format(id=id, iid=iid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/edit/<int:wid>", methods=['POST', 'GET']) #new
def editInvoiceLine(id, iid, wid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                WorkDescription = request.form['WorkDescription']
                UnitRate = request.form['UnitRate']
                Quantity = request.form['Quantity']
                Quantifier = request.form['Quantifier']
                Amount = float(UnitRate) * int(Quantity)
                Amount = format(Amount, '.2f')
                ProjectStatus = getProjectStatus(ProjectID)
                if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                    updatesql='UPDATE tbl_InvoiceLine SET WorkDescription="{WorkDescription}", UnitRate={UnitRate}, Quantity={Quantity}, Quantifier="{Quantifier}", Amount={Amount} WHERE WorkID={WorkID}'
                    cursor.execute(updatesql.format(WorkID=wid, WorkDescription=WorkDescription, UnitRate=UnitRate, Quantity=Quantity, Quantifier=Quantifier, Amount=Amount))
                    sql = 'SELECT SUM(Amount) as GrantTotal FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
                    cursor.execute(sql.format(InvoiceID=iid))
                    data = cursor.fetchall()
                    for i in data:
                        GrantTotal = i['GrantTotal']
                    updatesql='UPDATE tbl_Invoice SET GrantTotal="{GrantTotal}" WHERE InvoiceID={InvoiceID}'
                    cursor.execute(updatesql.format(GrantTotal=GrantTotal, InvoiceID=iid))
                    connection.commit()
                    return redirect('/staff/{id}/invoice/{iid}/edit'.format(id=id, iid=iid))
                else: 
                    return redirect('/staff/{id}/invoice/{iid}/edit'.format(id=id, iid=iid))
            else: 
                return redirect('/staff/{id}/invoice/{iid}/edit'.format(id=id, iid=iid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/view", methods=['POST', 'GET']) #new
def viewInvoice(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/view/submit", methods=['POST', 'GET']) #new
def submitInvoice(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            for i in invoice: 
                ProjectID = i['ProjectID']
                ProjectStatus = i['ProjectStatus']
                InvoiceStatus = i['InvoiceStatus']
                GrantTotal = i['GrantTotal']
                TotalAmount = i['TotalAmount']
                Invoiced = i['Invoiced']
                if Invoiced == None:
                    Invoiced = 0
                NewInvoiced = GrantTotal+Invoiced
            if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                if InvoiceStatus == 'New':
                    if TotalAmount >= GrantTotal+Invoiced:
                        updateInvoiceSQL = 'UPDATE tbl_Invoice SET InvoiceStatus="Pending for Payment", InvoiceDate=curdate() WHERE InvoiceID={InvoiceID}'
                        cursor.execute(updateInvoiceSQL.format(InvoiceID=iid))
                        updateProjectSQL = 'UPDATE tbl_Project SET Invoiced= {NewInvoiced} WHERE ProjectID={ProjectID}'
                        cursor.execute(updateProjectSQL.format(ProjectID=ProjectID, NewInvoiced=NewInvoiced))
                        connection.commit()
                        return redirect('/staff/{id}/invoice/{iid}/view'.format(id=id, iid=iid))
                    else: 
                        return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid Amount', role=role)
                else:
                    return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid Submit Invoice Status', role=role)
            else:
                return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid Submit Project Status', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/view/confirm", methods=['POST', 'GET']) #new
def confirmInvoice(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            for i in invoice: 
                ProjectID = i['ProjectID']
                ProjectStatus = i['ProjectStatus']
                InvoiceStatus = i['InvoiceStatus']
                AmountReceived = i['AmountReceived']
                GrantTotal = i['GrantTotal']
                if AmountReceived == None:
                    AmountReceived = 0
                NewAmountReceived = AmountReceived + GrantTotal
            if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                if InvoiceStatus == 'Pending for Payment':
                    updateInvoiceSQL = 'UPDATE tbl_Invoice SET InvoiceStatus="Paid", ConfirmedBy="{ConfirmedBy}" WHERE InvoiceID={InvoiceID}'
                    cursor.execute(updateInvoiceSQL.format(ConfirmedBy=id, InvoiceID=iid))
                    updateProjectSQL = 'UPDATE tbl_Project SET AmountReceived={NewAmountReceived} WHERE ProjectID={ProjectID}'
                    cursor.execute(updateProjectSQL.format(ProjectID=ProjectID, NewAmountReceived=NewAmountReceived))
                    connection.commit()
                    return redirect('/staff/{id}/invoice/{iid}/view'.format(id=id, iid=iid))
                else:
                    return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid accept/reject Invoice Status', role=role)
            else:
                return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid accept/reject Project Status', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/view/reject", methods=['POST', 'GET']) #new
def rejectInvoice(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            for i in invoice: 
                ProjectID = i['ProjectID']
                ProjectStatus = i['ProjectStatus']
                InvoiceStatus = i['InvoiceStatus']
                GrantTotal = i['GrantTotal']
                Invoiced = i['Invoiced']
                NewInvoiced = Invoiced - GrantTotal
            if ProjectStatus == "Project Start" or ProjectStatus=="Warranty Start":
                if InvoiceStatus == 'Pending for Payment':
                    updateQuotationSQL = 'UPDATE tbl_Invoice SET InvoiceStatus="Rejected", ConfirmedBy="{ConfirmedBy}" WHERE InvoiceID={InvoiceID}'
                    cursor.execute(updateQuotationSQL.format(ConfirmedBy=id, InvoiceID=iid))
                    updateProjectSQL = 'UPDATE tbl_Project SET Invoiced={NewInvoiced} WHERE ProjectID={ProjectID}'
                    cursor.execute(updateProjectSQL.format(ProjectID=ProjectID, NewInvoiced=NewInvoiced))
                    connection.commit()
                    return redirect('/staff/{id}/invoice/{iid}/view'.format(id=id, iid=iid))
                else:
                    return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid accept/reject Invoice Status', role=role)
            else:
                return render_template('staffInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, status='Invalid accept/reject Project Status', role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/invoice/<int:iid>/view/report", methods=['POST', 'GET']) #new
def viewInvoiceReport(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            rendered = render_template('staffInvoiceReport.html', invoice=invoice, invoiceLine=invoiceLine)
            responsestring = pdfkit.from_string(rendered, False, options={"enable-local-file-access": ""})
            response = make_response(responsestring)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment;filename=invoice.pdf'      
            return response
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/activity", methods=['POST', 'GET']) #new
def activity(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            updateActivityStatus()
            cursor.execute('SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID')
            activity = cursor.fetchall()
            return render_template('staffActivity.html', user=user, activity=activity, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addActivity", methods=['POST', 'GET']) #new
def addActivity(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus = "Project Start" or ProjectStatus = "Warranty Start"')
            project = cursor.fetchall()
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                ActivityName = request.form['ActivityName']
                ActivityDescription = request.form['ActivityDescription']
                ActivityLocation = request.form['ActivityLocation']
                ActivityStartDate = request.form['ActivityStartDate']
                ActivityEndDate = request.form['ActivityEndDate']
                insertsql='INSERT INTO tbl_Activity(ProjectID, ActivityName, ActivityDescription, ActivityLocation, ActivityStartDate, ActivityEndDate, ActivityStatus) VALUES ("{ProjectID}", "{ActivityName}", "{ActivityDescription}", "{ActivityLocation}", "{ActivityStartDate}", "{ActivityEndDate}", "New")'
                cursor.execute(insertsql.format(ProjectID=ProjectID, ActivityName=ActivityName, ActivityDescription=ActivityDescription, ActivityLocation=ActivityLocation, ActivityStartDate=ActivityStartDate, ActivityEndDate=ActivityEndDate))
                connection.commit()
                cursor.execute('SELECT ActivityID FROM tbl_Activity ORDER BY ActivityID DESC LIMIT 1')
                data = cursor.fetchall()
                for i in data:
                    ActivityID = i['ActivityID']
                return redirect('/staff/{id}/activity/{ActivityID}/edit'.format(id=id, ActivityID=ActivityID))
            else: 
                return render_template('staffActivityAdd.html', user=user, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/activity/<int:aid>/edit", methods=['POST', 'GET']) #new
def editActivity(id, aid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND ActivityID="{ActivityID}"'
            cursor.execute(sql.format(ActivityID=aid))
            activity = cursor.fetchall()
            sql = 'SELECT ActivityStatus, ProjectStatus from tbl_Activity, tbl_Project WHERE tbl_Activity.ProjectID = tbl_Project.ProjectID AND ActivityID = {ActivityID}'
            cursor.execute(sql.format(ActivityID=aid))
            Status = cursor.fetchall()
            for i in Status: 
                ProjectStatus = i['ProjectStatus']
                ActivityStatus = i['ActivityStatus']
            if ProjectStatus == 'Project Start' or ProjectStatus == 'Warranty Start':
                if ActivityStatus == 'New' or ActivityStatus ==  "In Progress":
                    sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND ActivityID="{ActivityID}"'
                    cursor.execute(sql.format(ActivityID=aid))
                    activity = cursor.fetchall()
                    sql = 'SELECT * FROM tbl_ActivityAssign, tbl_UserManagement WHERE tbl_ActivityAssign.UserID=tbl_UserManagement.UserID AND ActivityID="{ActivityID}"'
                    cursor.execute(sql.format(ActivityID=aid))
                    ActivityAssign = cursor.fetchall()
                    sql = 'SELECT * FROM tbl_UserManagement WHERE UserID NOT IN (SELECT UserID FROM tbl_ActivityAssign WHERE ActivityID = "{ActivityID}")'
                    cursor.execute(sql.format(ActivityID=aid))
                    otherUser = cursor.fetchall()
                    if request.method == 'POST':
                        ProjectID = request.form['ProjectID']
                        ActivityName = request.form['ActivityName']
                        ActivityDescription = request.form['ActivityDescription']
                        ActivityLocation = request.form['ActivityLocation']
                        ActivityStartDate = request.form['ActivityStartDate']
                        ActivityEndDate = request.form['ActivityEndDate']
                        updatesql='UPDATE tbl_Activity SET ActivityName="{ActivityName}", ActivityDescription="{ActivityDescription}", ActivityLocation="{ActivityLocation}", ActivityStartDate="{ActivityStartDate}", ActivityEndDate="{ActivityEndDate}" WHERE ActivityID={ActivityID}'
                        cursor.execute(updatesql.format(ActivityName=ActivityName, ActivityDescription=ActivityDescription, ActivityLocation=ActivityLocation, ActivityStartDate=ActivityStartDate, ActivityEndDate=ActivityEndDate, ActivityID=aid))
                        connection.commit()
                        sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND ActivityID="{ActivityID}"'
                        cursor.execute(sql.format(ActivityID=aid))
                        activity = cursor.fetchall()
                        sql = 'SELECT * FROM tbl_ActivityAssign, tbl_UserManagement WHERE tbl_ActivityAssign.UserID=tbl_UserManagement.UserID AND ActivityID="{ActivityID}"'
                        cursor.execute(sql.format(ActivityID=aid))
                        ActivityAssign = cursor.fetchall()
                        sql = 'SELECT * FROM tbl_UserManagement WHERE UserID NOT IN (SELECT UserID FROM tbl_ActivityAssign WHERE ActivityID = "{ActivityID}")'
                        cursor.execute(sql.format(ActivityID=aid))
                        otherUser = cursor.fetchall()
                        return render_template('staffActivityEdit.html', user=user, activity=activity, ActivityAssign=ActivityAssign, otherUser=otherUser, status='success', role=role)
                    else: 
                        return render_template('staffActivityEdit.html', user=user, activity=activity, ActivityAssign=ActivityAssign, otherUser=otherUser, role=role)
                else: 
                    return render_template('staffActivityEdit.html', user=user, status='Invalid Activity Status', role=role)
            else: 
                return render_template('staffActivityEdit.html', user=user, status='Invalid Project Status', role=role)
    else:
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/activity/<int:aid>/deleteActivity", methods=['POST', 'GET']) #new
def deleteActivity(id, aid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            deletesql='UPDATE tbl_Activity SET ActivityStatus="Deleted", DeletedBy={UserID} WHERE ActivityID="{ActivityID}"'
            cursor.execute(deletesql.format(UserID=id, ActivityID=aid))
            connection.commit()
            return redirect('/staff/{id}/activity'.format(id=id))
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/activity/<int:aid>/edit/add", methods=['POST', 'GET']) #new
def assignStaff(id, aid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                ActivityID = request.form['ActivityID']
                UserID = request.form['UserID']
                insertsql='INSERT INTO tbl_ActivityAssign VALUES ({ActivityID}, {UserID})'
                cursor.execute(insertsql.format(ActivityID=ActivityID, UserID=UserID))
                connection.commit()
                return redirect('/staff/{id}/activity/{aid}/edit'.format(id=id, aid=aid))
            else:
                return redirect('/staff/{id}/activity/{aid}/edit'.format(id=id, aid=aid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/activity/<int:aid>/edit/<int:uid>", methods=['POST', 'GET']) #new
def editAssignStaff(id, aid, uid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                ActivityID = request.form['ActivityID']
                UserID = request.form['UserID']
                updatesql='UPDATE tbl_ActivityAssign SET UserID={UserID} WHERE UserID={OldUserID} AND ActivityID="{ActivityID}"'
                cursor.execute(updatesql.format(ActivityID=ActivityID, UserID=UserID, OldUserID=uid))
                connection.commit()
                return redirect('/staff/{id}/activity/{aid}/edit'.format(id=id, aid=aid))
            else:
                return redirect('/staff/{id}/activity/{aid}/edit'.format(id=id, aid=aid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/activity/<int:aid>/delete/<int:uid>", methods=['POST', 'GET']) #new
def deleteAssignStaff(id, aid, uid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            deletesql='DELETE FROM tbl_ActivityAssign WHERE UserID={UserID} AND ActivityID="{ActivityID}"'
            cursor.execute(deletesql.format(ActivityID=aid, UserID=uid))
            connection.commit()
            return redirect('/staff/{id}/activity/{aid}/edit'.format(id=id, aid=aid))
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/activity/<int:aid>/view", methods=['POST', 'GET']) #pending
def viewActivity(id, aid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            updateActivityStatus()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND ActivityID="{ActivityID}"'
            cursor.execute(sql.format(ActivityID=aid))
            activity = cursor.fetchall()
            sql = 'SELECT * FROM tbl_ActivityAssign, tbl_UserManagement WHERE tbl_ActivityAssign.UserID=tbl_UserManagement.UserID AND ActivityID="{ActivityID}"'
            cursor.execute(sql.format(ActivityID=aid))
            ActivityAssign = cursor.fetchall()
            return render_template('staffActivityView.html', user=user, activity=activity, ActivityAssign=ActivityAssign, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory", methods=['POST', 'GET']) #new
def inventory(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Inventory')
            inventory = cursor.fetchall()
            return render_template('staffInventory.html', user=user, inventory=inventory, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addInventory", methods=['POST', 'GET']) #new
def addInventory(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                InventoryName = request.form['InventoryName']
                Description = request.form['Description']
                Stock = request.form['Stock']
                Attachment = request.files['Attachment']
                insertsql='INSERT INTO tbl_Inventory(InventoryName, Description, Stock, Attachment) VALUES  ("{InventoryName}", "{Description}", "{Stock}", "{Attachment}")'
                cursor.execute(insertsql.format(InventoryName=InventoryName, Description=Description, Stock=Stock, Attachment=Attachment.filename))
                connection.commit()
                for file in request.files.getlist("Attachment"):
                    try:
                        container_client_inventory.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                        status='NameDup'
                #Attachment.save(os.path.join(app.config['UPLOAD_FOLDER_INVENTORY'], Attachment.filename))
                return redirect('/staff/{id}/inventory'.format(id=id))
            else: 
                return render_template('staffInventoryAdd.html', user=user, status=None, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory/<int:iid>/edit", methods=['POST', 'GET']) #new
def editInventory(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
            cursor.execute(sql.format(iid=iid))
            inventory = cursor.fetchall()
            if request.method == 'POST':
                InventoryName = request.form['InventoryName']
                Description = request.form['Description']
                updatesql='UPDATE tbl_Inventory SET InventoryName="{InventoryName}",Description="{Description}" WHERE InventoryID={iid}'
                cursor.execute(updatesql.format(InventoryName=InventoryName, Description=Description, iid=iid))
                connection.commit()
                user = getUserInfo(id)
                sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                cursor.execute(sql.format(iid=iid))
                inventory = cursor.fetchall()
                return render_template('staffInventoryEdit.html', user=user, inventory=inventory, status='success', role=role)
            else: 
                return render_template('staffInventoryEdit.html', user=user, inventory=inventory, status=None, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory/<int:iid>/edit/submitpic", methods=['POST', 'GET']) #new
def editInventorySubmitPic(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                Attachment = request.files['Attachment']
                for file in request.files.getlist("Attachment"):
                    try:
                        container_client_inventory.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                        status='NameDup'
                #Attachment.save(os.path.join(app.config['UPLOAD_FOLDER_INVENTORY'], Attachment.filename))
                sql = 'UPDATE tbl_Inventory SET Attachment="{Attachment}" WHERE InventoryID={InventoryID}'
                cursor.execute(sql.format(Attachment=Attachment.filename, InventoryID=iid))
                connection.commit()
                return redirect('/staff/{id}/inventory/{InventoryID}/edit'.format(id=id, InventoryID=iid))
            else:
                sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                cursor.execute(sql.format(iid=iid))
                inventory = cursor.fetchall()
                return render_template('staffInventoryEdit.html', user=user, inventory=inventory, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory/<int:iid>/view", methods=['POST', 'GET']) #new
def viewInventory(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
            cursor.execute(sql.format(iid=iid))
            inventory = cursor.fetchall()
            sql = 'SELECT * FROM tbl_AddStock WHERE InventoryID={iid}'
            cursor.execute(sql.format(iid=iid))
            addStockLine = cursor.fetchall()
            sql = 'SELECT * FROM tbl_UsageManagement WHERE InventoryID={iid}'
            cursor.execute(sql.format(iid=iid))
            usageLine = cursor.fetchall()
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
            project = cursor.fetchall()
            return render_template('staffInventoryView.html', user=user, inventory=inventory, addStockLine=addStockLine, usageLine=usageLine, project=project, role=role)
    else: 
        return render_template('404.html'), 404

'''
@app.route("/staff/<int:id>/inventory/<int:iid>/download", methods=['POST', 'GET']) #new
def inventoryDownload(id, iid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT Attachment FROM tbl_Inventory WHERE InventoryID={iid}'
            cursor.execute(sql.format(iid=iid))
            inventory = cursor.fetchall()
            for i in inventory: 
                return send_from_directory(app.config['UPLOAD_FOLDER_INVENTORY'], i['Attachment'], as_attachment=True)
    else: 
        return render_template('404.html'), 404
'''
        
@app.route("/staff/<int:id>/inventory/<int:iid>/view/addStock/add", methods=['POST', 'GET']) #new
def addStock(id, iid): 
    if checkLoginStatus(id) == True: 
        with connection.cursor() as cursor:
            if request.method == 'POST':
                InventoryID = request.form['InventoryID']
                Date = request.form['Date']
                Quantity = request.form['Quantity']
                UnitPrice = request.form['UnitPrice']
                Remarks = request.form['Remarks']
                TotalPrice = float(UnitPrice) * int(Quantity)
                TotalPrice = format(TotalPrice, '.2f')
                sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                cursor.execute(sql.format(iid=iid))
                inventory = cursor.fetchall()
                for i in inventory:
                    Stock = i['Stock']
                NewStock = int(Stock) + int(Quantity)
                insertsql='INSERT INTO tbl_AddStock(InventoryID, Date, Quantity, UnitPrice, TotalPrice, Remarks) VALUES ({InventoryID}, "{Date}", "{Quantity}", {UnitPrice}, {TotalPrice}, "{Remarks}")'
                cursor.execute(insertsql.format(InventoryID=InventoryID, Date=Date, Quantity=Quantity, UnitPrice=UnitPrice, TotalPrice=TotalPrice, Remarks=Remarks))
                updatesql='UPDATE tbl_Inventory SET Stock={NewStock} WHERE InventoryID={InventoryID}'
                cursor.execute(updatesql.format(NewStock=NewStock, InventoryID=InventoryID))
                connection.commit()
                return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
            else:
                return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory/<int:iid>/view/addStock/<int:aid>", methods=['POST', 'GET']) #new
def editAddStock(id, iid, aid): 
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                InventoryID = request.form['InventoryID']
                Date = request.form['Date']
                Quantity = request.form['Quantity']
                OldQuantity = request.form['OldQuantity']
                UnitPrice = request.form['UnitPrice']
                Remarks = request.form['Remarks']
                TotalPrice = float(UnitPrice) * int(Quantity)
                TotalPrice = format(TotalPrice, '.2f')
                sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                cursor.execute(sql.format(iid=iid))
                inventory = cursor.fetchall()
                for i in inventory:
                    Stock = i['Stock']
                NewStock = int(Stock) - int(OldQuantity) + int(Quantity)
                updateLinesql='UPDATE tbl_AddStock SET Date="{Date}", Quantity="{Quantity}", UnitPrice={UnitPrice}, TotalPrice={TotalPrice}, Remarks="{Remarks}" WHERE AddID={aid}'
                cursor.execute(updateLinesql.format(Date=Date, Quantity=Quantity, UnitPrice=UnitPrice, TotalPrice=TotalPrice, Remarks=Remarks, aid=aid))
                updatesql='UPDATE tbl_Inventory SET Stock={NewStock} WHERE InventoryID={InventoryID}'
                cursor.execute(updatesql.format(NewStock=NewStock, InventoryID=InventoryID))
                connection.commit()
                return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
            else:
                return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory/<int:iid>/view/usageManagement/add", methods=['POST', 'GET']) #new
def usageManagement(id, iid):  
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id) 
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
            project = cursor.fetchall()
            if request.method == 'POST':
                InventoryID = request.form['InventoryID']
                Date = request.form['Date']
                Quantity = request.form['Quantity']
                ProjectID = request.form['ProjectID']
                Remarks = request.form['Remarks']
                sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                cursor.execute(sql.format(iid=iid))
                inventory = cursor.fetchall()
                for i in inventory:
                    Stock = i['Stock']
                if int(Stock) >= int(Quantity):
                    NewStock = int(Stock) - int(Quantity)
                    insertsql='INSERT INTO tbl_UsageManagement(InventoryID, Date, Quantity, Remarks, ProjectID, UpdatedBy) VALUES ({InventoryID}, "{Date}", "{Quantity}", "{Remarks}", {ProjectID}, {UpdatedBy})'
                    cursor.execute(insertsql.format(InventoryID=InventoryID, Date=Date, Quantity=Quantity, Remarks=Remarks, ProjectID=ProjectID, UpdatedBy=id))
                    updatesql='UPDATE tbl_Inventory SET Stock={NewStock} WHERE InventoryID={InventoryID}'
                    cursor.execute(updatesql.format(NewStock=NewStock, InventoryID=InventoryID))
                    connection.commit()
                    return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
                else: 
                    sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                    cursor.execute(sql.format(iid=iid))
                    inventory = cursor.fetchall()
                    sql = 'SELECT * FROM tbl_AddStock WHERE InventoryID={iid}'
                    cursor.execute(sql.format(iid=iid))
                    addStockLine = cursor.fetchall()
                    sql = 'SELECT * FROM tbl_UsageManagement WHERE InventoryID={iid}'
                    cursor.execute(sql.format(iid=iid))
                    usageLine = cursor.fetchall()
                    return render_template('staffInventoryView.html', user=user, inventory=inventory, addStockLine=addStockLine, usageLine=usageLine, status="Stock not enough", role=role, project=project)
            else:
                return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/inventory/<int:iid>/view/usageManagement/<int:uid>", methods=['POST', 'GET']) #new
def editUsageManagement(id, iid, uid): 
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
            project = cursor.fetchall()
            if request.method == 'POST':
                InventoryID = request.form['InventoryID']
                Date = request.form['Date']
                Quantity = request.form['Quantity']
                OldQuantity = request.form['OldQuantity']
                ProjectID = request.form['ProjectID']
                Remarks = request.form['Remarks']
                sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                cursor.execute(sql.format(iid=iid))
                inventory = cursor.fetchall()
                for i in inventory:
                    Stock = i['Stock']
                if (int(Stock) + int(OldQuantity) - int(Quantity)) >= 0:
                    NewStock = int(Stock) + int(OldQuantity) - int(Quantity)
                    updateLinesql='UPDATE tbl_UsageManagement SET Date="{Date}", Quantity="{Quantity}", ProjectID={ProjectID}, UpdatedBy={UpdatedBy}, Remarks="{Remarks}" WHERE UsageID={uid}'
                    cursor.execute(updateLinesql.format(Date=Date, Quantity=Quantity, Remarks=Remarks, ProjectID=ProjectID, UpdatedBy=id, uid=uid))
                    updatesql='UPDATE tbl_Inventory SET Stock={NewStock} WHERE InventoryID={InventoryID}'
                    cursor.execute(updatesql.format(NewStock=NewStock, InventoryID=InventoryID))
                    connection.commit()
                    return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
                else: 
                    sql = 'SELECT * FROM tbl_Inventory WHERE InventoryID={iid}'
                    cursor.execute(sql.format(iid=iid))
                    inventory = cursor.fetchall()
                    sql = 'SELECT * FROM tbl_AddStock WHERE InventoryID={iid}'
                    cursor.execute(sql.format(iid=iid))
                    addStockLine = cursor.fetchall()
                    sql = 'SELECT * FROM tbl_UsageManagement WHERE InventoryID={iid}'
                    cursor.execute(sql.format(iid=iid))
                    usageLine = cursor.fetchall()
                    return render_template('staffInventoryView.html', user=user, inventory=inventory, addStockLine=addStockLine, usageLine=usageLine, status="Stock not enough", role=role, project=project)
            else:
                return redirect('/staff/{id}/inventory/{iid}/view'.format(id=id, iid=iid))
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/income", methods=['POST', 'GET']) #new
def income(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_IncomeExpenses WHERE Type="Income"')
            income = cursor.fetchall()
            return render_template('staffIncome.html', user=user, income=income, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/expenses", methods=['POST', 'GET']) #new
def expenses(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_IncomeExpenses WHERE Type="Expenses"')
            expenses = cursor.fetchall()
            return render_template('staffExpenses.html', user=user, expenses=expenses, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addIncome", methods=['POST', 'GET']) #new
def addIncome(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
            project = cursor.fetchall()
            cursor.execute('SELECT * FROM tbl_UserManagement')
            allUser = cursor.fetchall()  
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                Details = request.form['Details']
                Date = request.form['Date']
                Category = request.form['Category']
                Attachment = request.files['Attachment']
                Amount = request.form['Amount']
                ClaimedBy = request.form['ClaimedBy']
                insertsql='INSERT INTO tbl_IncomeExpenses(ProjectID, Details, Type, Date, Category, Amount, Attachment, ClaimedBy) VALUES ("{ProjectID}", "{Details}", "Income", "{Date}", "{Category}", {Amount}, "{Attachment}", {ClaimedBy})'
                cursor.execute(insertsql.format(ProjectID=ProjectID, Details=Details, Date=Date, Category=Category, Attachment=Attachment.filename, Amount=Amount, ClaimedBy=ClaimedBy))
                connection.commit()
                for file in request.files.getlist("Attachment"):
                    try:
                        container_client_incomeexpenses.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                        status='NameDup'
                #Attachment.save(os.path.join(app.config['UPLOAD_FOLDER_IE'], Attachment.filename))
                return redirect('/staff/{id}/income'.format(id=id))
            else: 
                return render_template('staffIncomeAdd.html', user=user, project=project, allUser=allUser, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/addExpenses", methods=['POST', 'GET']) #new
def addExpenses(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
            project = cursor.fetchall()
            cursor.execute('SELECT * FROM tbl_UserManagement')
            allUser = cursor.fetchall()  
            if request.method == 'POST':
                ProjectID = request.form['ProjectID']
                Details = request.form['Details']
                Date = request.form['Date']
                Category = request.form['Category']
                Attachment = request.files['Attachment']
                Amount = request.form['Amount']
                ClaimedBy = request.form['ClaimedBy']
                insertsql='INSERT INTO tbl_IncomeExpenses(ProjectID, Details, Type, Date, Category, Amount, Attachment, ClaimedBy) VALUES ("{ProjectID}", "{Details}", "Expenses", "{Date}", "{Category}", {Amount}, "{Attachment}", {ClaimedBy})'
                cursor.execute(insertsql.format(ProjectID=ProjectID, Details=Details, Date=Date, Category=Category, Attachment=Attachment.filename, Amount=Amount, ClaimedBy=ClaimedBy))
                connection.commit()
                for file in request.files.getlist("Attachment"):
                    try:
                        container_client_incomeexpenses.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                #Attachment.save(os.path.join(app.config['UPLOAD_FOLDER_IE'], Attachment.filename))
                return redirect('/staff/{id}/expenses'.format(id=id))
            else: 
                return render_template('staffExpensesAdd.html', user=user, project=project, allUser=allUser, role=role)
    else: 
        return render_template('404.html'), 404

'''
@app.route("/staff/<int:id>/IncomeExpenses/<int:ieid>/download", methods=['POST', 'GET']) #new
def IEDownload(id, ieid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT Attachment FROM tbl_IncomeExpenses WHERE IEID={ieid}'
            cursor.execute(sql.format(ieid=ieid))
            attachment = cursor.fetchall()
            for i in attachment: 
                return send_from_directory(app.config['UPLOAD_FOLDER_IE'], i['Attachment'], as_attachment=True)
    else: 
        return render_template('404.html'), 404
'''
                
@app.route("/staff/<int:id>/IncomeExpenses/<int:ieid>/edit", methods=['POST', 'GET']) #new
def editIE(id, ieid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:

            if request.method == 'POST':
                Details = request.form['Details']
                Date = request.form['Date']
                Category = request.form['Category']
                Amount = request.form['Amount']
                insertsql='UPDATE tbl_IncomeExpenses SET Details="{Details}", Date="{Date}", Category="{Category}", Amount={Amount} WHERE IEID={ieid}'
                cursor.execute(insertsql.format(Details=Details, Date=Date, Category=Category, Amount=Amount, ieid=ieid))
                connection.commit()
            user = getUserInfo(id)
            role = getRole(id)
            sql = 'SELECT * FROM tbl_IncomeExpenses WHERE IEID={ieid}'
            cursor.execute(sql.format(ieid=ieid))
            record = cursor.fetchall()
            cursor.execute('SELECT * FROM tbl_UserManagement')
            allUser = cursor.fetchall()  
            cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
            project = cursor.fetchall()
            return render_template('staffIEEdit.html', user=user, record=record, allUser=allUser, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/IncomeExpenses/<int:ieid>/edit/submitpic", methods=['POST', 'GET']) #new
def editIESubmitPic(id, ieid):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                Attachment = request.files['Attachment']
                for file in request.files.getlist("Attachment"):
                    try:
                        container_client_incomeexpenses.upload_blob(file.filename, file) # upload the file to the container using the filename as the blob name
                        filenames += file.filename + "<br /> "                    
                    except Exception as e:
                        print(e)
                        print("Ignoring duplicate filenames") # ignore duplicate filenames
                        status='NameDup'
                #Attachment.save(os.path.join(app.config['UPLOAD_FOLDER_IE'], Attachment.filename))
                sql = 'UPDATE tbl_IncomeExpenses SET Attachment="{Attachment}" WHERE IEID={IEID}'
                cursor.execute(sql.format(Attachment=Attachment.filename, IEID=ieid))
                connection.commit()
                return redirect('/staff/{id}/IncomeExpenses/{IEID}/edit'.format(id=id, IEID=ieid))
            else:
                sql = 'SELECT * FROM tbl_IncomeExpenses WHERE IEID={ieid}'
                cursor.execute(sql.format(ieid=ieid))
                record = cursor.fetchall()
                cursor.execute('SELECT * FROM tbl_UserManagement')
                allUser = cursor.fetchall()  
                cursor.execute('SELECT * FROM tbl_Project WHERE ProjectStatus <> "Closed"')
                project = cursor.fetchall()
                return render_template('staffIEEdit.html', user=user, record=record, allUser=allUser, project=project, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/IncomeExpenses/export", methods=['POST', 'GET']) #new
def IEexport(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            return render_template('staffIEReport.html', user=user, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/IncomeExpenses/export/download", methods=['POST', 'GET']) #new
def IEexportDownload(id):
    if checkLoginStatus(id) == True:
        if request.method == 'POST':
            Type = request.form['Type']
            fromDate = request.form['fromDate']
            toDate = request.form['toDate']
            sql = "SELECT * FROM tbl_IncomeExpenses WHERE Type='{Type}' AND Date BETWEEN '{fromDate}' AND '{toDate}'" 
            query = sql.format(Type=Type, fromDate=fromDate, toDate=toDate)
            print(query)
            df = pd.read_sql_query(query, conn)  # Read data into a pandas DataFrame
            conn.close()
            excel_file_path = "output_data.xlsx" # Export the data from the DataFrame to an Excel file
            df.to_excel(excel_file_path, index=False)
            return send_file(excel_file_path, as_attachment=True)
        else:
            return redirect('/staff/{id}/IncomeExpenses/export'.format(id=id))
    else: 
        return render_template('404.html'), 404
        
@app.route("/staff/<int:id>/profileCreation", methods=['POST', 'GET']) #new
def profileCreation(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                accType = request.form['accType']
                name = request.form['name']
                phoneNo = request.form['phoneNo']
                email = request.form['email']
                password = request.form['password']
                confirmPassword = request.form['confirmPassword']
                if confirmPassword == password:
                    cursor.execute('SELECT * FROM tbl_UserManagement')
                    result = cursor.fetchall()
                    for i in result:
                        if int(i['PhoneNo']) == int(phoneNo):
                            return render_template('staffProfileCreation.html', user=user, status='phoneNodup',  role=role)
                        if i['Email'] == email:
                            return render_template('staffProfileCreation.html', user=user, status='emaildup', role=role)   
                    insertsql='INSERT INTO tbl_UserManagement(Password, Name, Email, PhoneNo, Role, LoginStatus) VALUES ("{password}", "{name}", "{email}", "{phoneNo}", "{role}", 0)'
                    cursor.execute(insertsql.format(password=password, name=name, phoneNo=phoneNo, email=email, role=accType))
                    connection.commit()
                    return render_template('staffProfileCreation.html', user=user, status='success', role=role)
                else:
                    return render_template('staffProfileCreation.html', user=user, status='invalidConfirmPassword', role=role)
            else: 
                return render_template('staffProfileCreation.html', user=user, role=role)
    else: 
        return render_template('404.html'), 404

@app.route("/staff/<int:id>/profileEdit", methods=['POST', 'GET']) #new
def profileEdit(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getUserInfo(id)
            role = getRole(id)
            if request.method == 'POST':
                name = request.form['name']
                phoneNo = request.form['phoneNo']
                email = request.form['email']
                password = request.form['password']
                sql = 'SELECT * FROM tbl_UserManagement WHERE UserID<>{UserID}'
                cursor.execute(sql.format(UserID=id))
                result = cursor.fetchall()
                for i in result:
                    if int(i['PhoneNo']) == int(phoneNo):
                        return render_template('staffProfileCreation.html', user=user, status='phoneNodup', role=role)
                    if i['Email'] == email:
                        return render_template('staffProfileCreation.html', user=user, status='emaildup', role=role)   
                insertsql='UPDATE tbl_UserManagement SET password="{password}", name="{name}", email="{email}", phoneNo="{phoneNo}" WHERE UserID={UserID}'
                cursor.execute(insertsql.format(password=password, name=name, phoneNo=phoneNo, email=email, UserID=id))
                connection.commit()
                user = getUserInfo(id)
                return render_template('staffProfileEdit.html', user=user, status='success', role=role)
            else: 
                return render_template('staffProfileEdit.html', user=user, role=role)
    else: 
        return render_template('404.html'), 404
    
@app.route("/staff/<int:id>/logout", methods=['GET']) #new
def staffLogout(id):
    if checkLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'UPDATE tbl_UserManagement set loginStatus=0 where userID={id};'
            cursor.execute(sql.format(id=id))
            connection.commit()
        return redirect('/')
    else: 
        return render_template('404.html'), 404
    
"Customer app route"
@app.route("/customer") #new 
def customerLogin():
    return render_template('customerLogin.html')

@app.route("/customer/login", methods=['POST', 'GET']) #new
def customerLoginValidation():
    with connection.cursor() as cursor:
        if request.method == 'POST':
            Email = request.form['Email']
            password = request.form['password']
            sql = 'SELECT CustomerID, Password from tbl_Customer WHERE Email="{Email}"'
            cursor.execute(sql.format(Email=Email))
            result = cursor.fetchall()
            for i in result: 
                if i['Password'] == password:
                    id = i['CustomerID']
                    sql = 'UPDATE tbl_Customer set loginStatus=1 where CustomerID={id};'
                    cursor.execute(sql.format(id=id))
                    connection.commit()
                    return redirect('/customer/{id}/home'.format(id=id))
                else: 
                    return render_template('customerLogin.html', status='fail')
            return render_template('customerLogin.html', status='fail')
        else:
            return render_template('customerLogin.html')

@app.route("/customer/forgotPassword")
def customerForgotPassword():
    return render_template('customerForgotPassword.html')

@app.route("/customer/forgotPassword/email", methods=['GET', 'POST'])
def customerPassword():
    with connection.cursor() as cursor:
        if request.method =='POST':
            PhoneNo = request.form['PhoneNo'].strip()
            Email = request.form['Email'].strip()
            with connection.cursor() as cursor:        
                cursor.execute('SELECT * from tbl_Customer')
                result = cursor.fetchall()
                for i in result: 
                    if int(i['PhoneNo']) == int(PhoneNo):   
                        if i['Email'] == Email:
                            subject = 'Forgot password'
                            message = 'Your Customer ID: {CustomerID} <br> <br>' \
                                'Your Password: {Password}<br> <br>'. format(CustomerID=i['CustomerID'] , Password=i['Password'] )
                            sendemail(Email, subject, message)
                            return render_template('customerForgotPassword.html', status='sent')  
                return render_template('customerForgotPassword.html', status='fail')
        else: 
            return redirect('/customer/forgotPassword')

@app.route("/customer/<int:id>/home", methods=['POST', 'GET']) #new
def customerHome(id):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            updateActivityStatus()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity, tbl_ActivityAssign WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND tbl_ActivityAssign.ActivityID = tbl_Activity.ActivityID AND ActivityEndDate>=curdate() AND tbl_Customer.CustomerID={id} AND ActivityStatus <> "Deleted"'
            cursor.execute(sql.format(id=id))
            activity = cursor.fetchall()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND tbl_Customer.CustomerID={id}'
            cursor.execute(sql.format(id=id))
            quote = cursor.fetchall()
            sql ='SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND tbl_Customer.CustomerID={id}'
            cursor.execute(sql.format(id=id))
            invoice = cursor.fetchall()
            return render_template('home.html', user=user, activity=activity, quote=quote, invoice=invoice, role='Customer')
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/customer/<int:cusid>/view", methods=['POST', 'GET']) #new
def customerViewcustomer(id, cusid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            sql = 'SELECT * FROM tbl_Customer WHERE CustomerID={cusid}'
            cursor.execute(sql.format(cusid=cusid))
            customer = cursor.fetchall()
            return render_template('staffCustomerView.html', user=user, customer=customer, role='Customer')
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/project/<int:pid>/view", methods=['POST', 'GET']) #new
def customerViewProject(id, pid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND tbl_Project.ProjectID = {pid}'
            cursor.execute(sql.format(pid=pid))
            activity = cursor.fetchall()
            return render_template('staffProjectView.html', user=user, project=project,activity=activity, role='Customer')
    else: 
        return render_template('404.html'), 404

'''
@app.route("/customer/<int:id>/project/<int:pid>/download", methods=['POST', 'GET']) #new
def customerProjectDownload(id, pid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT ProjectAttachment FROM tbl_Project WHERE ProjectID={pid}'
            cursor.execute(sql.format(pid=pid))
            project = cursor.fetchall()
            for i in project: 
                return send_from_directory(app.config['UPLOAD_FOLDER'], i['ProjectAttachment'], as_attachment=True)
    else: 
        return render_template('404.html'), 404
'''
        
@app.route("/customer/<int:id>/quote/<int:qid>/view", methods=['POST', 'GET']) #new
def customerViewQuote(id, qid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotation = cursor.fetchall()
            sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotationLine = cursor.fetchall()
            return render_template('customerQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, role="Customer")
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/quote/<int:qid>/view/confirm", methods=['POST', 'GET']) #new
def customerConfirmQuotation(id, qid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            if request.method == 'POST':
                ConfirmedWith = request.form['ConfirmedWith']
                ConfirmedTime = request.form['ConfirmedTime']
                sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotation = cursor.fetchall()
                sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotationLine = cursor.fetchall()
                for i in quotation: 
                    ProjectID = i['ProjectID']
                    ProjectStatus = i['ProjectStatus']
                    QuotationStatus = i['QuotationStatus']
                    TotalAmount = i['GrantTotal']
                if ProjectStatus == 'Quotation Pending for Confirmation':
                    if QuotationStatus == 'Pending for Confirmation':
                        updateQuotationSQL = 'UPDATE tbl_Quotation SET QuotationStatus="Confirmed", ConfirmedWith="{ConfirmedWith}", ConfirmedTime="{ConfirmedTime}" WHERE QuotationID={QuotationID}'
                        cursor.execute(updateQuotationSQL.format(ConfirmedWith=ConfirmedWith, ConfirmedTime=ConfirmedTime, QuotationID=qid))
                        updateProjectSQL = 'UPDATE tbl_Project SET ProjectStatus="Project Start", TotalAmount={TotalAmount} WHERE ProjectID={ProjectID}'
                        cursor.execute(updateProjectSQL.format(ProjectID=ProjectID, TotalAmount=TotalAmount))
                        connection.commit()
                        return redirect('/customer/{id}/quote/{qid}/view'.format(id=id, qid=qid))
                    else:
                        return render_template('customerQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, role="Customer", status = 'Invalid Confirm Quotation Status')
                else:
                    return render_template('customerQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, role="Customer", status = 'Invalid Confirm Project Status')
            else: 
                return redirect('/customer/{id}/quote/{qid}/view'.format(id=id, qid=qid))
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/quote/<int:qid>/view/reject", methods=['POST', 'GET']) #new
def customerRejectQuotation(id, qid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            if request.method == 'POST':
                ConfirmedWith = request.form['ConfirmedWith']
                ConfirmedTime = request.form['ConfirmedTime']
                sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotation = cursor.fetchall()
                sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
                cursor.execute(sql.format(QuotationID=qid))
                quotationLine = cursor.fetchall()
                for i in quotation: 
                    ProjectID = i['ProjectID']
                    ProjectStatus = i['ProjectStatus']
                    QuotationStatus = i['QuotationStatus']
                if ProjectStatus == 'Quotation Pending for Confirmation':
                    if QuotationStatus == 'Pending for Confirmation':
                        updateQuotationSQL = 'UPDATE tbl_Quotation SET QuotationStatus="Rejected", ConfirmedWith="{ConfirmedWith}", ConfirmedTime="{ConfirmedTime}" WHERE QuotationID={QuotationID}'
                        cursor.execute(updateQuotationSQL.format(ConfirmedWith=ConfirmedWith, ConfirmedTime=ConfirmedTime, QuotationID=qid))
                        updateProjectSQL = 'UPDATE tbl_Project SET ProjectStatus="Pending for Quotation" WHERE ProjectID={ProjectID}'
                        cursor.execute(updateProjectSQL.format(ProjectID=ProjectID))
                        connection.commit()
                        return redirect('/customer/{id}/quote/{qid}/view'.format(id=id, qid=qid))
                    else:
                        return render_template('customerQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, role="Customer", status = 'Invalid Confirm Quotation Status')
                else:
                    return render_template('customerQuoteView.html', user=user, quotation=quotation, quotationLine=quotationLine, role="Customer", status = 'Invalid Confirm Project Status')
            else: 
                return redirect('/customer/{id}/quote/{qid}/view'.format(id=id, qid=qid))
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/quote/<int:qid>/view/report", methods=['POST', 'GET']) #new
def customerViewQuoteReport(id, qid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Quotation WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Quotation.ProjectID AND QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotation = cursor.fetchall()
            sql = 'SELECT * FROM tbl_QuotationLine WHERE QuotationID="{QuotationID}"'
            cursor.execute(sql.format(QuotationID=qid))
            quotationLine = cursor.fetchall()
            rendered = render_template('staffQuoteReport.html', quotation=quotation, quotationLine=quotationLine)
            responsestring = pdfkit.from_string(rendered, False, options={"enable-local-file-access": ""})
            response = make_response(responsestring)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment;filename=quotation.pdf'      
            return response
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/invoice/<int:iid>/view", methods=['POST', 'GET']) #new
def customerViewInvoice(id, iid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            return render_template('customerInvoiceView.html', user=user, invoice=invoice, invoiceLine=invoiceLine, role='Customer')
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/invoice/<int:iid>/view/report", methods=['POST', 'GET']) #new
def customerViewInvoiceReport(id, iid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Invoice WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Invoice.ProjectID AND InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoice = cursor.fetchall()
            sql = 'SELECT * FROM tbl_InvoiceLine WHERE InvoiceID="{InvoiceID}"'
            cursor.execute(sql.format(InvoiceID=iid))
            invoiceLine = cursor.fetchall()
            rendered = render_template('staffInvoiceReport.html', invoice=invoice, invoiceLine=invoiceLine)
            responsestring = pdfkit.from_string(rendered, False, options={"enable-local-file-access": ""})
            response = make_response(responsestring)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment;filename=invoice.pdf'      
            return response
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/activity/<int:aid>/view", methods=['POST', 'GET']) #pending
def customerViewActivity(id, aid):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            updateActivityStatus()
            sql = 'SELECT * FROM tbl_Project, tbl_Customer, tbl_Activity WHERE tbl_Project.CustomerID=tbl_Customer.CustomerID AND tbl_Project.ProjectID = tbl_Activity.ProjectID AND ActivityID="{ActivityID}"'
            cursor.execute(sql.format(ActivityID=aid))
            activity = cursor.fetchall()
            sql = 'SELECT * FROM tbl_ActivityAssign, tbl_UserManagement WHERE tbl_ActivityAssign.UserID=tbl_UserManagement.UserID AND ActivityID="{ActivityID}"'
            cursor.execute(sql.format(ActivityID=aid))
            ActivityAssign = cursor.fetchall()
            return render_template('staffActivityView.html', user=user, activity=activity, ActivityAssign=ActivityAssign, role='Customer')
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/profileEdit", methods=['POST', 'GET']) #new
def customerEditProfile(id):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            user = getCustomerInfo(id)
            sql = 'SELECT * FROM tbl_Customer WHERE CustomerID={cusid}'
            cursor.execute(sql.format(cusid=id))
            customer = cursor.fetchall()
            if request.method == 'POST':
                Password = request.form['Password']
                CompanyName = request.form['CompanyName']
                ContactPerson = request.form['ContactPerson']
                PhoneNo = request.form['PhoneNo']
                Email = request.form['Email']
                SecondContact = request.form['SecondContact']
                SecondContactEmail = request.form['SecondContactEmail']
                SecondContactPhone = request.form['SecondContactPhone']
                BillingAddress = request.form['BillingAddress']
                PrimaryAddress = request.form['PrimaryAddress']
                CompanyType = request.form['CompanyType']
                sql = 'SELECT * FROM tbl_Customer WHERE CustomerID!={cusid}'
                cursor.execute(sql.format(cusid=id))
                result = cursor.fetchall()
                for i in result:
                    if int(i['PhoneNo']) == int(PhoneNo):
                        return render_template('customerEditProfile.html', user=user, customer=customer, status='phoneNodup', role='Customer')
                    if i['Email'] == Email:
                        return render_template('customerEditProfile.html', user=user, customer=customer, status='emaildup', role='Customer')   
                if SecondContact == ('' or 'None'):
                    updatesql='UPDATE tbl_Customer SET Password="{Password}", CompanyName="{CompanyName}", ContactPerson="{ContactPerson}", PhoneNo={PhoneNo}, Email="{Email}", BillingAddress="{BillingAddress}",PrimaryAddress="{PrimaryAddress}", CompanyType="{CompanyType}" WHERE CustomerID={cusid}'
                    cursor.execute(updatesql.format(Password=Password, CompanyName=CompanyName, ContactPerson=ContactPerson, PhoneNo=PhoneNo, Email=Email, BillingAddress=BillingAddress, PrimaryAddress=PrimaryAddress, CompanyType=CompanyType, cusid=id))
                    connection.commit()
                else:
                    updatesql='UPDATE tbl_Customer SET Password="{Password}", CompanyName="{CompanyName}", ContactPerson="{ContactPerson}", PhoneNo={PhoneNo}, Email="{Email}", SecondContact="{SecondContact}", SecondContactEmail="{SecondContactEmail}",SecondContactPhone="{SecondContactPhone}", BillingAddress="{BillingAddress}",PrimaryAddress="{PrimaryAddress}", CompanyType="{CompanyType}" WHERE CustomerID={cusid}'
                    cursor.execute(updatesql.format(Password=Password, CompanyName=CompanyName, ContactPerson=ContactPerson, PhoneNo=PhoneNo, Email=Email, SecondContact=SecondContact, SecondContactEmail=SecondContactEmail, SecondContactPhone=SecondContactPhone, BillingAddress=BillingAddress, PrimaryAddress=PrimaryAddress, CompanyType=CompanyType, cusid=id))
                    connection.commit() 
                user = getCustomerInfo(id)
                sql = 'SELECT * FROM tbl_Customer WHERE CustomerID={cusid}'
                cursor.execute(sql.format(cusid=id))
                customer = cursor.fetchall()            
                return render_template('customerEditProfile.html', user=user, customer=customer, status='success', role='Customer')
            else: 
                return render_template('customerEditProfile.html', user=user, customer=customer, role='Customer')
    else: 
        return render_template('404.html'), 404

@app.route("/customer/<int:id>/logout", methods=['GET']) #new
def customerLogout(id):
    if checkCustomerLoginStatus(id) == True:
        with connection.cursor() as cursor:
            sql = 'UPDATE tbl_Customer set loginStatus=0 where CustomerID={id};'
            cursor.execute(sql.format(id=id))
            connection.commit()
            return redirect('/')
    else: 
        return render_template('404.html'), 404
    
"Error handling"
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(InterfaceError)
def handle_interface_error(error):
    # Log the error, inform the user, etc.
    return render_template('500.html'), 500

if __name__=='__main__':
    app.run(debug=True)
