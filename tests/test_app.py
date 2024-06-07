import pytest
from app import app, get_session
from unittest.mock import patch, MagicMock
from models import User, ReimbursementRequest , Document , Department ,RequestType
from flask import session
import io
from crud import delete_request_type, update_request_type

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'your_secret_key'
    with app.test_client() as client:
        with app.app_context():
            yield client

class MockCursor:
    def __init__(self):
        self.fetchall_data = None
        self.data = None

    def execute(self, query, params=None):
        pass

    def fetchone(self):
        return self.data

    def fetchall(self):
        return self.fetchall_data if self.fetchall_data is not None else []

    def close(self):
        pass

    def commit(self):
        self.commit_called = True

@pytest.fixture
def mock_db():
    mock_cursor = MockCursor()
    with patch('flask_mysqldb.MySQL.connection', new_callable=MagicMock) as mock_conn:
        mock_conn.cursor.return_value = mock_cursor
        yield mock_cursor
        


def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Home' in response.data

def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_register_user(client, mock_db):
    response = client.post('/register', data=dict(
        first_name='Dikshita',
        last_name='Patidar',
        email='dikshita@nucleusteq.com',
        password='dikshita',
        department='1'  
    ), follow_redirects=True)
    assert response.status_code == 200
    
def test_login_user(client, mock_db):
    response = client.post('/login', data=dict(
        email='dikshita@nucluesteq.com',
        password='dikshita'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Home' in response.data

def test_logout_user(client, mock_db):
    client.post('/login', data=dict(
        email='dikshita@nucluesteq.com',
        password='dikshita'
    ), follow_redirects=True)

    response = client.get('/logout', follow_redirects=True)

    assert response.status_code == 200
    assert b'Home' in response.data
    assert b'Login' in response.data

def test_admin_dashboard(client):
    mock_user = MagicMock(spec=User)
    mock_user.user_id = 1
    mock_user.role = 'Admin'
    mock_user.user_status = 'active'

    mock_pending_user = MagicMock(spec=User)
    mock_pending_user.role = 'pending'
    
    mock_request = MagicMock(spec=ReimbursementRequest)

    mock_session = MagicMock()
    mock_query = mock_session.query
    mock_query.return_value.filter_by.return_value.all.side_effect = [[mock_pending_user], [mock_request]]

    with patch('database.get_session', return_value=mock_session):
        with client.session_transaction() as sess:
            sess['user_id'] = mock_user.user_id
            sess['role'] = mock_user.role

        response = client.get('/admin_dashboard')

    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data

def test_pending_user_registration(client):
    mock_inactive_user = MagicMock(spec=User)
    mock_inactive_user.user_status = 'Inactive'

    mock_manager = MagicMock(spec=User)
    mock_manager.role = 'manager'
    mock_manager.user_id = 1

    mock_session = MagicMock()
    mock_query = mock_session.query
    mock_query.return_value.filter_by.return_value.options.return_value.all.return_value = [mock_inactive_user]
    mock_query.return_value.filter_by.return_value.all.return_value = [mock_manager]

    with patch('database.get_session', return_value=mock_session):
        response = client.get('/pending_user_registration')

    assert response.status_code == 200
    assert b'Pending User Registration' in response.data
    
def test_approve_user(client):
    mock_admin_user = MagicMock(spec=User)
    mock_admin_user.role = 'Admin'
    
    mock_user = MagicMock(spec=User)
    mock_user.user_id = 1

    mock_request = MagicMock()
    mock_request.form.get.side_effect = ['employee', mock_user.user_id]

    mock_session = MagicMock()
    mock_query = mock_session.query
    mock_query.return_value.get.return_value = mock_user

    with patch('app.request', mock_request), patch('database.get_session', return_value=mock_session):
        with client.session_transaction() as sess:
            sess['role'] = mock_admin_user.role
        response = client.post('/approve_user/1', data={'role': 'employee', 'manager_id': mock_user.user_id})
    assert response.status_code == 302

def test_reject_user(client):
    mock_user = MagicMock(spec=User)
    mock_user.user_id = 1
    mock_user.role = 'Admin'
    mock_user.user_status = 'active'

    mock_rejected_user = MagicMock(spec=User)
    mock_rejected_user.user_id = 2
    mock_rejected_user.email = 'abc@nucleusteq.com'

    mock_session = MagicMock()
    mock_query = mock_session.query
    mock_query.return_value.get.return_value = mock_rejected_user

    with patch('database.get_session', return_value=mock_session):
        with client.session_transaction() as sess:
            sess['user_id'] = mock_user.user_id
            sess['role'] = mock_user.role

        response = client.post(f'/reject_user/{mock_rejected_user.user_id}', follow_redirects=True)

    assert response.status_code == 200

def test_reimbursement_request_tracking(client):
    mock_reimbursement_request = MagicMock()
    mock_reimbursement_request.request_id = 1
    mock_reimbursement_request.employee_id = 1

    mock_session = MagicMock()

    with patch('crud.get_session', return_value=mock_session):
        with patch('crud.get_all_reimbursement_requests', return_value=[mock_reimbursement_request]):
            response = client.get('/reimbursement_request_tracking')

    assert response.status_code == 200
    
def test_manage_departments(client):
    mock_department1 = MagicMock(spec=Department)
    mock_department1.department_id = 1
    mock_department1.name = 'HR'

    mock_department2 = MagicMock(spec=Department)
    mock_department2.department_id = 2
    mock_department2.name = 'IT'

    mock_session = MagicMock()
    mock_session.query.return_value.order_by.return_value.all.return_value = [mock_department1, mock_department2]

    with patch('crud.get_session', return_value=mock_session):
        response = client.get('/manage_departments')

    assert response.status_code == 200
    assert b'HR' in response.data
    assert b'IT' in response.data  
      
def test_edit_user(client):
    # Mock session data
    mock_session = MagicMock()
    mock_session.__contains__.side_effect = lambda key: key in ('user_id', 'role')
    mock_session.__getitem__.side_effect = lambda key: 1 if key == 'user_id' else 'Admin'

    # Mock the get_session function
    with patch('crud.get_session', return_value=mock_session):
        # Mock query results
        mock_user = MagicMock(spec=User)
        mock_managers = [MagicMock(spec=User) for _ in range(3)]
        mock_query = mock_session.query
        mock_query.return_value.get.return_value = mock_user
        mock_query.return_value.filter_by.return_value.all.return_value = mock_managers


def test_employee_dashboard(client, mock_db):
    # Patch the get_session function to return the mock session
    with patch('database.get_session', return_value=mock_db):
        # Simulate an Employee session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Employee'
        
        # Simulate a GET request to the /employee_dashboard endpoint
        response = client.get('/employee_dashboard')
        
        # Check the response status code
        assert response.status_code == 200
        
        # Check that the correct template is rendered
        assert b'Employee Dashboard' in response.data




def test_submit_reimbursement(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['manager_id'] = 2
    
    form_data = {
        'request_type_id': '1',
        'amount': '50.00',
        'request_date': '2024-06-01',
    }
    data = {
        'document': (io.BytesIO(b"this is a test"), 'test_document.pdf'),
        **form_data
    }

    with patch('crud.get_all_request_types', return_value=[{'id': 1, 'type': 'Travel'}]), \
         patch('crud.get_amount_limit', return_value=100.00), \
         patch('crud.create_reimbursement_request', return_value=1), \
         patch('crud.create_document'):

        response = client.post('/submit_reimbursement', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
        

def test_submit_reimbursement_amount_exceeds_limit(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['manager_id'] = 2
    
    form_data = {
        'request_type_id': '1',
        'amount': '150.00',
        'request_date': '2024-06-01',
    }
    data = {
        'document': (io.BytesIO(b"this is a test"), 'test_document.pdf'),
        **form_data
    }

    with patch('crud.get_all_request_types', return_value=[{'id': 1, 'type': 'Travel'}]), \
         patch('crud.get_amount_limit', return_value=100.00), \
         patch('crud.create_reimbursement_request'), \
         patch('crud.create_document'):

        response = client.post('/submit_reimbursement', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess['message_category'] == 'danger'    
        
        
def test_history(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Employee'
    
    mock_reimbursement_request = MagicMock(spec=ReimbursementRequest)
    mock_reimbursement_request.request_id = 1
    mock_reimbursement_request.employee_id = 1

    mock_document = MagicMock(spec=Document)
    mock_document.request_id = 1

    mock_session = MagicMock()
    mock_query = mock_session.query
    mock_query.return_value.filter_by.return_value.all.side_effect = [[mock_reimbursement_request], [mock_document]]

    with patch('crud.get_session', return_value=mock_session):
        response = client.get('/history')

    assert response.status_code == 200
          
def test_manager_dashboard(client, mock_db):
    # Create a mock reimbursement request
    mock_request = MagicMock(spec=ReimbursementRequest)
    mock_request.manager_id = 1
    mock_request.status = 'pending'
    
    with patch('database.get_session', return_value=mock_db):
        # Simulate a Manager session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Manager'
        
        # Simulate a GET request to the /manager_dashboard endpoint
        response = client.get('/manager_dashboard')
        
        # Check the response status code
        assert response.status_code == 200
        
        # Check that the correct template is rendered and contains expected content
        assert b'Manager Dashboard' in response.data          

# def test_pending_requests(client, mock_db):
#     # Create mock objects
#     mock_request = MagicMock(spec=ReimbursementRequest)
#     mock_request.request_id = 1
#     mock_request.status = 'pending'
#     mock_request.manager_id = 1

#     mock_user = MagicMock(spec=User)
#     mock_user.user_id = 2

#     mock_request_type = MagicMock(spec=RequestType)
#     mock_request_type.request_type_id = 1

#     mock_document = MagicMock(spec=Document)
#     mock_document.request_id = 1

#     with patch('database.get_session', return_value=mock_db):
#         # Simulate a Manager session
#         with client.session_transaction() as sess:
#             sess['user_id'] = 1
#             sess['role'] = 'Manager'

#         # Simulate a GET request to the /pending_requests endpoint
#         response = client.get('/pending_requests')
        
#         # Check the response status code
#         assert response.status_code == 200
        
#         # Check that the correct template is rendered and contains expected content
#         assert b'Pending Reimbursement Requests' in response.data        

def test_approve_reimbursement(client, mock_db):
    mock_request = MagicMock(spec=ReimbursementRequest)
    mock_request.request_id = 1
    mock_request.manager_id = 1
    mock_request.status = 'pending'

    with patch('database.get_session', return_value=mock_db):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Manager'
        response = client.post(f'/approve_reimbursement/{mock_request.request_id}', data={'comments': 'Approved'})
        assert response.status_code == 302  
        
        
def test_delete_request_type_success(mock_db):
    request_type_id = 1
    # mock_db.data = RequestType(id=request_type_id)
    delete_request_type(request_type_id)
    

def test_delete_request_type_not_found(mock_db):
    request_type_id = 1
    mock_db.data = None
    delete_request_type(request_type_id)



@pytest.fixture
def mock_session():
    return {'user_id': 1, 'role': 'Manager'}

def test_rejected_requests_redirect_when_not_logged_in(mock_session):
    with app.test_client() as client:
        response = client.get('/rejected_requests')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'

def test_rejected_requests_redirect_when_not_manager(mock_session):
    mock_session['role'] = 'Employee'
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.update(mock_session)
        response = client.get('/rejected_requests')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'

@pytest.fixture
def mock_session():
    return {'user_id': 1, 'role': 'Admin'}

def test_edit_user_redirect_when_not_logged_in():
    with app.test_client() as client:
        response = client.get('/edit_user/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'

def test_edit_user_redirect_when_not_admin(mock_session):
    mock_session['role'] = 'Manager'
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.update(mock_session)
        response = client.get('/edit_user/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'

def test_edit_user_success(mock_session, mocker):
    
    mock_query = mocker.MagicMock()
    
    mocker.patch('database.get_session', return_value=mock_query)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.update(mock_session)
        response = client.get('/edit_user/1')
        assert response.status_code == 200

def test_update_user_redirect_when_not_logged_in():
    with app.test_client() as client:
        response = client.post('/update_user/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'

def test_update_user_redirect_when_not_admin(mock_session):
    mock_session['role'] = 'Manager'
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.update(mock_session)
        response = client.post('/update_user/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'

def test_delete_user_redirect_when_not_logged_in():
    with app.test_client() as client:
        response = client.post('/delete_user/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'
        
def test_delete_user_redirect_when_not_admin(mock_session):
    mock_session['role'] = 'Manager'
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.update(mock_session)
        response = client.post('/delete_user/1')
        assert response.status_code == 302
        assert response.location == 'http://localhost/login'
 