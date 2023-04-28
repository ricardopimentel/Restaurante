import sys
from django.contrib import messages
from django.shortcuts import render, redirect, resolve_url as r
from django.views.decorators.csrf import csrf_exempt
from restaurante.administracao.models import config
from restaurante.core.libs.calendario import calendario
from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import pessoa, aluno, prato, usuariorestaurante, venda, alunoscem
import datetime

from restaurante.venda.forms import ConfirmacaoVendaForm

# Eu sei que tenho que trocar isso
usuario = 'winbackup'
senha = 'v4c4pr3t4'

# Views
def Vendas(request):
    if dict(request.session).get('nome'):
        return render(request, 'venda/vendas.html', {
            'title': 'Vendas',
            'itemselec': 'VENDAS',
        })
    return redirect(r('Login'))

def Venda(request):
    ListaAlunos = []
    con = conexaoAD(usuario, senha)
    retorno = con.ListaAlunos()

    if str(retorno) == 'i':
	    messages.error(request, 'Falha ao realizar a consulta verifique o usuário "'+ usuario+'"')
    else:
        for lista in retorno:
            try:
                if lista.get('raw_attributes'):
                    ListaAlunos.append({
                        'nome': (lista['raw_attributes']['displayName'][0]).decode('UTF-8'),
                        'cpf': (lista['raw_attributes']['sAMAccountName'][0]).decode('UTF-8'),
                    })
            except:
                messages.error(request, str(sys.exc_info()[1]))
    return render(request, 'venda/venda.html', {
        'title': 'Venda',
        'itemselec': 'VENDAS',
        'step': 'pri',
        'alunos': ListaAlunos,
    })

def VendaLotes(request):
    ListaAlunos = []
    con = conexaoAD(usuario, senha)
    if str(con.ListaAlunos()) == 'i':
        messages.error(request, 'Falha ao realizar a consulta verifique o usuário "' + usuario + '"')
    else:
        for lista in con.ListaAlunos():
            try:
                if lista.get('raw_attributes'):
                    ListaAlunos.append({
                        'nome': lista['raw_attributes']['displayName'][0],
                        'cpf': lista['raw_attributes']['sAMAccountName'][0],
                    })
            except:
                messages.error(request, str(sys.exc_info()[1]))

    return render(request, 'venda/venda_em_lotes.html', {
        'title': 'Venda',
        'itemselec': 'VENDAS',
        'step': 'pri',
        'alunos': ListaAlunos,
    })


def VenderLotes(request, id_pessoa):
    if request.method == 'POST':
        messages.success(request, "Você quer vender")
    calendarobj = calendario()

    # Pega od dados necessarios para montar visão do calendario
    dadospagina = calendarobj.getCalendario()
    dadospagina['title'] = 'Venda'
    dadospagina['itemselec'] = 'VENDAS'
    dadospagina['step'] = 'seg'
    return render(request, 'venda/venda_em_lotes.html', dadospagina)


@csrf_exempt
def Vender(request, id_pessoa):
    form = ConfirmacaoVendaForm(request, id_pessoa)
    if request.method == 'POST':
        form = ConfirmacaoVendaForm(request, id_pessoa, data=request.POST)
        if form.is_valid():
            id_aluno = request.POST['id_aluno']
            restricoes = Restricoes(id_aluno)
            if not restricoes['status']:
                vendaobj = SalvarVenda(request, id_aluno, 1, id_pessoa)
                if vendaobj:
                    messages.success(request, "Venda realizada com sucesso")
                return redirect(r('Venda'))
            else:
                messages.error(request, restricoes['erro'])
                return redirect(r('Venda'))

    data = datetime.datetime.now()
    print(data.hour)
    pratoobj = ExistePratoCadastrado(data.hour)
    cem = False
    if pratoobj:
        aluno = ExisteAlunoCadastrado(id_pessoa)
        try:
            cem = alunoscem.objects.select_related('id_pessoa').get(id_pessoa__usuario=id_pessoa)
        except:
            cem = False
        if not aluno:
            aluno = SalvaAluno(id_pessoa)

        return render(request, 'venda/venda.html', {
            'title': 'Venda',
            'itemselec': 'VENDAS',
            'step': 'fim',
            'dados': aluno,
            'data': data,
            'prato': pratoobj,
            'formulario': form,
            'cem': cem,
        })
    else:
        return render(request, 'venda/venda.html', {
            'title': 'Venda',
            'itemselec': 'VENDA',
            'step': 'notprato',
        })

# Métodos aplicados nas views
def SalvaAluno(cpf):
    con = conexaoAD(usuario, senha)
    nomealuno = (con.DadosAluno(cpf)[0]['raw_attributes']['displayName'][0]).decode('UTF-8')

    pessoaobj = pessoa(nome=nomealuno, usuario=cpf, status=True)
    pessoaobj.save()

    alunoobj = aluno(id_pessoa=pessoaobj)
    alunoobj.save()

    return {'pessoa': pessoaobj, 'aluno': alunoobj}


def ExistePratoCadastrado(hora):
    id = False
    if hora <= 14:
        id = "Almoço"
    else:
        id = "Janta"
    try:
        return prato.objects.get(descricao=id)
    except:
        return False


def ExisteAlunoCadastrado(id_pessoa):
    try:
        dados = aluno.objects.select_related('id_pessoa').get(id_pessoa__usuario=id_pessoa)
        return {'pessoa': dados.id_pessoa, 'aluno': dados}
    except:
        return False


def SalvarVenda(request, id_aluno, id_prato, id_pessoa):
    try:
        data = datetime.datetime.now()

        pratoobj = prato.objects.get(id=id_prato)
        usuariorestauranteobj = usuariorestaurante.objects.select_related('id_pessoa').get(id_pessoa__usuario=str(request.session['userl']))
        alunoobj = aluno.objects.get(id=id_aluno)

        #Verificar se a bolsa é 100%
        try:
            cem = alunoscem.objects.select_related('id_pessoa').get(id_pessoa__usuario=id_pessoa)
            precoprato = (pratoobj.preco * 2)
        except:
            precoprato = pratoobj.preco
        #criar objeto da venda
        vendaobj = venda(data=data, valor=precoprato, id_aluno=alunoobj, id_prato=pratoobj, id_usuario_restaurante=usuariorestauranteobj)
        vendaobj.save()#salva venda

        return True
    except:
        messages.error(request, 'O usuário não tem permissão para realizar a venda. '+ str(sys.exc_info()[1]))
        return False


def Restricoes(id_aluno):
    try:
        horafechamento = config.objects.get(id=1).hora_fechamento_vendas
        hoje = datetime.datetime.today()
        if hoje.time() < horafechamento:
            vendaobj = venda.objects.filter(data__contains=hoje.date(), id_aluno=id_aluno)
            if vendaobj:
                return {'status': True, 'erro': "Aluno já realizou compra hoje"}
            return {'status': False, 'erro': "Não há restrições"}
    except:
        return {'status': True, 'erro': "Falha ao verificar o horário de fechamento"}
    else:
        return {'status': True, 'erro': "O horário das vendas está encerrado"}
