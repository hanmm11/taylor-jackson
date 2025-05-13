
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

engine = create_engine("sqlite:///chat.db", echo=False)
Base = declarative_base()

class MessageRecord(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer)
    chat_id = Column(String)
    chat_title = Column(String, nullable=True)
    user_id = Column(String)
    sender = Column(String)
    text = Column(Text)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    chat_type = Column(String)
    source = Column(String)
    reply_to_user_id = Column(String, nullable=True)
    related_user_id = Column(String, nullable=True)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
