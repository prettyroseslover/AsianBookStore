from flask import Flask, render_template, url_for, request, redirect, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import re, os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from form import LoginForm, FurtherInfo, BookFilter, RatingBook, CheckDiscount, RegistryForm
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
import telebot

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a really really really really long secret key'

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(160), nullable=False)
    name = db.Column(db.String(255))
    surname = db.Column(db.String(255))
    famname = db.Column(db.String(255))
    phone_number = db.Column(db.String(10))
    address = db.Column(db.String(255))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


Zakaz_Books_table = db.Table(
    "zakaz_books",
    db.Model.metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("book", db.Integer, db.ForeignKey('books.id_book'), nullable=False),
    db.Column("zakaz", db.Integer, db.ForeignKey('zakaz.id_zakaz'), nullable=False),
)

class Books(db.Model):
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

    def __repr__(self):
        return '<{}>'.format(self.title)


class Promocode(db.Model):
    __tablename__ = 'promocode'
    id_promocode = db.Column(db.Integer, primary_key=True)
    promocode = db.Column(db.String(10), nullable=False)
    discount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Promocode: {}, {}>'.format(self.promocode, self.discount)


class Zakaz(db.Model):
    __tablename__ = 'zakaz'
    id_zakaz = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_zakaz = db.Column(db.DateTime, default=datetime.utcnow)
    id_promocode_used = db.Column(db.Integer, db.ForeignKey('promocode.id_promocode'))
    books = db.relationship("Books", secondary=Zakaz_Books_table, backref="zakazy")

    def __repr__(self):
        return '<Zakaz #{}>'.format(self.id_zakaz)


# class Card(db.Model):
#     __tablename__ = 'card'
#     id_card = db.Column(db.Integer, primary_key=True)
#     id_zakazi = db.Column(db.Integer, db.ForeignKey('zakaz.id_zakaz'), nullable=False)
#     id_books = db.Column(db.Integer, db.ForeignKey('books.id_book'), nullable=False)
#     quantity_wanted = db.Column(db.Integer, nullable=False)
#     time_card = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def __repr__(self):
#         return '<Card #{}>'.format(self.id)


class Rating(db.Model):
    __tablename__ = 'rating'
    id_rating = db.Column(db.Integer, primary_key=True)
    id_book_to_rate = db.Column(db.Integer, db.ForeignKey('books.id_book'), nullable=False)
    id_client_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.TEXT)
    time_rating = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Rating {}/5 id {}>'.format(self.rating, self.id_book_to_rate)


@app.route('/')
def hello_world():
    flag_btn = current_user.is_authenticated
    new_books = []
    new_books.append(Books.query.get(15))
    new_books.append(Books.query.get(2))
    new_books.append(Books.query.get(11))
    new_books.append(Books.query.get(1))
    return render_template("index.html", flag_btn=flag_btn, new_books=new_books)


@app.route('/about')
def about_us():
    flag_btn = current_user.is_authenticated
    return render_template("about_us.html", flag_btn=flag_btn)


@app.route('/shelves', methods=['POST', 'GET'])
def shelves():
    form = BookFilter()
    flag_btn = current_user.is_authenticated
    books_available = Books.query
    if form.validate_on_submit():

        lang = {"Русский": form.russian.data, "Английский": form.english.data, "Японский": form.japanese.data}
        fil1 = [k for k, v in lang.items() if v == True]
        if len(fil1) > 0:
            books_available = books_available.filter(Books.language.in_(fil1))

        genre = {"Научпоп": form.scipop.data, "Кулинария": form.cookbook.data, "Рассказы": form.stories.data,
                 "Повесть": form.narrative.data, "Роман": form.novel.data, "Эссе": form.essay.data}
        fil2 = [k for k, v in genre.items() if v == True]
        if len(fil2) > 0:
            books_available = books_available.filter(Books.genre.in_(fil2))

        country = {"Япония": form.japan.data, "Китай": form.china.data, "Корея": form.korea.data,
                   "Вьетнам": form.vietnam.data}
        fil3 = [k for k, v in country.items() if v == True]
        if len(fil3) > 0:
            books_available = books_available.filter(Books.country.in_(fil3))

        if form.sort.data == '2':
            books_available = books_available.order_by(Books.price)
        elif form.sort.data == '1':
            books_available = books_available.order_by(Books.price.desc())
        else:
            books_available = books_available.order_by(Books.id_book)

    books_available = books_available.all()
    return render_template("shelves.html", flag_btn=flag_btn, books=books_available, form=form)


