# -*- coding: utf-8 -*-

from django import template
import datetime


register = template.Library()

@register.filter
def get_at_index(list, index):
    return list[index]

@register.filter
def convert_datetime(data):
    return data.strftime("%d/%m/%Y %H:%M:%S")

@register.filter
def convert_date(data):
    return datetime.datetime.strptime(str(data), '%Y-%m-%d').strftime('%d/%m/%Y')

@register.filter
def cut_string(texto, tamanho_max):
    tamanho = len(texto)
    if(tamanho > tamanho_max):
        texto = texto[tamanho - tamanho_max:]
    return texto

@register.filter
def vtiquet(indice, ltiquets):
    for ticket in ltiquets:
        if str(ticket.rotulo) == str(indice):
            return True
    return False

@register.filter
def split1000(s, sep='.'):
    s = str(s)
    return s if len(s) <= 3 else split1000(s[:-3], sep) + sep + s[-3:]

@register.filter
def extensao_arquivo(arquivo):
    if arquivo[-3::] == 'pdf':
        return 'pdf'
    elif arquivo[-3::] == 'jpg':
        return 'jpg'
    elif arquivo[-3::] == 'tif':
        return 'tif'
    elif arquivo[-3::] == 'wps':
        return 'wps'
    else:
        return 'nada'

@register.filter
def codec(texto):
    return texto.decode("latin-1")

@register.filter()
def to_int(value):
    return int(value)

@register.filter()
def real(valor):
    if valor != None:
        import locale
        locale.setlocale( locale.LC_ALL, 'pt_BR.utf8' )
        return locale.currency( valor, grouping=True )
    return ''
