from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

user_project = Table(
    "user_project",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.project_id"), primary_key=True)
)

class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True, index=True, nullable=False)
  name = Column(String, nullable=False)
  hashed_password = Column(String, nullable=False)
  is_active = Column(Boolean, default=True, nullable=False)
  created_at = Column(DateTime(timezone=True), server_default=func.now())

  pic = Column(String, nullable=True)
  company = Column(String, nullable=True)
  dark_mode = Column(Boolean, default=False, nullable=False)
  role = Column(String, nullable=True)

  # address fields
  address = Column(String, nullable=True)
  city = Column(String, nullable=True)
  state = Column(String, nullable=True)
  country = Column(String, nullable=True)
  zipcode = Column(String, nullable=True)
  
  projects = relationship("Project", secondary="user_project", back_populates="users")

class Project(Base):
  __tablename__ = "projects"

  project_id = Column(Integer, primary_key=True)
  name = Column(String, nullable=False)
  description = Column(String, nullable=True)
  users = relationship("User", secondary="user_project", back_populates="projects")


