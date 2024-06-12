import pytest
from app import app
from flask import session
from unittest.mock import patch, MagicMock
from crud import get_document
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    with app.test_client() as client:
        with app.app_context():
            yield client

# Tests for Flask routes
@patch('app.get_session')
@patch('app.RegistrationForm')
@patch('app.create_user')
@patch('app.create_notification')
def test_register(mock_create_notification, mock_create_user, mock_RegistrationForm, mock_get_session, client):
    mock_form = MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form.first_name.data = 'John'
    mock_form.last_name.data = 'Doe'
    mock_form.email.data = 'john.doe@example.com'
    mock_form.password.data = 'password123'
    mock_form.department.data = '1'
    mock_RegistrationForm.return_value = mock_form

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_department = MagicMock()
    mock_department.department_id = 1
    mock_department.department_name = 'HR'
    mock_session.query().all.return_value = [mock_department]

    mock_user = MagicMock()
    mock_create_user.return_value = mock_user

    response = client.post('/register', data=dict(
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        password='password123',
        department='1'
    ), follow_redirects=True)

    assert response.status_code == 200
    mock_create_user.assert_called_once_with('John', 'Doe', 'john.doe@example.com', 'password123', 'pending', 'inactive', None, '1')
    mock_create_notification.assert_called_once()
    assert b'Registration successful, awaiting admin approval.' in response.data

@patch('app.get_session')
@patch('app.LoginForm')
def test_login(mock_LoginForm, mock_get_session, client):
    mock_form = MagicMock()
    mock_form.validate_on_submit.return_value = True
    mock_form.email.data = 'john.doe@nucleusteq.com'
    mock_form.password.data = 'password123'
    mock_LoginForm.return_value = mock_form

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_user = MagicMock()
    mock_user.user_status = 'active'
    mock_user.password = 'password123'
    mock_user.role = 'Employee'
    mock_user.user_id = 1
    mock_user.manager_id = None
    mock_session.query().filter_by().first.return_value = mock_user

    response = client.post('/login', data=dict(
        email='john.doe@nucleusteq.com',
        password='password123'
    ), follow_redirects=True)

    assert response.status_code == 200
    assert session['user_id'] == 1
    assert session['role'] == 'Employee'
    assert b'Employee Dashboard' in response.data  # Assuming the dashboard has this string

