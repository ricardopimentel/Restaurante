# -*- coding: utf-8 -*-
import os

from django.shortcuts import render, redirect
from restaurante.core.forms import LoginForm
import sys
from restaurante.core.models import pessoa, aluno, admin, ticket, prato, venda, usuariorestaurante
from restaurante.core.libs.calendario import calendario
import datetime
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import pdfkit
from django.http.response import HttpResponse
from django.template.loader import get_template
import platform

def cancelarTicketsVencidos():
    # Verificar se há algum ticket do mes anterior ativos e caso haja, mudar o status para false
    today = datetime.date.today() # Data de hj do sistema
    ticketsantigos = ticket.objects.filter(data_criacao__range=[datetime.datetime(1989, 1, 1, 00, 00, 00, 000000), datetime.datetime(today.year, today.month, 1, 00, 00, 00, 000000)], status = True)
    # Percorre a lista dos tickets antigos e muda o status para false
    for item in ticketsantigos:
        item.status = False
        item.save()

# Create your views here.
def home(request):
    try: # Verificar se usuario esta logado
        if request.session['nome']:
            # Chama a página inicial - index
            # Pegar lista de tikets disponiveis
            if(request.session['usertip'] == 'aluno'):# Verifica se é aluno
                # Verificar se há algum ticket do mes anterior ativos e caso haja, mudar o status para false
                cancelarTicketsVencidos()
                # Pega todos os tickets com status = true
                ticketobj = ticket.objects.filter(status = True, id_aluno = request.session['idaluno'])
                return render(request, 'index.html', {'err': '', 'itemselec': 'HOME', 'tickets': ticketobj})
            else:
                return render(request, 'index.html', {'err': '', 'itemselec': 'HOME'})
    except KeyError: ###################---- LOGIN ----###################### Se der excecao mostrar tela de login
        # Se vier algo pelo post significa que houve requisição
        if request.method == 'POST':
            # Cria uma instancia do formulario com os dados vindos do request POST:
            form = LoginForm(request, data=request.POST)
            # Checa se os dados são válidos:
            if form.is_valid():
                # Logou no ad, verificar se está salvo no banco de dados
                try:
                    pess = pessoa.objects.get(usuario=request.session['userl'])
                    if pess:# Pessoa Cadastrada
                        # Pessoa cadastrada, abrir página inicial
                        if(request.session['usertip'] == 'aluno'): # Se for aluno, mostrar tela de aluno
                            # Salva na sessão o id da pesoa
                            request.session['idpessoa'] = pess.id
                            # Salva id do aluno
                            cursor = connection.cursor()
                            cursor.execute("SELECT aluno.id from core_pessoa pessoa, core_aluno aluno WHERE pessoa.id = aluno.id_pessoa_id and pessoa.id = '"+ str(request.session['idpessoa'])+"'")
                            idaluno = cursor.fetchall()
                            request.session['idaluno'] = idaluno[0][0]
                        return redirect('/restaurante')
                except:
                    print(sys.exc_info())
                    # Pessoa não cadastrada - Fazer cadastro
                    pessoaobj = pessoa(nome = request.session['nome'], usuario = request.session['userl'], status = True)
                    pessoaobj.save()
                    # Verificar tipo de usuário
                    if(request.session['usertip'] == 'aluno'): # Cadastrar Aluno
                        alunoobj = aluno(id_pessoa = pessoaobj)
                        alunoobj.save()
                    elif(request.session['usertip'] == 'admin'): # Cadastrar Admin
                        adminobj = admin(id_pessoa = pessoaobj)
                        adminobj.save()
                    return redirect('/restaurante')
            else: # Se os dados não são válidos, mostra tela de login com os erros destacados
                return render('login.html', {'form': form, 'err': '', 'itemselec': 'HOME',}, request)
        else: # se não veio nada no post cria uma instancia vazia
            # Criar instancia vazia do formulario de login
            request.session['menu'] = ['HOME']
            request.session['url'] = ['restaurante/']
            request.session['img'] = ['home24.png']
            form = LoginForm(request)
            return render(request, 'login.html', {
             'title': 'Home',
             'itemselec': 'HOME',
             'form': form,
             })
# Create your views here.
def logout(request):
    try:
        del request.session['nome']
        del request.session['mail']
        del request.session['curso']
        del request.session['userl']
        del request.session['menu']
        del request.session['url']
        
    except KeyError:
        print(sys.exc_info())
    return redirect("/restaurante")