@app.route('/shelves/<int:id>')
def book_detail(id):
    flag_btn = current_user.is_authenticated
    curr_book = Books.query.get(id)
    return render_template("book.html", flag_btn=flag_btn, book=curr_book)


@app.route('/shelves/<int:id>/add')
@login_required
def add(id):
    if str(id) in session:
        session[str(id)] = session.get(str(id)) + 1
    else:
        session[str(id)] = 1

    return redirect(url_for('book_detail', id=id))


@app.route('/recs')
def recs():
    flag_btn = current_user.is_authenticated
    rec = Rating.query.filter(Rating.comment.isnot("")).all()
    id_bs = []
    auth = []
    pic = []
    for r in rec:
        title = Books.query.get(r.id_book_to_rate).title
        id_bs.append(title)
        author = User.query.get(r.id_client_by).username
        auth.append(author)
        picture = Books.query.get(r.id_book_to_rate).image
        pic.append(picture)
    sz = len(rec)

    return render_template("recs.html", flag_btn=flag_btn, rec=rec, book=id_bs, auth=auth, sz=sz, pic=pic)


regex = '^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$'


def check(email):
    if re.search(regex, email):
        return True
    else:
        return False


@app.route('/signin', methods=['POST', 'GET'])
def sign():
    form = RegistryForm()
    error = None
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    if form.validate_on_submit():
        if db.session.query(User).filter(User.username == form.username.data).first():
            error = "Такой логин уже есть! Придумайте другой"
            return render_template("user.html", error=error, form=form)
        if not check(form.email.data):
            error = "Это не email!"
            return render_template("user.html", error=error, form=form)
        if db.session.query(User).filter(User.email == form.email.data).first():
            error = "Такой email уже есть! Может, вам стоит войти?"
            return render_template("user.html", error=error, form=form)
        user1 = User(username=form.username.data, email=form.email.data)
        user1.set_password(form.password.data)
        db.session.add(user1)
        db.session.commit()
        user = db.session.query(User).filter(User.username == form.username.data).first()
        login_user(user)
        return redirect(url_for('account'))
    return render_template("user.html", error=error, form=form)


@app.route('/login', methods=['POST', 'GET'])
def log():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('account'))

        flash("Invalid username/password", 'error')
        return redirect(url_for('log'))
    return render_template('login.html', form=form)


validate_phone_number_pattern = "^\\+?[1-9][0-9]{7,14}$"


def check_ph(phone):
    if re.match(validate_phone_number_pattern, phone):
        return True
    else:
        return False


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    form = FurtherInfo()
    user = User.query.get_or_404(current_user.id)
    flag = (user.surname is None) and (user.name is None) and (user.famname is None) and (
                user.phone_number is None) and (user.address is None)

    if form.validate_on_submit():
        user.surname = form.surname.data
        user.name = form.name.data
        user.famname = form.famname.data
        if check_ph(form.phone_number.data):
            user.phone_number = form.phone_number.data
        else:
            flash("Invalid number")
            return render_template('account.html', form=form, flag=flag)
        user.address = form.address.data
        db.session.commit()
        flag = False
    #flag_for_orders = (Zakaz.books is None)
    #flag_for_orders = (user.id > 5)
    my_orders = Zakaz.query.filter(Zakaz.id_client == current_user.id).all()

    return render_template('account.html', form=form, flag=flag, order=my_orders)


@app.route('/update_acc', methods=['POST', 'GET'])
@login_required
def update_acc():
    form = FurtherInfo()
    user = User.query.get_or_404(current_user.id)

    if form.validate_on_submit():
        user.surname = form.surname.data
        user.name = form.name.data
        user.famname = form.famname.data
        if check_ph(form.phone_number.data):
            user.phone_number = form.phone_number.data
        else:
            flash("Invalid number")
            return render_template('update_acc.html', form=form)
        user.address = form.address.data
        db.session.commit()
        return redirect(url_for('account'))

    return render_template('update_acc.html', form=form)


