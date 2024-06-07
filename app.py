from flask import Flask, render_template, redirect, url_for, flash, session, request, send_from_directory
from forms import RegistrationForm, LoginForm
from models import User, Department, ReimbursementRequest
from crud import *
from database import get_session
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import or_
import os
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
role_mapping = {
    'employee': 'Employee',
    'manager': 'Manager',
    'admin': 'Admin'
}

if not app.debug:
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)

@app.route('/')
def home():
    app.logger.info('Home page accessed')
    return render_template('home.html', title='Home')


@app.route('/error')
def error():
    try:
        1 / 0
    except ZeroDivisionError as e:
        app.logger.error('An error occurred: %s', e)
    return 'Error page'


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    session = get_session()
    departments = session.query(Department).all()
    department_choices = [(str(department.department_id), department.department_name) for department in departments]

    form.department.choices = department_choices

    if form.validate_on_submit():
        try:
            department_id = form.department.data
            user = create_user(form.first_name.data, form.last_name.data, form.email.data,
                               form.password.data, 'pending', 'inactive', None, department_id)
            if user:
                flash('Registration successful, awaiting admin approval.', 'success')
                app.logger.info('Registration successful, awaiting admin approval.')

                create_notification(1, f'New user registration pending approval: {user.email}', False, datetime.utcnow())
                return redirect(url_for('login'))
        except SQLAlchemyError as e:
            flash(f'Error: {e}', 'danger')
            app.logger.error(f'Error: {e}')
    else:
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{error}", 'danger')
            
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        if not email.endswith('@nucleusteq.com'):
            flash('Invalid email domain', 'danger')
            return redirect(url_for('login'))
        
        session_db = get_session()
        user = session_db.query(User).filter_by(email=form.email.data).first()
        if user and user.user_status == 'deleted':
            flash('User is deleted.', 'danger')
            app.logger.warning('User is deleted.')
            return redirect(url_for('login'))
        
        if user and user.password == form.password.data:                 
            if user.user_status == 'inactive':
                flash('Your account is not yet activated.', 'warning')
                app.logger.warning('Account is not yet activated.')  
            else:
                session['user_id'] = user.user_id
                session['role'] = user.role
                session['manager_id'] = user.manager_id if user.manager_id else None
                app.logger.info('Login Successful')  

                if user.role == 'Admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'Employee':
                    return redirect(url_for('employee_dashboard'))
                elif user.role == 'Manager':
                    return redirect(url_for('manager_dashboard'))
        else:
            flash('Invalid Email or Password.', 'danger')
            app.logger.warning('Invalid Email or password')  
            
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    app.logger.info("log out")
    return redirect(url_for('home'))

@app.route('/download_policy')
def download_policy():
    return send_from_directory(directory='static' , path='Reimbursement Request Policy.pdf', as_attachment=True)

# ADMIN ROUTES
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    session_db = get_session()
    pending_users = session_db.query(User).filter_by(role='pending').all()
    reimbursement_requests = get_all_reimbursement_requests()
    app.logger.info("admin dashboard")
    return render_template('admin_dashboard.html', title='Admin Dashboard', pending_users=pending_users,reimbursement_requests=reimbursement_requests)