def geraticket(request):
    try: # Verificar se usuario esta logado
        if request.session['nome']:
            # Pegar ID do aluno
            idaluno = request.session['idaluno']
            # Cria instancia da classe calendario
            calendarobj = calendario()
            # Pega od dados necessarios para montar visão do calendario
            dadospagina = calendarobj.getCalendario()
            #ticketobj = ticket.objects.get(status = True, id_aluno = 1)
            ticketobj = ticket.objects.filter(id_aluno = idaluno)
            # Se vier algo pelo post significa que houve requisição
            if request.method == 'POST':
                diasmes = range(1, dadospagina['lastday'] + 1) # Gera lista com todos os dias do mes
                for dia in diasmes:
                    try:
                        cb = request.POST[str(dia)]
                        if cb:
                            mes = dadospagina['hojemesint']+1
                            mesf = ''
                            if mes < 10:
                                mesf = '0' + str(mes)
                            else:
                                mesf = str(mes)
                            label = str(dia) + mesf+ str(dadospagina['hojeano'])
                            tk = ticket(rotulo = label, data_criacao = datetime.datetime.today(), status = True, id_aluno = aluno.objects.get(id = idaluno))
                            tk.save()
                    except:
                        print(sys.exc_info())
                return redirect('/restaurante')
            # Adiciona componentes
            dadospagina['err'] = ''
            dadospagina['itemselec'] = 'HOME'
            dadospagina['tickets'] = ticketobj
            dadospagina['hora'] = datetime.datetime.today().time
            dadospagina['horafechamento'] = datetime.time(14, 0o3)
            
            print(datetime.datetime.today().time)
            
            return render(request, 'geraticket.html', dadospagina)
    except KeyError:
        return redirect('/restaurante/login')

@csrf_exempt
def vender(request, idaluno, idticket, idprato):
    try:# Verificar se usuario esta logado
        if request.session['nome']:
            # Pegar alunos cujo o status da pessoa relacionada seja true
            alunos = aluno.objects.select_related().filter(id_pessoa__status=True)
            
            if idaluno == '***aluno***' and idticket == '***ticket***' and idprato == '***prato***': # URL Padrão
            
                return render(request, 'venda.html', {'err': '', 'itemselec': 'HOME', 'step': 'pri', 'alunos': alunos})
            
            elif not idaluno == '***aluno***' and idticket == '***ticket***'  and idprato == '***prato***':
                # Pegar nome do aluno
                nome = aluno.objects.select_related().get(id=idaluno)
                # Pega os tickets do aluno
                tiquetes = ticket.objects.filter(id_aluno = idaluno, status = True)
                if tiquetes:
                    return redirect('/restaurante/venda/'+idaluno+'/'+str(tiquetes[0].id)+'/1')
                else:
                    return render(request, 'venda.html', {'err': '', 'itemselec': 'HOME', 'step': 'seg', 'nome': nome, 'alunos': alunos, 'tiquetes': tiquetes, 'idaluno': idaluno, 'idticket': idticket})
            
            elif not idaluno == '***aluno***' and not idticket == '***ticket***' and idprato == '***prato***':
                # Pegar nome do aluno
                nome = aluno.objects.select_related().get(id=idaluno)
                # Pega os tickets do aluno
                tiquetes = ticket.objects.filter(id_aluno = idaluno)
                # Pega os pratos disponiveis
                pratos = prato.objects.filter(status = True)
                
                return render(request, 'venda.html', {'err': '', 'itemselec': 'HOME', 'step': 'ter', 'nome': nome, 'alunos': alunos, 'tiquetes': tiquetes, 'idaluno': idaluno, 'idticket': idticket, 'pratos': pratos})
            
            elif not idaluno == '***aluno***' and not idticket == '***ticket***' and not idprato == '***prato***': # Finalizar venda
                # Pegar nome do aluno
                Aluno = aluno.objects.select_related().get(id=idaluno)
                # Data
                data = datetime.datetime.today()
                # Prato
                Prato = prato.objects.get(id = idprato)
                # Se vier algo pelo post significa que houve requisição
                if request.method == 'POST':
                    # Pega ticket
                    tick = ticket.objects.get(id = idticket)
                    tick.status = False # Desabilita ticket usado
                    tick.save()
                    # gera venda
                    ven = venda(data = data, valor = Prato.preco, id_prato = Prato, id_ticket = tick, id_usuario_restaurante = usuariorestaurante.objects.get(id = 1))
                    ven.save()
                    
                    return redirect('/restaurante/venda/***aluno***/***ticket***/***prato***')
                    
                return render(request, 'venda.html', {'err': '', 'itemselec': 'HOME', 'prato': Prato, 'data': data, 'step': 'fim', 'aluno': Aluno, 'ticket': idticket})
    except KeyError:
        return redirect('/restaurante/login')

def relatorios(request):
    try: # Verificar se usuario esta logado
        if request.session['nome']:
            return render(request, 'relatorios.html', {'err': '', 'itemselec': 'HOME'})
    except KeyError:
        return redirect('/restaurante/login')

