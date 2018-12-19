'''
Routes for the website
'''

from flask import Flask, make_response, jsonify, g, render_template, flash, redirect, url_for, request, send_from_directory, session, abort

from flask_bcrypt import check_password_hash, generate_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_uploads import configure_uploads
from flask_mail import Mail, Message
from flask_sslify import SSLify
from flask_compress import Compress

from itsdangerous import URLSafeTimedSerializer

from threading import Thread

from werkzeug.datastructures import CombinedMultiDict, FileStorage
from werkzeug.utils import secure_filename
import os
import datetime

import forms
import models

from peewee import SelectQuery

app = Flask(__name__)

app.secret_key = 'secret-key' # Your sceret key

# app.config['UPLOADED_<Name of Upload Set In Uppercase>_DEST']
app.config['UPLOADED_IMAGES_DEST'] = 'images/uploads/products'

configure_uploads(app, (forms.images,))

login_manager = LoginManager() # create a login manager
login_manager.init_app(app) # initialize login manager with flask app
login_manager.login_view = 'login' # view used for login
login_manager.login_message = "Lütfen Giriş Yapınız !"

app.config['MAIL_SERVER']='smtp.gmail.com' # Your mail server
app.config['MAIL_PORT'] = 465 # Your mail server port
app.config['MAIL_USERNAME'] = 'duzceflask@gmail.com' # your mail server username
app.config['MAIL_PASSWORD'] = '205164647786' # your mail server sifre
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
sslify = SSLify(app)
Compress(app)

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if (endpoint == 'static' or endpoint == 'product_images'):
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

