'''
All forms for the website
'''

from flask_uploads import IMAGES, UploadSet
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import IntegerField, PasswordField, StringField, TextAreaField
from wtforms.validators import (DataRequired, Email, Length, ValidationError,
                                equal_to, regexp)

import models

images = UploadSet('images', IMAGES)


def email_kontrol(form, field):
    if models.Kullanici.select().where(models.Kullanici.email == field.data).exists():
        raise ValidationError('Kullanıcı Email Adresi Zaten Kayıtlı')

class KayitForm(FlaskForm):
    isim = StringField('İsim ve Soyisim', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(),Email(),email_kontrol])
    sifre = PasswordField('Şifre', validators=[DataRequired(),Length(min=6), equal_to('sifre2', message='Şifreler Eşleşmiyor')])
    sifre2 = PasswordField('Şifre Tekrar', validators=[DataRequired()])
    telefon = IntegerField('Telefon', validators=[DataRequired()])

class GirisForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    sifre = PasswordField('Şifre', validators=[DataRequired()])



class YeniUrunForm(FlaskForm):
    ad = StringField('Ürün Adı', validators=[DataRequired()])
    image_1 = FileField('Ürün Resmi', validators=[FileRequired(), FileAllowed(images, 'Images only!')])
    
    adet = IntegerField('Ürün Stok Adedi', validators=[DataRequired()])
    
    satis_fiyati = IntegerField('Satış Fiyatı')
    
    kategori = StringField('Kategori')
    
    diger_detaylar = TextAreaField('Diğer Detaylar')

class UrunDuzenleForm(FlaskForm):
    ad = StringField('Ürün Adı', validators=[DataRequired()])
    image_1 = FileField('Ürün Resmi', validators=[ FileAllowed(images, 'Images only!')])
   
    adet = IntegerField('Ürün Stok Adedi', validators=[DataRequired()])
    
    satis_fiyati = IntegerField('Satış Fiyatı')
    
    kategori = StringField('Kategori')
    
    diger_detaylar = TextAreaField('Diğer  Detaylar')


class OdemeForm(FlaskForm):
    isim = StringField('İsim ve Soyisim', validators=[DataRequired()])
    adres = StringField('Adres', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefon = IntegerField("Telefon", validators=[DataRequired()])


class EmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])




