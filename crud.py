from database import get_session
from datetime import datetime
from models import *
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

def create_user(first_name: str, last_name: str, email: str, password: str, role: str, user_status: str, manager_id: int, department_id: int):
    session = get_session()
    try:  
        hashed_password = generate_password_hash(password, method='sha256')        
        user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password,
                    role=role, user_status=user_status, manager_id=manager_id, department_id=department_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except SQLAlchemyError as e:
        print(f"Error creating user: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def create_department(department_name: str):
    try:
        session = get_session()
        department = Department(department_name=department_name)
        session.add(department)
        session.commit()
        session.refresh(department)
        return department
    except SQLAlchemyError as e:
        print(f"Error creating department: {e}")
        session.rollback()
        return None

def create_request_type(type_name: str, amount_limit: float):
    try:
        session = get_session()
        request_type = RequestType(type_name=type_name, amount_limit=amount_limit)
        session.add(request_type)
        session.commit()
        session.refresh(request_type)
        return request_type
    except SQLAlchemyError as e:
        print(f"Error creating request type: {e}")
        session.rollback()
        return None

def create_reimbursement_request(employee_id, request_type_id, amount, request_date, manager_id):
    session_db = get_session()
    try:
        new_request = ReimbursementRequest(
            employee_id=employee_id,
            request_type_id=request_type_id,
            amount=amount,
            request_date=request_date,
            status='pending',
            manager_id=manager_id
        )
        session_db.add(new_request)
        session_db.commit()
        request_id = new_request.request_id
        return request_id
    except SQLAlchemyError as e:
        session_db.rollback()
        raise e
    finally:
        session_db.close()

def get_all_request_types():
    session = get_session()
    request_types = session.query(RequestType).all()
    session.close()
    return request_types

def create_document(request_id: int, document_path: str):
    try:
        session = get_session()
        document = Document(request_id=request_id, document_path=document_path)
        session.add(document)
        session.commit()
        session.refresh(document)
        return document
    except SQLAlchemyError as e:
        print(f"Error creating document: {e}")
        session.rollback()
        return None

def create_notification(user_id: int, message: str, is_read: bool, created_at: datetime):
    try:
        session = get_session()
        notification = Notification(user_id=user_id, message=message, is_read=is_read, created_at=created_at)
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification
    except SQLAlchemyError as e:
        print(f"Error creating notification: {e}")
        session.rollback()
        return None

# read function
def get_user(user_id: int):
    session = get_session()
    return session.query(User).get(user_id)

def get_departments(department_id: int):
    session = get_session()
    return session.query(Department).get(department_id)

def get_request_type(request_type_id: int):
    session = get_session()
    return session.query(RequestType).get(request_type_id)

def get_reimbursement_request(request_id: int):
    session = get_session()
    return session.query(ReimbursementRequest).get(request_id)

def get_all_reimbursement_requests():
    session = get_session()
    reimbursement_requests = session.query(ReimbursementRequest).all()
    session.close()
    return reimbursement_requests

def get_document(request_id: int):
    session = get_session()
    Document = session.query(Document).get(request_id)
    return Document.document_path

def get_amount_limit(request_type_id :int):
    session = get_session()
    request_type =session.query(RequestType).filter_by(request_type_id=request_type_id).first()
    return request_type.amount_limit if request_type else None


def get_notification(notification_id: int):
    session = get_session()
    return session.query(Notification).get(notification_id)

# update funcion
def update_user(user_id: int, updates: dict):
    try:
        session = get_session()
        user = session.query(User).get(user_id)
        if user:
            for key, value in updates.items():
                setattr(user, key, value)
            session.commit()
            session.refresh(user)
            return user
        else:
            return None
    except SQLAlchemyError as e:
        print(f"Error updating user: {e}")
        session.rollback()
        return None

def update_department(department_id: int, updates: dict):
    try:
        session = get_session()
        department = session.query(Department).get(department_id)
        if department:
            for key, value in updates.items():
                setattr(department, key, value)
            session.commit()
            session.refresh(department)
            return department
        else:
            return None
    except SQLAlchemyError as e:
        print(f"Error updating department: {e}")
        session.rollback()
        return None

def update_request_type(request_type_id: int, updates: dict):
    try:
        session = get_session()
        request_type = session.query(RequestType).get(request_type_id)
        if request_type:
            for key, value in updates.items():
                setattr(request_type, key, value)
            session.commit()
            session.refresh(request_type)
            return request_type
        else:
            return None
    except SQLAlchemyError as e:
        print(f"Error updating request type: {e}")
        session.rollback()
        return None

# Delete functions

def delete_user(user_id: int):
    try:
        session = get_session()
        user = session.query(User).get(user_id)
        if user:
            session.delete(user)
            session.commit()
        else:
            print("User not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting user: {e}")
        session.rollback()

def delete_request_type(request_type_id: int):
    try:
        session = get_session()
        request_type = session.query(RequestType).get(request_type_id)
        if request_type:
            session.delete(request_type)
            session.commit()
        else:
            print("Request type not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting request type: {e}")
        session.rollback()        
