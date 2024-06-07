from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Float, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship

class Department(Base):
    __tablename__ = 'departments'
    
    department_id = Column(Integer, primary_key=True)
    department_name = Column(String(100), unique=True, nullable=False)

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    user_status = Column(String(20), nullable=False)
    manager_id = Column(Integer, ForeignKey('users.user_id'))
    department_id = Column(Integer, ForeignKey('departments.department_id'))
    
    manager = relationship('User', remote_side=[user_id])
    department = relationship('Department')

class RequestType(Base):
    __tablename__ = 'request_types'
    
    request_type_id = Column(Integer, primary_key=True)
    type_name = Column(String(50), unique=True, nullable=False)
    amount_limit = Column(Float, nullable=False)

class ReimbursementRequest(Base):
    __tablename__ = 'reimbursement_requests'
    
    request_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    request_type_id = Column(Integer, ForeignKey('request_types.request_type_id'), nullable=False)
    amount = Column(Float, nullable=False)
    request_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    comments = Column(Text)
    manager_id = Column(Integer, ForeignKey('users.user_id'))
    
    employee = relationship('User', foreign_keys=[employee_id])
    manager = relationship('User', foreign_keys=[manager_id])

class Document(Base):
    __tablename__ = 'documents'
    
    document_id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('reimbursement_requests.request_id'), nullable=False)
    document_path = Column(String(255), nullable=False)
    
    reimbursement_request = relationship('ReimbursementRequest')

    
class Notification(Base):
    __tablename__ = 'notifications'
    
    notification_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    
    user = relationship('User')