@app.route('/pending_user_registration')
def pending_user_registration():
    session = get_session()
    pending_users = session.query(User).filter_by(user_status='Inactive').options(joinedload(User.department)).all()
    managers = session.query(User).filter(or_(User.role == 'manager', User.role == 'admin'), User.user_status != 'deleted').all()
    session.close()
    app.logger.info("pending user registration. ")
    
    return render_template('pending_user_registration.html', pending_users=pending_users , managers=managers)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    role = request.form.get('role')
    manager_id = request.form.get('manager_id')

    try:
        session_db = get_session()
        user = session_db.query(User).get(user_id)
        if user:
            if not role:
                session['message'] = 'Role is mandatory for approval.'
                session['message_category'] = 'danger'
                
                return redirect(url_for('pending_user_registration'))
            elif role.lower() == 'employee' and not manager_id:
                session['message'] = 'Manager is mandatory for employee role.'
                session['message_category'] = 'danger'
                return redirect(url_for('pending_user_registration'))
            
            user.role = role_mapping.get(role.lower(), role)
            user.user_status = 'active'
            if role.lower() == 'employee':
                user.manager_id = manager_id
            session_db.commit()
            session['message'] = f'User {user.email} approved successfully.'
            session['message_category'] = 'success'
            app.logger.info("user approved by admin successfully")
        else:
            session['message'] = 'user not found'
            session['message_category'] = 'danger'
    except SQLAlchemyError as e:
        session_db.rollback()
        session['message'] = f'Error {e}.'
        session['message_category'] = 'danger'
        app.logger.error(f'Error :{e}')
    finally:
        session_db.close()
    
    return redirect(url_for('pending_user_registration'))


