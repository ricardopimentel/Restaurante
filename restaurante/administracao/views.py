import sys
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, resolve_url as r


# Create your views here.
from restaurante.administracao.forms import AdForm, CadastroPratoForm, ConfigHorarioLimiteVendasForm, \
    CadastroAlunosBolsistasForm
from restaurante.administracao.models import config
from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import prato, alunoscem, pessoa
from restaurante.venda.views import ExisteAlunoCadastrado, SalvaAluno

# Eu sei que tenho que trocar isso
usuario = 'winbackup'
senha = 'v4c4pr3t4'

def Administracao(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            return render(request, 'administracao/administracao.html', {
                'title': 'Administração',
                'itemselec': 'ADMINISTRAÇÃO',
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def Configuracao(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'):  # Verifica permissão de gerente ou admin
            return render(request, 'administracao/configuracao.html', {
                'title': 'Configuração',
                'itemselec': 'CONFIGURAÇÃO',
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def Dados_ad(request):
    if dict(request.session).get('nome'):  # verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin': # Verifica permissão de administrador
            try:
                model = (config.objects.get(id=1))
                # Vefirica se veio aolgo pelo POST
                if request.method == 'POST':
                    # cria uma instancia do formulario de preenchimento dos dados do AD com os dados vindos do request POST:
                    form = AdForm(request, data=request.POST)
                    # Checa se os dados são válidos:
                    if form.is_valid():
                        # Chama a página novamente
                        messages.success(request, 'Configurações salvas com sucesso!')
                    return render(request, 'administracao/admin_config_ad.html', {'form': form})
                else:
                    form = AdForm(request, initial={
                        'dominio': model.dominio,
                        'endservidor': model.endservidor,
                        'gadmin': model.gadmin,
                        'ou': model.ou, 'filter': model.filter
                    })
                    return render(request, 'administracao/admin_config_ad.html', {
                        'title': 'Config. LDAP',
                        'itemselec': 'ADMINISTRAÇÃO',
                        'form': form,
                    })
            except ObjectDoesNotExist:
                model = ''
                messages.error(request, sys.exc_info())
                return redirect(r('Administracao'))
        else:
            messages.error(request, "Você não tem permissão para acessar essa página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))

def ConfigInicial(request):
    form = AdForm(request)
    if request.method == 'POST':
        # cria uma instancia do formulario de preenchimento dos dados do AD com os dados vindos do request POST:
        form = AdForm(request, data=request.POST)
        # Checa se os dados são válidos:
        if form.is_valid():
            return redirect(r('Login'))
    return render(request, 'administracao/admin_config_ad_inicial.html', {
        'title': 'Config. Inicial',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
    })


def CadastroPrato(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            form = CadastroPratoForm()
            pratos = prato.objects.all()
            if request.method == 'POST':
                form = CadastroPratoForm(data=request.POST)
                if form.is_valid():
                    messages.success(request, 'Prato Cadastrado Com Sucesso!!')
                    return redirect(r('CadastroPrato'))
            return render(request, 'administracao/admin_cadastro_prato.html', {
                'title': 'Cadastro de Prato',
                'itemselec': 'ADMINISTRAÇÃO',
                'form': form,
                'pratos': pratos,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))

def ExcluirPratos(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            check = False
            pratos = prato.objects.all()
            for item in pratos:
                if request.POST.get(str(item.id)):
                    check = True
                    try:
                        item.delete()
                        messages.success(request, 'Prato '+ item.descricao+ ' excluído')
                    except:
                        messages.error(request, 'Erro ao exluir prato '+ item.descricao)
            if not check:
                messages.error(request, 'Selecione pelo menos 1 prato para excluir')
            return redirect(r('CadastroPrato'))
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def ExcluirBolsistas(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'):  # Verifica permissão de gerente ou admin
            menu = 'CONFIGURAÇÃO'
            if (dict(request.session).get('usertip') == 'admin'):
                menu = 'ADMINISTRAÇÃO'
            bolsistas = alunoscem.objects.select_related('id_pessoa')
            if request.method == 'POST':
                check = False
                for aluno in bolsistas:
                    if request.POST.get(str(aluno.id)):
                        check = True
                        try:
                            aluno.delete()
                            messages.success(request, 'Bolsista '+ str(aluno.id_pessoa.nome)+ ' excluído')
                        except:
                            messages.error(request, 'Erro ao exluir bolsista '+ str(aluno.id))
                if not check:
                    messages.error(request, 'Selecione pelo menos 1 aluno para excluir')
                return redirect(r('ExcluirBolsistas'))
            else:
                return render(request, 'administracao/admin_conferir_cadastro_bolsistas.html', {
                    'title': 'Lista de Bolsistas 100%',
                    'itemselec': menu,
                    'bolsistas': bolsistas,
                })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def EditarPrato(request, id_prato):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            pratos = prato.objects.all()
            pratoobj = pratos.get(pk=id_prato)
            form = CadastroPratoForm(initial={'descricao': pratoobj.descricao, 'preco': pratoobj.preco, 'status': pratoobj.status, 'id': id_prato})

            return render(request, 'administracao/admin_cadastro_prato.html', {
                'title': 'Cadastro de Prato',
                'itemselec': 'ADMINISTRAÇÃO',
                'form': form,
                'pratos': pratos,
                'id': id_prato,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))

def HorarioLimiteVendas(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            configobj = config.objects.get(id=1)
            form = ConfigHorarioLimiteVendasForm(initial={'hora_fechamento_vendas': configobj.hora_fechamento_vendas})
            if request.method == 'POST':
                form = ConfigHorarioLimiteVendasForm(data=request.POST)
                # Checa se os dados são válidos:
                if form.is_valid():
                    try:
                        configobj.hora_fechamento_vendas = form.cleaned_data['hora_fechamento_vendas']
                        configobj.save()
                        messages.success(request, 'Horário salvo com sucesso!')
                    except:
                        messages.error(request, 'Erro ao atualizar o horario de fechamento das vendas.')
                    return redirect(r('HorarioLimiteVendas'))
            return render(request, 'administracao/admin_config_horario_limite_vendas.html', {
                'title': 'Cadastro de Prato',
                'itemselec': 'ADMINISTRAÇÃO',
                'form': form,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def Tutoriais(request, action):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            form = CadastroPratoForm()
            pratos = prato.objects.all()
            if request.method == 'POST':
                form = CadastroPratoForm(data=request.POST)
                if form.is_valid():
                    messages.success(request, 'Prato Cadastrado Com Sucesso!!')
                    return redirect(r('CadastroPrato'))
            return render(request, 'administracao/admin_cadastro_prato.html', {
                'title': 'Cadastro de Prato',
                'itemselec': 'ADMINISTRAÇÃO',
                'form': form,
                'pratos': pratos,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def CadastroBolsistas(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'): # Verifica permissão de gerente ou admin
            menu = 'CONFIGURAÇÃO'
            if (dict(request.session).get('usertip') == 'admin'):
                menu = 'ADMINISTRAÇÃO'
            ListaErros = []
            ListaAcertos = []
            form = CadastroAlunosBolsistasForm()
            if request.method == 'POST':#se vier pelo post
                ListaAlunosAD = GetListaEstudantesAD()
                form = CadastroAlunosBolsistasForm(data=request.POST)
                if form.is_valid():#se o formulário foi válido, ou seja todos os campos obrigatórios preecnhidos
                    usuarios = form.cleaned_data['usuarios']
                    ListaCPFsDigitados = list(map(str, usuarios.split('\n'))) #Transforma todos os cpfs digitados no campo usuários em uma lista
                    # Percorre a lista de cpfs
                    for cpf in ListaCPFsDigitados:
                        cpf = str(cpf.replace('\r', ''))
                        if (cpf in ListaAlunosAD):
                            try:
                                alunoobj = ExisteAlunoCadastrado(cpf)
                                if alunoobj:
                                    pessoaobj = pessoa.objects.get(usuario=cpf) #pega uma instancia da pessoa com o cpf listado
                                    aluno = ExisteAlunoCadastrado(pessoaobj.id)
                                else:
                                    retorno = SalvaAluno(cpf)
                                    aluno = retorno['aluno']
                                    pessoaobj = retorno['pessoa']
                                cem = alunoscem(id_pessoa=pessoaobj)
                                cem.save()
                                ListaAcertos.append("O CPF: "+ cpf+ " Foi adicionado com sucesso!")
                            except:
                                ListaErros.append("O CPF: "+ cpf+ " Não foi adicionado")
                        else:
                            ListaErros.append("O CPF: "+ cpf+ " Não é de um aluno do IFTO")
                    return render(request, 'administracao/admin_cadastro_bolsistas.html', {
                        'title': 'Cadastro de Bolsistas',
                        'ListaErros': ListaErros,
                        'ListaAcertos': ListaAcertos,
                        'itemselec': menu,
                        'form': CadastroAlunosBolsistasForm(),
                    })
            return render(request, 'administracao/admin_cadastro_bolsistas.html', {
                'title': 'Cadastro de Bolsistas',
                'itemselec': menu,
                'form': form,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def GetListaEstudantesAD():
    ListaAlunos = []
    con = conexaoAD(usuario, senha)
    retorno = con.ListaAlunos()

    if str(retorno) == 'i':
        return False
    else:
        for lista in retorno:
            try:
                if lista.get('raw_attributes'):
                    ListaAlunos.append((lista['raw_attributes']['sAMAccountName'][0]).decode('UTF-8'))
            except:
                return False
        return ListaAlunos