@app.route('/post_rating', methods=['POST', 'GET'])
@login_required
def post_rating():
    choice = []
    for i in Books.query.all():
        choice.append((i.id_book, i.title))
    form = RatingBook()
    form.book.choices = choice
    if form.validate_on_submit():
        if form.comment.data is None:
            rate_obj = Rating(id_book_to_rate=form.book.data, id_client_by=current_user.id, rating=form.rating.data)
        else:
            rate_obj = Rating(id_book_to_rate=form.book.data, id_client_by=current_user.id, rating=form.rating.data, comment=form.comment.data)

        db.session.add(rate_obj)
        db.session.commit()
        return redirect(url_for('account'))
    return render_template('post_rating.html', form=form)


@app.route('/busket', methods=['POST', 'GET'])
@login_required
def busket():
    all_q = len(db.session.query(Books).all()) + 1
    s = []
    d = {}
    total = 0
    flag = False
    id_promo = 0
    for i in range(1, all_q):
        if str(i) in session:
            s.append(i)
            d[i] = session[str(i)]
            id_b = Books.query.get(i)
            total += id_b.price * session[str(i)]

    if len(s) > 0:
        books_chosen = Books.query.filter(Books.id_book.in_(s))
        flag = True
    else:
        books_chosen = None

    user = User.query.get_or_404(current_user.id)
    flag_log = (user.surname is None) or (user.name is None) or (user.famname is None) or (
            user.phone_number is None) or (user.address is None)
    form = CheckDiscount()
    error = None
    if form.validate_on_submit():
        exist = Promocode.query.filter(Promocode.promocode == form.promocode.data).first()
        if exist:
            total = total * ((100 - exist.discount) / 100)
            id_promo = exist.id_promocode
        else:
            error = "Такого промокода не существует"
            id_promo = 0
    return render_template('busket.html', book=books_chosen, flag=flag, dict=d, total=total, flag_log=flag_log, error=error, form=form, id_promo=id_promo)


@app.route('/busket/buy/<int:id>')
@login_required
def buy(id):
    if id == 0:
        new_order = Zakaz(id_client=current_user.id)
    else:
        new_order = Zakaz(id_client=current_user.id, id_promocode_used=id)

    all_q = len(db.session.query(Books).all()) + 1
    for i in range(1, all_q):
        if str(i) in session:
            b = Books.query.get(i)
            b.quantity = b.quantity - session[str(i)]
            if b.quantity < 0:
                return "На складе нет такого кол-ва книг"

            for n in range(0, session[str(i)]):
                new_order.books.append(b)

        session.pop(str(i), None)
    db.session.add(new_order)
    db.session.commit()
    return render_template('buy.html')

@app.route('/busket/<int:id>/delete_item')
@login_required
def delete_item(id):
    if session[str(id)] == 1:
        session.pop(str(id), None)
    else:
        session[str(id)] = session[str(id)] - 1
    return redirect(url_for('busket'))


@app.route('/logout')
@login_required
def logout():
    all_q = len(db.session.query(Books).all()) + 1
    for i in range(1, all_q):
        if str(i) in session:
            session.pop(str(i), None)
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('log'))

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        if current_user.id == 5:
            return True
        else: 
            print(current_user.id)
            flash("You are not the admin")
            return False
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('log'))

admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(ModelView(Books, db.session))
admin.add_view(ModelView(Promocode, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Rating, db.session))

# @app.route('/admin')
# @login_required
# def admin():
#     id = current_user.id
#     if id == 5:
#        #return render_template('admin.html')

#         return redirect(url_for('admin'))
#     else:
#         flash("You are not admin")
#         return redirect(url_for('log'))


@app.route('/telegram',methods= ['POST'])
def telegram():
    Name = request.form['Name']
    Telegram = request.form['Telegram']
    msg_text = request.form['msg_text']
    output = 'Имя: ' + Name + '\nТелеграм: ' + Telegram + '\n\nОтзыв:\n' + msg_text
    print(output)
    if Name and Telegram and msg_text:
        token = '5626665491:AAHZVovachxJXmOXAXPLfV47YI3hbyHLnfg'
        bot = telebot.TeleBot(token)
        chat_id = '1283589339' #moj
        #bot.send_message(chat_id, output)
        return jsonify({'output':'Спасибо за отзыв!'})

    return jsonify({'error' : 'Missing data!'})



if __name__ == '__main__':
    app.run(debug=True)