def test_logout(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Employee'
    
    response = client.get('/logout', follow_redirects=True)

    assert response.status_code == 200
    assert 'user_id' not in session
    assert 'role' not in session
    assert b'Home' in response.data  # Assuming the home page has this string


def test_home(client):
    """Test the home page route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Home' in response.data

def test_error(client):
    """Test the error page route."""
    response = client.get('/error')
    assert response.status_code == 200
    assert b'Error page' in response.data

@patch('app.get_session')
@patch('app.get_all_reimbursement_requests')
def test_admin_dashboard(mock_get_all_reimbursement_requests, mock_get_session, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'
    
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_user = MagicMock()
    mock_session.query().filter_by().all.return_value = [mock_user]

    mock_reimbursement_request = MagicMock()
    mock_get_all_reimbursement_requests.return_value = [mock_reimbursement_request]

    response = client.get('/admin_dashboard')

    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
    mock_get_all_reimbursement_requests.assert_called_once()
    

@patch('app.get_session')
def test_pending_user_registration(mock_get_session, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'
    
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_user_inactive = MagicMock()
    mock_user_manager = MagicMock()
    mock_session.query().filter_by().options().all.return_value = [mock_user_inactive]
    mock_session.query().filter().all.return_value = [mock_user_manager]

    response = client.get('/pending_user_registration')

    assert response.status_code == 200
    assert b'Pending User Registration' in response.data

@patch('app.get_session')
def test_approve_user(mock_get_session, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_user = MagicMock()
    mock_user.email = 'test@example.com'
    mock_session.query().get.return_value = mock_user

    response = client.post('/approve_user/1', data=dict(role='Employee', manager_id=2), follow_redirects=True)

    assert response.status_code == 200
    mock_session.commit.assert_called_once()
    assert b'User test@example.com approved successfully.' in response.data

@patch('app.get_session')
def test_reject_user(mock_get_session, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_user = MagicMock()
    mock_user.email = 'test@example.com'
    mock_session.query().get.return_value = mock_user

    response = client.post('/reject_user/1', follow_redirects=True)

    assert response.status_code == 200
    mock_session.delete.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()
    assert b'User test@example.com request rejected and deleted successfully.' in response.data
    
    

@patch('app.get_session')
@patch('app.get_all_reimbursement_requests')
def test_reimbursement_request_tracking(mock_get_all_reimbursement_requests, mock_get_session, client):
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_reimbursement_request = MagicMock()
    mock_get_all_reimbursement_requests.return_value = [mock_reimbursement_request]

    response = client.get('/reimbursement_request_tracking')

    assert response.status_code == 200
    assert b'Reimbursement Request Tracking' in response.data  # Assuming the page has this string
    mock_get_all_reimbursement_requests.assert_called_once()
    mock_session.close.assert_called_once()
    
    
    
@patch('app.get_session')
def test_manage_departments(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_department = MagicMock()
    mock_session.query().order_by().all.return_value = [mock_department]

    response = client.get('/manage_departments')
    assert response.status_code == 200
    assert b'Manage Departments' in response.data

@patch('app.get_session')
def test_add_department(mock_get_session, client):
    mock_session = mock_get_session.return_value

    response = client.post('/add_department', data=dict(department_name='IT', department_id='123'))
    assert response.status_code == 302  # Redirect status
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

@patch('app.get_session')
def test_manage_users(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_user = MagicMock()
    mock_session.query().filter().all.return_value = [mock_user]

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'

    response = client.get('/manage_users')
    assert response.status_code == 200
    assert b'Manage Users' in response.data

@patch('app.get_session')
def test_edit_user(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_user = MagicMock()
    mock_manager = MagicMock()
    mock_session.query().get.return_value = mock_user
    mock_session.query().filter().all.return_value = [mock_manager]

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'

    response = client.get('/edit_user/1')
    assert response.status_code == 200
    assert b'Edit User' in response.data

@patch('app.get_session')
def test_update_user(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_user = MagicMock()
    mock_session.query().get.return_value = mock_user

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'

    response = client.post('/update_user/1', data=dict(role='employee', manager_id='2'))
    assert response.status_code == 302  # Redirect status
    mock_user.role = 'employee'
    mock_user.manager_id = '2'
    mock_session.commit.assert_called_once()

@patch('app.get_session')
def test_delete_user(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_user = MagicMock()
    mock_session.query().get.return_value = mock_user

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'

    response = client.post('/delete_user/1')
    assert response.status_code == 302  # Redirect status
    mock_user.user_status = 'deleted'
    mock_session.commit.assert_called_once()

@patch('app.get_session')
def test_employee_dashboard(mock_get_session, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Employee'

    response = client.get('/employee_dashboard')
    assert response.status_code == 200
    assert b'Employee Dashboard' in response.data

@patch('app.get_all_request_types')
@patch('app.create_reimbursement_request')
@patch('app.create_document')
@patch('app.get_session')
def test_submit_reimbursement(mock_get_session, mock_create_document, mock_create_reimbursement_request, mock_get_all_request_types, client):
    mock_get_all_request_types.return_value = [{'request_type_id': 1, 'request_type': 'Travel'}]

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['manager_id'] = 2

    response = client.get('/submit_reimbursement')
    assert response.status_code == 200
    assert b'Submit Reimbursement' in response.data

    with open('test_document.txt', 'w') as f:
        f.write('test content')

    with open('test_document.txt', 'rb') as f:
        data = {
            'request_type_id': 1,
            'amount': '100.0',
            'request_date': '2024-01-01',
            'document': (f, 'test_document.txt')
        }

        response = client.post('/submit_reimbursement', data=data, content_type='multipart/form-data')
        assert response.status_code == 302
        mock_create_reimbursement_request.assert_called_once()
        mock_create_document.assert_called_once()

    os.remove('test_document.txt')


@patch('app.get_session')
def test_history(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_request = MagicMock()
    mock_document = MagicMock()
    mock_session.query().filter_by().all.return_value = [mock_request]
    mock_session.query().filter_by().all.return_value = [mock_document]

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Employee'

    response = client.get('/history')
    assert response.status_code == 200
    assert b'History' in response.data


@patch('app.get_session')
def test_manager_dashboard(mock_get_session, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Manager'

    response = client.get('/manager_dashboard')
    assert response.status_code == 200
    assert b'Manager Dashboard' in response.data

@patch('app.get_session')
def test_pending_requests(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_request = MagicMock()
    mock_user = MagicMock()
    mock_request_type = MagicMock()
    mock_session.query().join().join().filter().all.return_value = [(mock_request, mock_user, mock_request_type)]
    
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Manager'

    response = client.get('/pending_requests')
    assert response.status_code == 200
    

@patch('app.get_session')
def test_approve_reimbursement(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_request = MagicMock()
    mock_request.manager_id = 2
    mock_session.query().filter_by().first.return_value = mock_request

    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Manager'

    response = client.post('/approve_reimbursement/1', data={'comments': 'Approved'})
    assert response.status_code == 302
    assert mock_request.status == 'approved'
    assert mock_request.comments == 'Approved'

@patch('app.get_session')
def test_reject_reimbursement(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_request = MagicMock()
    mock_request.manager_id = 2
    mock_session.query().filter_by().first.return_value = mock_request

    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Manager'

    response = client.post('/reject_reimbursement/1', data={'comments': 'Rejected'})
    assert response.status_code == 302
    assert mock_request.status == 'rejected'
    assert mock_request.comments == 'Rejected'

@patch('app.get_session')
def test_approved_requests(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_request = MagicMock()
    mock_user = MagicMock()
    mock_request_type = MagicMock()
    mock_session.query().join().join().filter().all.return_value = [(mock_request, mock_user, mock_request_type)]
    
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Manager'

    response = client.get('/approved_requests')
    assert response.status_code == 200
    assert b'Approved Requests' in response.data

@patch('app.get_session')
def test_rejected_requests(mock_get_session, client):
    mock_session = mock_get_session.return_value
    mock_request = MagicMock()
    mock_user = MagicMock()
    mock_request_type = MagicMock()
    mock_session.query().join().join().filter().all.return_value = [(mock_request, mock_user, mock_request_type)]
    
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Manager'

    response = client.get('/rejected_requests')
    assert response.status_code == 200
    assert b'Rejected Requests' in response.data
