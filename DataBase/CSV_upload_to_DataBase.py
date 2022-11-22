import csv
from lib2to3.pytree import type_repr
import sqlalchemy as db
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

# input_files = "./Uploded_files/file1.csv"

engine = db.create_engine('sqlite:///app/database.db', echo=True)

Base = declarative_base()
class Books(Base):
    __tablename__ = 'books'
    id_book = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String(64), nullable=False)
    genre = db.Column(db.String(64), nullable=False)
    country = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer)
    image = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind = engine)
session = Session()

# res = session.query(Books).all()
# for r in res:
#    print(r.title)
# print(res)

with open('DataBase/книгидб.csv', 'r', encoding='utf8') as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        if row[0]=='' or row[1]=='' or row[3]=='' or row[4]=='' or row[5]=='' or row[7]=='':
            print('Ошибка:', row)
        if row[6] == '':
            row[6] = 0
        # if not isinstance(row[2], int):
        #     print("Ошибка в цене:",row[0])
        #     exit()
        # if not isinstance(row[2], int):
        #     print("Ошибка в количестве:",row[0])
        #     exit()
        
        print(row)
        session.add(Books(title=row[0], author=row[1], price=int(row[2]), language=row[3], genre=row[4], country=row[5], year=int(row[6]), image='./Images/'+row[7], quantity=int(row[8])))
session.commit()
