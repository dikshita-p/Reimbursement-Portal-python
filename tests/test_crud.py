import pytest
from unittest.mock import patch, MagicMock
from crud import *
from datetime import datetime

@pytest.fixture
def mock_session():
    with patch('crud.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        yield mock_session

def test_create_user(mock_session):
    mock_user = MagicMock()
    with patch('crud.User', return_value=mock_user):
        result = create_user('John', 'Doe', 'john.doe@example.com', 'password123', 'admin', 'active', 1, 1)
        mock_session.add.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()
        assert result == mock_user

def test_create_department(mock_session):
    mock_department = MagicMock()
    with patch('crud.Department', return_value=mock_department):
        result = create_department('HR')
        mock_session.add.assert_called_once_with(mock_department)
        mock_session.commit.assert_called_once()
        assert result == mock_department

def test_create_request_type(mock_session):
    mock_request_type = MagicMock()
    with patch('crud.RequestType', return_value=mock_request_type):
        result = create_request_type('Travel', 500.00)
        mock_session.add.assert_called_once_with(mock_request_type)
        mock_session.commit.assert_called_once()
        assert result == mock_request_type

def test_create_reimbursement_request(mock_session):
    mock_request = MagicMock()
    with patch('crud.ReimbursementRequest', return_value=mock_request):
        mock_request.request_id = 1
        result = create_reimbursement_request(1, 1, 200.00, datetime.now(), 1)
        mock_session.add.assert_called_once_with(mock_request)
        mock_session.commit.assert_called_once()
        assert result == 1

def test_get_all_request_types(mock_session):
    mock_request_types = [MagicMock(), MagicMock()]
    mock_session.query().all.return_value = mock_request_types
    result = get_all_request_types()
    assert result == mock_request_types

def test_create_document(mock_session):
    mock_document = MagicMock()
    with patch('crud.Document', return_value=mock_document):
        result = create_document(1, 'path/to/document')
        mock_session.add.assert_called_once_with(mock_document)
        mock_session.commit.assert_called_once()
        assert result == mock_document

def test_create_notification(mock_session):
    mock_notification = MagicMock()
    with patch('crud.Notification', return_value=mock_notification):
        result = create_notification(1, 'Test message', datetime.now())
        mock_session.add.assert_called_once_with(mock_notification)
        mock_session.commit.assert_called_once()
        assert result == mock_notification

def test_get_user(mock_session):
    mock_user = MagicMock()
    mock_session.query().get.return_value = mock_user
    result = get_user(1)
    assert result == mock_user

def test_get_departments(mock_session):
    mock_department = MagicMock()
    mock_session.query().get.return_value = mock_department
    result = get_departments(1)
    assert result == mock_department

def test_get_request_type(mock_session):
    mock_request_type = MagicMock()
    mock_session.query().get.return_value = mock_request_type
    result = get_request_type(1)
    assert result == mock_request_type

def test_get_reimbursement_request(mock_session):
    mock_request = MagicMock()
    mock_session.query().get.return_value = mock_request
    result = get_reimbursement_request(1)
    assert result == mock_request

def test_get_all_reimbursement_requests(mock_session):
    mock_requests = [MagicMock(), MagicMock()]
    mock_session.query().all.return_value = mock_requests
    result = get_all_reimbursement_requests()
    assert result == mock_requests


def test_get_amount_limit(mock_session):
    mock_request_type = MagicMock()
    mock_request_type.amount_limit = 500.00
    mock_session.query().filter_by().first.return_value = mock_request_type
    result = get_amount_limit(1)
    assert result == 500.00

def test_get_notification(mock_session):
    mock_notification = MagicMock()
    mock_session.query().get.return_value = mock_notification
    result = get_notification(1)
    assert result == mock_notification

def test_update_user(mock_session):
    mock_user = MagicMock()
    mock_session.query().get.return_value = mock_user
    updates = {'first_name': 'Jane'}
    result = update_user(1, updates)
    assert result == mock_user
    assert mock_user.first_name == 'Jane'
    mock_session.commit.assert_called_once()

def test_update_department(mock_session):
    mock_department = MagicMock()
    mock_session.query().get.return_value = mock_department
    updates = {'department_name': 'Finance'}
    result = update_department(1, updates)
    assert result == mock_department
    assert mock_department.department_name == 'Finance'
    mock_session.commit.assert_called_once()

def test_update_request_type(mock_session):
    mock_request_type = MagicMock()
    mock_session.query().get.return_value = mock_request_type
    updates = {'type_name': 'Accommodation'}
    result = update_request_type(1, updates)
    assert result == mock_request_type
    assert mock_request_type.type_name == 'Accommodation'
    mock_session.commit.assert_called_once()

def test_delete_user(mock_session):
    mock_user = MagicMock()
    mock_session.query().get.return_value = mock_user
    delete_user(1)
    mock_session.delete.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()

def test_delete_request_type(mock_session):
    mock_request_type = MagicMock()
    mock_session.query().get.return_value = mock_request_type
    delete_request_type(1)
    mock_session.delete.assert_called_once_with(mock_request_type)
    mock_session.commit.assert_called_once()
