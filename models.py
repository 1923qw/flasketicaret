'''
    Shopping Project Database
    -----------------------------------------------------------------
    Database Model For Shopping Site
    author : Nitesh Kumar Niranjan <niteshkumarniranjan@gmail.com>
'''

import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *
from playhouse.migrate import SqliteMigrator
import uuid

# Default database
DATABASE = SqliteDatabase('magaza.db')
migrator = SqliteMigrator(DATABASE)


# User Table
class Kullanici(UserMixin, Model):
    """App Users Table"""
    isim = CharField()
    email = CharField(unique=True)
    sifre = CharField(max_length=100)
    telefon = CharField()
    katilma_zamani = DateTimeField(default=datetime.datetime.now)
    admin_mi = BooleanField(default=False)


    class Meta:
        database = DATABASE
  
    @classmethod
    def kullanici_ekle(cls, isim, email, sifre, telefon, admin=False):
        try:
            cls.create(
                isim = isim,
                email = email,
                sifre = generate_password_hash(sifre),
                telefon = telefon,
                admin_mi = admin
            )
        except IntegrityError:
            raise ValueError("Kullanıcı Zaten Var")


class Urun(Model):
    """Ürün Tablosu"""
    ad = CharField()
    baslik = CharField()
    image_1 = CharField()
    adet = IntegerField()
    satis_fiyati = IntegerField(null=False)
    kategori = CharField()
    
    diger_detaylar = TextField()
    yayin_zaman = DateTimeField(default=datetime.datetime.now)


    class Meta:
        database = DATABASE
        order_by = ('-yayin_zaman',)

    @classmethod
    def urun_ekle(cls, ad, image_1, adet, satis_fiyati, kategori, diger_detaylar):
        try:
            _baslik = ad.replace(" ", "_").lower()
            cls.create(
                ad = ad, 
                baslik = _baslik,
                image_1 = image_1, 
                adet = adet,
                satis_fiyati = satis_fiyati, 
                kategori = kategori, 
                diger_detaylar = diger_detaylar,
            )
        except IntegrityError:
            raise ValueError("Bir Hata Oluştu.")




class Sepet(Model):
    kullanici_email = ForeignKeyField(Kullanici, related_name='carts')
    urun_id = ForeignKeyField(Urun, related_name='products')
    adet = IntegerField()
    
    class Meta:
        database = DATABASE

    @classmethod
    def urun_ekle(cls, kullanici_email_id, urun_id_id, adet=1):
        try:
            cls.create(
                kullanici_email_id=kullanici_email_id,
                urun_id_id=urun_id_id,
                adet=adet
            )
        except IntegrityError:
            raise ValueError("Bir Hata Oluştu.")



class Satisgecmisi(Model):
    """Item Buying History"""
    siparis_id = CharField(max_length=50, unique=True)
    urun_id = ForeignKeyField(Urun, related_name='product')
    musteri = ForeignKeyField(Kullanici, related_name='customer')
    urun_adi = CharField()
    musteri_adi = CharField()
    telefon = IntegerField()
    odeme_yontemi = CharField()
    urun_adedi = IntegerField()
    musteri_adresi = TextField()
    satis_zamani = DateTimeField(default=datetime.datetime.now)
    durum = CharField()
    teslim = BooleanField()
    teslim_zamani = DateTimeField(null = True, default = datetime.datetime.now)


    class Meta:
        database = DATABASE
        order_by = ('teslim_zamani',)
    
    @classmethod
    def satis_gecmisi_ekle(cls, musteri, urun_id, urun_adi, urun_adedi, musteri_adi, musteri_adresi, telefon, odeme_yontemi, durum="Hazırlanıyor", teslim=False):
        cls.create(
            siparis_id = str(uuid.uuid4()),
            musteri = musteri,
            urun_id = urun_id,
            urun_adi = urun_adi,
            urun_adedi = urun_adedi,
            musteri_adi = musteri_adi,
            musteri_adresi = musteri_adresi,
            telefon = telefon,
            odeme_yontemi = odeme_yontemi,
            durum = durum,
            teslim=teslim
        )







def initialize():
    DATABASE.connect()
    DATABASE.create_tables([Kullanici, Urun, Sepet, Satisgecmisi], safe=True)
    DATABASE.close()