@csrf_exempt
def relatoriovendas(request):
    try: # Verificar se usuario esta logado        
        if request.session['nome']:
            # inicializar váriaveis 
            vd = ''
            soma = 0
            datainicial = ''
            datafinal = ''
            err = ''
            
            if request.method == 'POST':
                # Pega valores do POST
                datainicial = request.POST['data-inicial']
                datafinal = request.POST['data-final']
                alunoselecionado = request.POST['aluno-selecionado']
                
                if datainicial > datafinal:
                    err = 'Erro no período informado'
                else:
                    if alunoselecionado == ' ':
                        alunoselecionado = ''
                        # Pega no bd os dados da vas vendas, de todos os aluno
                        vd = venda.objects.select_related().filter(data__range=[datainicial+ ' 00:00:00', datafinal+ ' 23:59:59']) # Filtrar pela data apenas
                    else:
                        # Pega no bd os dados da vas vendas, filtrando por aluno
                        vd = venda.objects.select_related().filter(data__range=[datainicial+ ' 00:00:00', datafinal+ ' 23:59:59'], id_ticket__id_aluno = alunoselecionado)
                # Salva valores na sessão p preencher automaticamente posteriormente
                request.session['data-inicial'] = datainicial
                request.session['data-final'] = datafinal
                request.session['aluno-selecionado'] = alunoselecionado
                
            try:
                # Pega valores da sessao para jogar no formulario
                datai = request.session['data-inicial']
                dataf = request.session['data-final']
            except KeyError:
                datai = ''
                dataf = ''
            
            try:
                alunoselecionado = request.session['aluno-selecionado']
            except KeyError:
                alunoselecionado = ''
            
            # Somar valor das vendas no periodo
            for vend in vd:
                soma = soma + vend.valor
            
            # Pegar lista de alunos cujo o status da pessoa relacionada seja true
            alunos = aluno.objects.select_related().filter(id_pessoa__status=True)
            
            return render(request, 'relatoriovendas.html', {'err': err, 'soma': soma, 'datainicial': datainicial, 'datafinal': datafinal, 'alunos': alunos, 'itemselec': 'HOME', 'inicial': datai, 'final': dataf, 'alunoenviado': alunoselecionado, 'venda': vd})
    except KeyError:
        return redirect('/restaurante/login')

@csrf_exempt
def pdfvendas(request):   
    # Verificar se usuario esta logado
    try:              
        if request.session['nome']:
            # Iniciar Variaveis
            soma = 0
            alunoselecionado = ''
            
            # Verificar dados salvos na sessão
            try:
                #Se tiver data salva na sessão
                if(request.session['data-inicial']):
                    datainicial = request.session['data-inicial'] # Pega data da sessão
                if(request.session['data-final']):
                    datafinal = request.session['data-final'] # Pega data da sessão
                if(request.session['aluno-selecionado']):
                    alunoselecionado = request.session['aluno-selecionado'] # Pega usuário da sessão
            except:
                pass
            
            if alunoselecionado == '':
                # Pega no bd os dados da vas vendas, de todos os aluno
                vd = venda.objects.select_related() # Filtrar pela data apenas
            else:
                # Pega no bd os dados da vas vendas, filtrando por aluno
                vd = venda.objects.select_related().filter(id_ticket__id_aluno = alunoselecionado)
            
            # Somar valor das vendas no periodo
            for vend in vd:
                soma = soma + vend.valor
            
            # Nome do aluno selecionado
            if alunoselecionado:
                Aluno = aluno.objects.get(id = alunoselecionado)
            else:
                Aluno = ''

            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            context = {'title': 'Relatório PDF',
                       'pagesize':'A4',
                       'soma': soma,
                       'datainicial': datetime.datetime.strptime(str(datainicial), '%Y-%m-%d').strftime('%d/%m/%Y'),
                       'datafinal': datetime.datetime.strptime(str(datafinal), '%Y-%m-%d').strftime('%d/%m/%Y'),
                       'venda': vd,
                       'aluno': Aluno,
                       'base_dir': BASE_DIR,
                       }
            
            template = get_template("pdfvendas.html")
            html = template.render(context)
            
            #path_wkthmltopdf = '/usr/bin/wkhtmltopdf'
            # Verificar se o sistema é windows
            if platform.system() == 'Windows':
                path_wkthmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            else:
                path_wkthmltopdf = '/usr/bin/wkhtmltopdf'

            config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
            options = {
                'encoding': 'utf-8',
                'footer-left': 'IFTO - Campus de Paraiso do Tocantins [date]',
                'footer-right': 'Pag. [page] de [topage]',
            }
            
            # Use False instead of output path to save pdf to a variable
            pdf = pdfkit.from_string(html, False, configuration=config, options=options)
            response = HttpResponse(pdf, content_type='application/pdf')
            return response
    except KeyError:
        return redirect('/restaurante/login')
    
    
@csrf_exempt
def relatorioticketsdia(request):
    try: # Verificar se usuario esta logado        
        if request.session['nome']:
            # inicializar váriaveis
            err = ''
            # Rotulo gerado pelo data atual
            today = datetime.datetime.today()
            mes = today.month
            mesf = ''
            if mes < 10:
                mesf = '0' + str(mes)
            else:
                mesf = str(mes)
            label = str(today.day) + mesf+ str(today.year)

            # Pega no bd os dados do ticket
            tick = ticket.objects.select_related().filter(rotulo = label, status = True)
            
            return render(request, 'relatorioticketsdiario.html', {'err': err, 'itemselec': 'HOME', 'tickets': tick})

    except KeyError:
        return redirect('/restaurante/login')
