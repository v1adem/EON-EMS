from sqlalchemy import Column, Integer, String, Boolean

from config import Base


class Admin(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    always_admin = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Admin(username='{self.username}')>"
