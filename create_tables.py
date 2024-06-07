from models import Base
from database import engine

# Create tables
Base.metadata.create_all(engine)




