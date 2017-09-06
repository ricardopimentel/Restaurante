# -*- coding: utf-8 -*-
from django.contrib import messages
from django.shortcuts import render, redirect, resolve_url as r
from django.views.decorators.csrf import csrf_exempt

from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import pessoa, aluno, prato, usuariorestaurante, venda
import datetime

# Create your views here.
def Home(request):
    try:# Verificar se usuario esta logado
        if request.session['nome']:
            # Chama a página inicial - index
            # Pegar lista de tikets disponiveis
            return render(request, 'index.html', {'err': '', 'itemselec': 'HOME'})
    except KeyError:
        return redirect(r('Login'))


def Venda(request):
    usuario = '2306214'
    senha = 'mushramboo4'

    con = conexaoAD(usuario, senha)
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

    con = conexaoAD(usuario, senha)
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