@login_manager.user_loader
def load_user(userid):
    try:
        return models.Kullanici.get(models.Kullanici.id == userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    """Connet to the database before each request."""
    try:
        g.db = models.DATABASE
        g.db.connect()
    except models.OperationalError:
        pass


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response

#
# Routes For Authentication
#

@app.route('/kaydol/', methods=('GET', 'POST'))
def kaydol():
    form = forms.KayitForm()
    if form.validate_on_submit():
        flash("Tebrikler! Başarıyla kaydoldunuz", category='Success')
        try:
            models.Kullanici.kullanici_ekle(
                isim = form.isim.data,
                email = form.email.data,
                sifre = form.sifre.data,
                telefon = form.telefon.data
            )
            user = models.Kullanici.get(models.Kullanici.email == form.email.data)
            login_user(user)
        except ValueError:
            pass
        # Send Email
        send_email("SüNa Mağazacılık", 'muhammedkrkyn@gmail.com', [form.email.data], '', render_template('email/kayit.html', user=form.isim.data))
        next = request.args.get('next')
        return redirect(next or url_for('index'))
    return render_template('kaydol.html', form=form, user=current_user)


@app.route('/giris/', methods=('GET', 'POST'))
def login():
    form = forms.GirisForm()
    next = request.args.get('next')
    if form.validate_on_submit():
        try:
            user = models.Kullanici.get(models.Kullanici.email == form.email.data)
        except models.DoesNotExist:
            flash("Email yada Şifre yanlış kontrol ediniz.", "Error")
        else:
            if check_password_hash(user.sifre.encode('utf-8'), form.sifre.data):
                login_user(user)
                if current_user.admin_mi:
                    return redirect(next or url_for('yonetici'))
                else:
                    flash("Başarıyla giriş yapıldı!", "Success")
                    return redirect(next or url_for('index'))
            else:
                flash("Email yada Şifre yanlış kontrol ediniz.", "Error")
    return render_template('giris.html', form=form, user=current_user)


@app.route('/cikis')
@login_required
def cikis():
    logout_user()
    flash("Başarıyla çıkış yapıldı tekrar görüşmek üzere iyi günler :)", "Success")
    return redirect(url_for('index'))


@app.route('/profil/')
@login_required
def profil():
    products = models.Urun.select(models.Satisgecmisi, models.Urun).join(models.Satisgecmisi).annotate(models.Satisgecmisi, models.Satisgecmisi.urun_adedi).where(models.Satisgecmisi.musteri == current_user.id)
    return render_template('profil.html', user=current_user, products=products)


# cancel order
@app.route('/siparis/iptal/<id>')
@login_required
def siparis_iptal(id):
    q = models.Satisgecmisi.update(durum="İptal Edildi").where(models.Satisgecmisi.siparis_id == id)
    q.execute()
    flash('Sipariş İptal Edildi!')
    return redirect(url_for('profil'))



#
# Routes for front pages
#

@app.route('/')
def index():
    return render_template("index.html", user=current_user, products=models.Urun)



@app.route('/iade')
def iade():
    return render_template("iade.html", user=current_user)



@app.route('/urun/kategori/erkek')
def urun_erkekler():
    products = models.Urun.select().where(models.Urun.kategori.contains('Erkek'))
    return render_template("index_erkek.html", user=current_user, products=products)

@app.route('/urun/kategori/kadin')
def urun_kadinlar():
    products = models.Urun.select().where(models.Urun.kategori.contains('Kadın'))
    return render_template("index_kadin.html", user=current_user, products=products)

@app.errorhandler(404)
def sayfa_bulunamadi(e):
    return render_template('404.html', user=current_user), 404

#
# Dashboard Routes
#

@app.route('/yonetici/')
@login_required
def yonetici():
    if current_user.admin_mi:
        return render_template("yonetici/html/dashboard.html", user=current_user)
    else:
        return redirect(url_for('index'))


@app.route('/yonetici/kullanicilar/')
@login_required
def yonetici_kullanicilar():
    if current_user.admin_mi:
        return render_template("yonetici/html/kullanicilar.html", user=current_user, data=models.Kullanici)
    else:
        return redirect(url_for('index'))


@app.route('/yonetici/urunler/')
@login_required
def yonetici_urunler():
    if current_user.admin_mi:
        return render_template("yonetici/html/urunler.html", user=current_user, products=models.Urun, app=app)
    else:
        return redirect(url_for('index'))


@app.route('/yonetici/urunler/yeni/', methods=('GET', 'POST'))
@login_required
def yonetici_urunler_yeni():
    if current_user.admin_mi:
        form = forms.YeniUrunForm(CombinedMultiDict((request.files, request.form)))
        filename1 = ''
        
        if form.validate_on_submit():
            if form.image_1.data:
                f = form.image_1.data
                filename1 = secure_filename(f.filename)
                f.save(os.path.join(
                    app.instance_path, app.config['UPLOADED_IMAGES_DEST'], filename1
                ))
            
            models.Urun.urun_ekle(
                ad=form.ad.data,
                image_1=filename1,
               
                adet=form.adet.data,
                
                satis_fiyati=form.satis_fiyati.data,
               
                kategori = form.kategori.data,
                
                diger_detaylar = form.diger_detaylar.data
            )
            return redirect(url_for('yonetici_urunler'))
        return render_template("yonetici/html/urun/yeni.html", user=current_user, form=form)
    else:
        return redirect(url_for('index'))

@app.route('/yonetici/urunler/duzenle/<id>', methods=('GET', 'POST'))
@login_required
def yonetici_urunler_duzenle(id):
    if current_user.admin_mi:
        product = models.Urun.get(models.Urun.id == id)
        form = forms.UrunDuzenleForm(CombinedMultiDict((request.files, request.form)), obj=product)
        # q = models.Kullanici.update(sifre=form.sifre.data).where(models.Kullanici.email == current_user.email)
        filename1 = ''
        

        if form.validate_on_submit():
            if form.image_1.data:
                f = form.image_1.data
                if type(f) == FileStorage:
                    filename1 = secure_filename(f.filename)
                    f.save(os.path.join(
                        app.instance_path, app.config['UPLOADED_IMAGES_DEST'], filename1
                    ))
                else:
                    filename1 = f
            
            q = models.Urun.update(
                ad=form.ad.data,
                adet=form.adet.data,
                image_1 = filename1,
                
                satis_fiyati=form.satis_fiyati.data,
                
                kategori = form.kategori.data,
                
                diger_detaylar = form.diger_detaylar.data
            ).where(models.Urun.id == id)
            q.execute()
        return render_template('yonetici/html/urun/duzenle.html', user=current_user, form=form, item=product)
    else:
        return redirect(url_for('index'))


@app.route('/yonetici/urunler/sil/<id>', methods=('GET', 'POST'))
@login_required
def yonetici_urunler_sil(id):
    if current_user.admin_mi:
        product_ins = models.Urun.get(models.Urun.id == id)
        product_ins.delete_instance()
        return redirect(url_for('yonetici_urunler'))
    else:
        return redirect(url_for('index'))


@app.route('/yonetici/siparisler/')
@login_required
def yonetici_siparisler():
    if current_user.admin_mi:
        return render_template("yonetici/html/siparisler.html", user=current_user, products=models.Satisgecmisi, app=app)
    else:
        return redirect(url_for('index'))

@app.route('/yonetici/siparisler/duzenle/<int:order_id>')
@login_required
def yonetici_siparis_duzenle(order_id):
    if current_user.admin_mi:
        product = models.Satisgecmisi.get(models.Satisgecmisi.id == order_id)
        return render_template("yonetici/html/siparis_duzenle.html", user=current_user, product=product, app=app)
    else:
        return redirect(url_for('index'))


@app.route('/yonetici/teslimat/<int:order_id>/<int:deliv>')
@login_required
def yonetici_teslimat(order_id, deliv):
    if current_user.admin_mi:
        if deliv == 1:
            q = models.Satisgecmisi.update(teslim = True, durum="Teslim Edildi", teslim_zamani=datetime.datetime.now()).where(models.Satisgecmisi.id == order_id)
            q.execute()
        else:
            q = models.Satisgecmisi.update(teslim = False, durum="Hazırlanıyor").where(models.Satisgecmisi.id == order_id)
            q.execute()
        return redirect(url_for('yonetici_siparisler'))
    else:
        return redirect(url_for('index'))



#
# Product Route
#
@app.route('/urun/<path:ad>/', methods=('GET', 'POST'))
def urun_sayfasi(ad):
    try:
        product_ins = models.Urun.get(models.Urun.baslik == ad)
    except models.Urun.DoesNotExist:
        return abort(404)
    
    return render_template("urun/index.html", user=current_user, product=product_ins)




#
# Cart and checkout route
#

@app.route('/satin_al/<int:product_id>')
@login_required
def satin_al(product_id):
    try:
        if models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id)):
            print('1')
            prod = models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q = models.Sepet.update(adet = prod.adet + 1).where((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q.execute()
    except models.Sepet.DoesNotExist:
        print('2')
        models.Sepet.urun_ekle(
            kullanici_email_id= current_user.id,
            urun_id_id= product_id,
            adet = 1
        )
    return redirect(url_for('odeme'))

@app.route("/sepetten_sil/<int:product_id>/", methods=('GET', 'POST'))
@login_required
def sepetten_sil(product_id):
    try:
        prod = models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
        prod.delete_instance()
    except models.Sepet.DoesNotExist:
        pass
    return redirect(url_for('sepet_sayfasi'))
	
@app.route("/sepet_bosalt", methods=('GET', 'POST'))
@login_required
def sepet_bosalt():
    try:
        prod = models.Sepet.get((models.Sepet.kullanici_email == current_user.id) )
        prod.delete().execute()
		
    except models.Sepet.DoesNotExist:
        pass
	
    return redirect(url_for('sepet_sayfasi'))


@app.route("/sepete_ekle/<int:product_id>/", methods=('GET', 'POST'))
@login_required
def sepete_ekle(product_id):
    try:
        if models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id)):
            print('1')
            prod = models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q = models.Sepet.update(adet = prod.adet + 1).where((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q.execute()
    except models.Sepet.DoesNotExist:
        print('2')
        models.Sepet.urun_ekle(
            kullanici_email_id= current_user.id,
            urun_id_id= product_id,
            adet = 1
        )

    flash("Başarıyla sepete eklendi!")
    return redirect(url_for('sepet_sayfasi'))

@app.route("/adet_artir/<int:product_id>/", methods=('GET', 'POST'))
@login_required
def adet_artir(product_id):
    try:
        if models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id)):
            print('1')
            prod = models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q = models.Sepet.update(adet = prod.adet + 1).where((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q.execute()
    except models.Sepet.DoesNotExist:
        print('2')
        models.Sepet.urun_ekle(
            kullanici_email_id= current_user.id,
            urun_id_id= product_id,
            adet = 1
        )

    flash("Adet Arttırıldı!")
    return redirect(url_for('sepet_sayfasi'))
	
@app.route("/adet_azalt/<int:product_id>/", methods=('GET', 'POST'))
@login_required
def adet_azalt(product_id):
    try:
        if models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id)):
            print('1')
            prod = models.Sepet.get((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q = models.Sepet.update(adet = prod.adet - 1).where((models.Sepet.kullanici_email == current_user.id) & (models.Sepet.urun_id == product_id))
            q.execute()
    except models.Sepet.DoesNotExist:
        print('2')
        models.Sepet.urun_ekle(
            kullanici_email_id= current_user.id,
            urun_id_id= product_id,
            adet = 1
        )

    flash("Adet Azalt!")
    return redirect(url_for('sepet_sayfasi'))
	
@app.route("/sepet/", methods=('GET', 'POST'))
@login_required
def sepet_sayfasi():
    products = models.Urun.select(models.Sepet, models.Urun).join(models.Sepet).annotate(models.Sepet, models.Sepet.adet).where(models.Sepet.kullanici_email == current_user.id)
    return render_template('sepet.html', user=current_user, products=products)

@app.route("/odeme/", methods=('GET', 'POST'))
@login_required
def odeme():
    products = {}
    totalprice = 0
    try:
        products = models.Urun.select(models.Sepet, models.Urun).join(models.Sepet).annotate(models.Sepet, models.Sepet.adet).where(models.Sepet.kullanici_email == current_user.id)
        for prod in products:
            totalprice += prod.satis_fiyati * prod.sepet.adet
    except models.Sepet.DoesNotExist:
        pass

    if request.method == 'POST':
        musteri_adi = request.form['fullname']
        musteri_adresi = request.form['hostelname']
        telefon = request.form['mobileno']
        odeme_yontemi = request.form['pay']

        for product in products:
            models.Satisgecmisi.satis_gecmisi_ekle(
                musteri = current_user.id,
                urun_id = product.id,
                urun_adi = product.ad,
                urun_adedi = product.sepet.adet,
                musteri_adi = musteri_adi,
                musteri_adresi = musteri_adresi,
                telefon = telefon,
                odeme_yontemi=odeme_yontemi,
            )

        try:
            ins = models.Sepet.delete().where(models.Sepet.kullanici_email_id == current_user.id)
            ins.execute()
        except models.Sepet.DoesNotExist:
            pass

        flash("Siparişiniz alındı kısa sürede hazırlanıp gönderilecektir.!", "Success")
        return redirect(url_for('index'))

    return render_template("odeme.html", user=current_user, products=products, totalprice=totalprice)




@app.route('/product_images')
def uploaded_file():
    filename = request.args.get('image')
    return send_from_directory(os.path.join(app.instance_path, app.config['UPLOADED_IMAGES_DEST']), filename)



def upload_file(file):
    try:
        file.save(file.filename)
    except:
        flash("Error Occured!!!!")

@app.route('/sitemap.xml')
def sitemap_file():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/db.db')
@login_required
def get_db():
    if current_user.admin_mi:
        return send_from_directory(app.root_path, 'shop.db')
    else:
        return redirect(url_for('index'))


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(app, msg)

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)



