# -*- coding: utf-8 -*-
from django.contrib import messages
from django.shortcuts import render, redirect, resolve_url as r
from django.views.decorators.csrf import csrf_exempt

from restaurante.core.forms import LoginForm
import sys

from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import pessoa, aluno, admin, prato, usuariorestaurante, venda
from django.db import connection
import datetime

# Create your views here.
def Home(request):
    try:# Verificar se usuario esta logado
        if request.session['nome']:
            # Chama a página inicial - index
            # Pegar lista de tikets disponiveis
            return render(request, 'index.html', {'err': '', 'itemselec': 'HOME'})
    except KeyError:###################---- LOGIN ----###################### Se der excecao mostrar tela de login
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
                            # Salva na sessão o id da pessoa
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
                    pessoaobj = pessoa(nome=request.session['nome'], usuario=request.session['userl'], status=True)
                    pessoaobj.save()
                    # Verificar tipo de usuário
                    if(request.session['usertip'] == 'aluno'): # Cadastrar Aluno
                        alunoobj = aluno(id_pessoa=pessoaobj)
                        alunoobj.save()
                    elif(request.session['usertip'] == 'admin'): # Cadastrar Admin
                        adminobj = admin(id_pessoa=pessoaobj)
                        adminobj.save()
                    return redirect('/restaurante')
            else:# Se os dados não são válidos, mostra tela de login com os erros destacados
                return render('login.html', {'form': form, 'err': '', 'itemselec': 'HOME',}, request)
        else:# se não veio nada no post cria uma instancia vazia
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
def Logout(request):
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


def Venda(request):
    usuario = '2306214'
    senha = 'mushramboo4'
    ou = 'DC=ifto, DC=local'

    con = conexaoAD(usuario, senha, ou)
    ListaAlunos = []
    for lista in con.ListaAlunos():
        if lista.get('raw_attributes'):
            ListaAlunos.append({
                'nome': lista['raw_attributes']['displayName'][0],
                'cpf': lista['raw_attributes']['sAMAccountName'][0],
            })

    return render(request, 'venda.html', {
        'title': 'Home',
        'itemselec': 'HOME',
        'step': 'pri',
        'alunos': ListaAlunos,
    })


@csrf_exempt
def Vender(request, id_pessoa):
    if request.method == 'POST':
        horafechamento = datetime.time(23, 59)
        id_aluno = request.POST['id_aluno']
        restricoes = Restricoes(horafechamento, id_aluno)
        if not restricoes['status']:
            vendaobj = SalvarVenda(request, id_aluno, 1)
            vendaobj.save()
            messages.success(request, "Venda realizada com sucesso")
            return redirect(r('Venda'))
        else:
            messages.error(request, restricoes['erro'])
            return redirect(r('Venda'))
    else:
        data = datetime.datetime.now()
        pratoobj = ExistePratoCadastrado(1)
        if pratoobj:
            dados = ExisteAlunoCadastrado(id_pessoa)
            if not dados:
                dados = SalvaAluno(id_pessoa)
            return render(request, 'venda.html', {
                'title': 'Home',
                'itemselec': 'HOME',
                'step': 'fim',
                'dados': dados,
                'data': data,
                'prato': pratoobj,
            })
        else:
            return render(request, 'venda.html', {
                'title': 'Home',
                'itemselec': 'HOME',
                'step': 'notprato',
            })


def SalvaAluno(id):
    usuario = '2306214'
    senha = 'mushramboo4'
    ou = 'DC=ifto, DC=local'

    con = conexaoAD(usuario, senha, ou)
    nomealuno = con.DadosAluno(id)[0]['raw_attributes']['displayName'][0]

    pessoaobj = pessoa(nome=nomealuno, usuario=id, status=True)
    pessoaobj.save()

    alunoobj = aluno(id_pessoa=pessoaobj)
    alunoobj.save()

    return {'pessoa': pessoaobj, 'aluno': alunoobj}


def ExistePratoCadastrado(id):
    try:
        return prato.objects.get(id=id)
    except:
        return False


def ExisteAlunoCadastrado(id_pessoa):
    try:
        dados = aluno.objects.select_related('id_pessoa').get(id_pessoa__usuario=id_pessoa)
        return {'pessoa': dados.id_pessoa, 'aluno': dados}
    except:
        return False


def SalvarVenda(request, id_aluno, id_prato):
    data = datetime.datetime.now()

    pratoobj = prato.objects.get(id=id_prato)
    usuariorestauranteobj = usuariorestaurante.objects.select_related('id_pessoa').get(id_pessoa__usuario=str(request.session['userl']))
    alunoobj = aluno.objects.get(id=id_aluno)

    vendaobj = venda(data=data, valor=pratoobj.preco, id_aluno=alunoobj, id_prato=pratoobj, id_usuario_restaurante=usuariorestauranteobj)
    vendaobj.save()

    return vendaobj


def Restricoes(horafechamento, id_aluno):
    hoje = datetime.datetime.today()
    if hoje.time() < horafechamento:
        vendaobj = venda.objects.filter(data__contains=hoje.date(), id_aluno=id_aluno)
        if vendaobj:
            return {'status': True, 'erro': "Aluno já realizou compra hoje"}
        return {'status': False, 'erro': "Não há restrições"}
    else:
        return {'status': True, 'erro': "O horário das vendas está encerrado"}