@app.route('/reject_user/<int:user_id>', methods=['POST'])
def reject_user(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    try:
        session_db = get_session()
        user = session_db.query(User).get(user_id)
        if user:
            session_db.delete(user)
            session_db.commit()
            session['message'] = f'User {user.email} request rejected and deleted successfully.'
            session['message_category'] = 'success'
            app.logger.info("user rejected by admin")
    except SQLAlchemyError as e:
        session_db.rollback()
        session['message'] = f'Error{e}.'
        session['message_category'] = 'danger'
        app.logger.error(f'Error :{e}')

    finally:
        session_db.close()

    return redirect(url_for('pending_user_registration'))

@app.route('/reimbursement_request_tracking')
def reimbursement_request_tracking():
    session = get_session()
    reimbursement_requests = get_all_reimbursement_requests()    
    session.close()
    app.logger.info("Reibursement form request tracking")
    return render_template('reimbursement_request_tracking.html', reimbursement_requests=reimbursement_requests)


@app.route('/manage_departments')
def manage_departments():
    session = get_session()
    departments = session.query(Department).order_by(Department.department_id.asc(  )).all()
    session.close()
    app.logger.info("Manager Dashboard")
    return render_template('manage_departments.html', departments=departments)

@app.route('/add_department', methods=['POST'])
def add_department():
    if request.method == 'POST':
        department_name = request.form['department_name']
        department_id = request.form['department_id']
        
        session = get_session()
        new_department = Department(department_name=department_name, department_id=department_id)
        session.add(new_department)
        session.commit()
        app.logger.info("Add departments")
        return redirect(url_for('manage_departments'))

@app.route('/manage_users')
def manage_users():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    session_db = get_session()
    users = session_db.query(User).filter(User.user_status.in_(['active','pending']), User.role != 'Admin').all()
    app.logger.info("Manage users")
    return render_template('manage_users.html', users=users)

@app.route('/edit_user/<int:user_id>')
def edit_user(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    session_db = get_session()
    user = session_db.query(User).get(user_id)
    managers = session_db.query(User).filter(or_(User.role == 'manager', User.role == 'admin'), User.user_status != 'deleted').all()

    app.logger.info("admin edited user details")
    return render_template('edit_user.html', user=user, managers=managers)

@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    role = request.form['role']
    manager_id = request.form['manager_id'] or None
    
    session_db = get_session()
    user = session_db.query(User).get(user_id)
    if user:
        user.role = role
        user.manager_id = manager_id
        session_db.commit()
        session['message'] = f'User {user.email} updated successfully.'
        session['message_category'] = 'success'
        app.logger.info(f"user {user.email} details updated")
    else:
        session['message'] = f'Error updating user {user.email}.'
        session['message_category'] = 'danger'
        app.logger.error(f"Error updating user {user.email} ")
    return redirect(url_for('manage_users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    
    session_db = get_session()
    user = session_db.query(User).get(user_id)
    if user:
        user.user_status = 'deleted'
        session_db.commit()
        session['message'] = f'User {user.email} deleted.'
        session['message_category'] = 'success'
        app.logger.info("user status udpated")
    else:
        session['message'] = f'Error'
        session['message_category'] = 'danger'
    
    return redirect(url_for('manage_users'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

# EMPLOYEE ROUTES
@app.route('/employee_dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['role'] != 'Employee':
        return redirect(url_for('login'))
    app.logger.info("employee dashboard")
    return render_template('employee_dashboard.html')

@app.route('/submit_reimbursement', methods=['GET', 'POST'])
def submit_reimbursement():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    request_types = get_all_request_types()

    if request.method == 'POST':
        request_type_id = request.form.get('request_type_id')
        amount = float(request.form.get('amount'))
        request_date = request.form.get('request_date')
        document = request.files['document']
        
        amount_limit =get_amount_limit(request_type_id)
        
        if amount_limit is None:
            session['message']= "Invalid request amount"
            session['message_category']='danger'
        elif amount > amount_limit:
            session['message'] = f"Amount exceeds the limit . Limit {amount_limit}"
            session['message_category']='danger'
        else:
            if document :
                
                document_filename = secure_filename(document.filename)
                document_path = os.path.join(UPLOAD_FOLDER, document_filename)
                document.save(document_path)

                try:
                    request_id = create_reimbursement_request(
                        employee_id=session['user_id'],
                        request_type_id=request_type_id,
                        amount=amount,
                        request_date=request_date,
                        manager_id=session['manager_id']
                    )
                    create_document(request_id, document_filename)
                    app.logger.info(f'Reimbursement request {request_id} submitted successfully.')
                    return redirect(url_for('employee_dashboard'))
                except SQLAlchemyError as e:
                    session['message'] = f'Error {e}.'
                    session['message_category']='danger'
                    app.logger.error(f'Error: {e}')
            
            return redirect(url_for('employee_dashboard'))

    return render_template('submit_reimbursement.html', request_types=request_types)

@app.route('/user_uploads/<filename>')
def user_uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER,filename)

@app.route('/history')
def history():
    if 'user_id' not in session or session['role'] != 'Employee':
        return redirect(url_for('login'))

    session_db = get_session()
    reimbursement_request = session_db.query(ReimbursementRequest).filter_by(employee_id=session['user_id']).all()
    reimbursement_requests = []
    for request in reimbursement_request:
        documents = session_db.query(Document).filter_by(request_id = request.request_id).all()
        reimbursement_requests.append({
            'rr': request,
            'documents':documents
        })
    session_db.close()
    app.logger.info("employee history")   
    return render_template('history.html', reimbursement_requests=reimbursement_requests)

# MANAGER ROUTES
@app.route('/manager_dashboard')
def manager_dashboard():
    if 'user_id' not in session or session['role'] != 'Manager':
        return redirect(url_for('login'))

    session_db = get_session()
    manager_id = session['user_id']
    pending_requests = session_db.query(ReimbursementRequest).filter_by(manager_id=manager_id, status='pending').all()
    app.logger.info("manager dashboard")
    return render_template('manager_dashboard.html', title='Manager Dashboard', pending_requests=pending_requests)
    


@app.route('/pending_requests')
def pending_requests():
    if 'user_id' not in session or session['role'] != 'Manager':
        return redirect(url_for('login'))
    
    session_db = get_session()
    pending_requests = (
        session_db.query(ReimbursementRequest, User,RequestType)
        .join(User, ReimbursementRequest.employee_id == User.user_id)
        .join(RequestType, ReimbursementRequest.request_type_id == RequestType.request_type_id)
        .filter(ReimbursementRequest.status == 'pending', ReimbursementRequest.manager_id == session['user_id'])
        .all()
    )

    reimbursement_requests = []
    for reimbursement_request, user,request_type in pending_requests:
        documents = session_db.query(Document).filter_by(request_id=reimbursement_request.request_id).all()
        reimbursement_requests.append({
            'request': reimbursement_request,
            'user': user,
            'request_type':request_type,
            'documents': documents
        })
    
    return render_template('pending_requests.html', pending_requests=reimbursement_requests)


@app.route('/approve_reimbursement/<int:request_id>', methods=['POST'])
def approve_reimbursement(request_id):
    if 'user_id' not in session or session['role'] != 'Manager':
        return redirect(url_for('login'))
    
    comments = request.form.get('comments')
    session_db = get_session()
    try:
        reimbursement_request = session_db.query(ReimbursementRequest).filter_by(request_id=request_id).first()
        if reimbursement_request and reimbursement_request.manager_id == session['user_id']:
            reimbursement_request.status = 'approved'
            reimbursement_request.comments = comments
            session_db.commit()
            session['message'] = 'Request Approved successfully.'
            session['message_category'] = 'success'
            app.logger.info('Request approved successfully.')
    except SQLAlchemyError as e:
        session_db.rollback()
        session['message'] = f'Error {e}.'
        session['message_category'] = 'danger'
        app.logger.error(f'Error: {e}')
    finally:
        session_db.close()
    return redirect(url_for('pending_requests'))

@app.route('/reject_reimbursement/<int:request_id>', methods=['POST'])
def reject_reimbursement(request_id):
    if 'user_id' not in session or session['role'] != 'Manager':
        return redirect(url_for('login'))
    
    comments = request.form.get('comments')
    session_db = get_session()
    try:
        reimbursement_request = session_db.query(ReimbursementRequest).filter_by(request_id=request_id).first()
        if reimbursement_request and reimbursement_request.manager_id == session['user_id']:
            reimbursement_request.status = 'rejected'
            reimbursement_request.comments = comments
            session_db.commit()
            session['message'] = 'Request rejected successfully.'
            session['message_category'] = 'success'
            app.logger.info('Request rejected successfully.')
    except SQLAlchemyError as e:
        session_db.rollback()
        session['message'] = f'Error'
        session['message_category'] = 'danger'
        app.logger.error(f'Error: {e}')
    finally:
        session_db.close()
    return redirect(url_for('pending_requests'))

@app.route('/approved_requests')
def approved_requests():
    if 'user_id' not in session or session['role'] != 'Manager':
        return redirect(url_for('login'))
    
    session_db = get_session()
    approved_requests = (
        session_db.query(ReimbursementRequest, User, RequestType)
        .join(User, ReimbursementRequest.employee_id == User.user_id)
        .join(RequestType, ReimbursementRequest.request_type_id == RequestType.request_type_id)
        .filter(ReimbursementRequest.status == 'approved', ReimbursementRequest.manager_id == session['user_id'])
        .all()
    )

    reimbursement_requests = []
    for request, user, request_type in approved_requests:
        documents = session_db.query(Document).filter_by(request_id=request.request_id).all()
        reimbursement_requests.append({
            'rr': (request, user, request_type),
            'documents': documents
        })
    session_db.close()
    app.logger.info("approved requests")
    return render_template('approved_requests.html', reimbursement_requests=reimbursement_requests)

@app.route('/rejected_requests')
def rejected_requests():
    if 'user_id' not in session or session['role'] != 'Manager':
        return redirect(url_for('login'))
    
    session_db = get_session()

    session_db = get_session()
    rejected_requests = (
        session_db.query(ReimbursementRequest, User, RequestType)
        .join(User, ReimbursementRequest.employee_id == User.user_id)
        .join(RequestType, ReimbursementRequest.request_type_id == RequestType.request_type_id)
        .filter(ReimbursementRequest.status == 'rejected', ReimbursementRequest.manager_id == session['user_id'])
        .all()
    )

    reimbursement_requests = []
    for request, user, request_type in rejected_requests:
        documents = session_db.query(Document).filter_by(request_id=request.request_id).all()
        reimbursement_requests.append({
            'rr': (request, user, request_type),
            'documents': documents
        })

    session_db.close()
    app.logger.info("rejected requests")
    return render_template('rejected_requests.html', reimbursement_requests=reimbursement_requests)

if __name__ == '__main__':
    app.run(debug=True)
