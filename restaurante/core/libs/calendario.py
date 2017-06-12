# -*- coding: utf-8 -*-
'''
Created on 30 de mar de 2017

@author: 2306214
'''
import calendar
import datetime

class calendario():
    
    def getCalendario(self):
        today = datetime.date.today()
        calendarobj = calendar
        calendarobj.setfirstweekday(calendar.SUNDAY)
        numerodiasmes = calendarobj.monthrange(today.year, today.month)[1]
        primeirodiasemana = calendarobj.weekday(today.year, today.month, 1)
        weekdayslabel = ('Segunda-Feira', 'Terça-Feira', 'Quarta-Feira', 'Quinta-Feira', 'Sexta-Feira', 'Sábado', 'Domingo')
        meses = ('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro')
        #smallweekdayslabel = ('D', 'S', 'T', 'Q', 'Q', 'S', 'S')
        smallweekdayslabel = ('Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb')
       
        #calendar.prmonth(2014, 1)
        diasmes = list(range(1, (numerodiasmes + 1)))
        diascompletos = []
        weekdays = []
        
        # Preencher lista com os dias da semana correspondente a cada dia do mes na mesma sequencia
        i = 0
        s = primeirodiasemana
        while i < len(diasmes):
            if (s) == 7:
                s = 0
            weekdays.append(+s)
            i = i + 1
            s = s + 1
        
        # Preencher lista diascompletos com datas formatadas igual aos ids dos tickets para futura comparação
        i = 0;
        while i < len(diasmes):
            mes = today.month
            mesf = ''
            if mes < 10:
                mesf = '0' + str(mes)
            diascompletos.append(str(i+1)+ mesf+ str(today.year))
            i = i + 1
        
        # Preencher lista com os dias do mes anterior presentes na primeira semana do mes vigente
        if primeirodiasemana < 6:
            i = 0
            mesanterior = []
            while i < (primeirodiasemana+1):
                mesanterior.append(' ')
                i = i + 1
            diasmes = mesanterior + diasmes
            weekdays = mesanterior + weekdays
            diascompletos = mesanterior + diascompletos

        return {'diascompletos': diascompletos, 'weekdays': weekdays, 'weekdayslabel': weekdayslabel, 'smallweekdayslabel': smallweekdayslabel, 'primeirodiasemana': primeirodiasemana, 'diasmes': diasmes, 'hoje': today.day,'hojemesint': today.month -1, 'hojemes': meses[today.month -1], 'hojeano': today.year, 'lastday': numerodiasmes}
    