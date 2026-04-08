import sys
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, resolve_url as r
import json


# Create your views here.
from restaurante.administracao.forms import AdForm, CadastroPratoForm, ConfigHorarioLimiteVendasForm, \
    CadastroAlunosBolsistasForm, CadastroAlunosColaboradoresForm, ConfigPixForm
from restaurante.administracao.models import config
from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import prato, alunoscem, pessoa, alunoscolaboradores, CardapioDia, OpcaoAlimento
from restaurante.core.constants import FOOD_OPTIONS
from restaurante.venda.views import ExisteAlunoCadastrado, SalvaAluno
import datetime

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


def EditarPrato(request, id_prato):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            pratos = prato.objects.all()
            pratoobj = pratos.get(pk=id_prato)
            form = CadastroPratoForm(initial={'descricao': pratoobj.descricao, 'preco': pratoobj.preco, 'preco_aluno': pratoobj.preco_aluno, 'status': pratoobj.status, 'id': id_prato})
            
            if request.method == 'POST':
                form = CadastroPratoForm(data=request.POST)
                if form.is_valid():
                    messages.success(request, 'Prato editado com sucesso!!')
                    return redirect(r('CadastroPrato'))
                else:
                    messages.error(request, 'Erro ao editar prato. Verifique os campos.')

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


def CadastroColaboradores(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'): # Verifica permissão de gerente ou admin
            menu = 'CONFIGURAÇÃO'
            if (dict(request.session).get('usertip') == 'admin'):
                menu = 'ADMINISTRAÇÃO'
            ListaErros = []
            ListaAcertos = []
            form = CadastroAlunosColaboradoresForm()
            if request.method == 'POST':#se veio pelo post
                ListaAlunosAD = GetListaEstudantesAD()
                form = CadastroAlunosColaboradoresForm(data=request.POST)
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
                                colab = alunoscolaboradores(id_pessoa=pessoaobj)
                                colab.save()
                                ListaAcertos.append("O CPF: "+ cpf+ " Foi adicionado com sucesso!")
                            except:
                                ListaErros.append("O CPF: "+ cpf+ " Não foi adicionado")
                        else:
                            ListaErros.append("O CPF: "+ cpf+ " Não é de um aluno do IFTO")
                    return render(request, 'administracao/admin_cadastro_colaboradores.html', {
                        'title': 'Cadastro de Alunos Colaboradores',
                        'ListaErros': ListaErros,
                        'ListaAcertos': ListaAcertos,
                        'itemselec': menu,
                        'form': CadastroAlunosColaboradoresForm(),
                    })
            return render(request, 'administracao/admin_cadastro_colaboradores.html', {
                'title': 'Cadastro de Alunos Colaboradores',
                'itemselec': menu,
                'form': form,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def ExcluirColaboradores(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'):  # Verifica permissão de gerente ou admin
            menu = 'CONFIGURAÇÃO'
            if (dict(request.session).get('usertip') == 'admin'):
                menu = 'ADMINISTRAÇÃO'
            colaboradores = alunoscolaboradores.objects.select_related('id_pessoa')
            if request.method == 'POST':
                check = False
                for aluno in colaboradores:
                    if request.POST.get(str(aluno.id)):
                        check = True
                        try:
                            aluno.delete()
                            messages.success(request, 'Aluno Colaborador '+ str(aluno.id_pessoa.nome)+ ' excluído')
                        except:
                            messages.error(request, 'Erro ao exluir colaborador '+ str(aluno.id))
                if not check:
                    messages.error(request, 'Selecione pelo menos 1 aluno para excluir')
                return redirect(r('ExcluirColaboradores'))
            else:
                return render(request, 'administracao/admin_conferir_cadastro_colaboradores.html', {
                    'title': 'Lista de Alunos Colaboradores',
                    'itemselec': menu,
                    'colaboradores': colaboradores,
                })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def GetListaEstudantesAD():
    # tenta conectar ao banco de dados para pegar parametros do ldap
    ou = ''
    filter = ''
    try:
        conf = config.objects.get(id=1)
        ou = conf.ou
        filter = conf.filter
    except:
        pass
    ListaAlunos = []
    con = conexaoAD(usuario, senha, ou, filter)
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


def ConfigPix(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if dict(request.session).get('usertip') == 'admin':# Verifica permissão de administrador
            try:
                configobj = config.objects.get(id=1)
            except config.DoesNotExist:
                configobj = config.objects.create(id=1, dominio='', endservidor='', gadmin='', ou='', filter='')

            if request.method == 'POST':
                form = ConfigPixForm(data=request.POST, instance=configobj)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Configurações de PIX salvas com sucesso!')
                    return redirect(r('ConfigPix'))
            else:
                form = ConfigPixForm(instance=configobj)

            return render(request, 'administracao/admin_config_pix.html', {
                'title': 'Configuração PIX',
                'itemselec': 'ADMINISTRAÇÃO',
                'form': form,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def GerenciarCardapio(request):
    if not request.session.get('nome'):
        return redirect(r('Login'))
    
    # Permitir admin e lanchonete (operadores)
    if request.session.get('usertip') not in ['admin', 'lanchonete']:
        messages.error(request, "Acesso Negado.")
        return redirect(r('Home'))

    hoje = datetime.date.today()
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        itens_selecionados = request.POST.getlist('itens')
        
        if not itens_selecionados:
            messages.warning(request, "Selecione ao menos um item para o cardápio.")
        else:
            itens_str = ", ".join(itens_selecionados)
            cardapio, created = CardapioDia.objects.update_or_create(
                data=hoje,
                tipo=tipo,
                defaults={'itens': itens_str}
            )
            messages.success(request, f"Cardápio de {cardapio.get_tipo_display()} salvo com sucesso!")
            return redirect(r('GerenciarCardapio'))

    # Buscar cardápios de hoje para exibir o que já está salvo
    cardapios_hoje = CardapioDia.objects.filter(data=hoje)
    cardapio_dict = {c.tipo: c.itens.split(", ") for c in cardapios_hoje}

    # Pegar as opções do banco de dados agrupadas por categoria
    food_options = {}
    for cat_key, cat_name in OpcaoAlimento.CATEGORIAS:
        food_options[cat_name] = OpcaoAlimento.objects.filter(categoria=cat_key).values_list('nome', flat=True)

    return render(request, 'administracao/gerenciar_cardapio.html', {
        'title': 'Gerenciar Cardápio',
        'itemselec': 'HOME',
        'food_options': food_options,
        'cardapio_hoje': cardapio_dict,
        'hoje': hoje,
    })


def GerenciarOpcoesAlimento(request):
    if not request.session.get('nome') or request.session.get('usertip') not in ['admin', 'lanchonete']:
        messages.error(request, "Acesso Negado.")
        return redirect(r('Home'))

    # Carga Inicial de Proteção (se o banco estiver vazio, carrega do constants.py)
    if not OpcaoAlimento.objects.exists():
        from restaurante.core.constants import FOOD_OPTIONS
        for cat, itens in FOOD_OPTIONS.items():
            for item in itens:
                OpcaoAlimento.objects.get_or_create(nome=item, categoria=cat)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        if nome and categoria:
            try:
                OpcaoAlimento.objects.create(nome=nome, categoria=categoria)
                messages.success(request, f"Item '{nome}' adicionado com sucesso!")
            except:
                messages.error(request, "Erro ao adicionar item. Verifique se o nome já existe.")
        return redirect(r('GerenciarOpcoesAlimento'))

    opcoes = OpcaoAlimento.objects.all()
    categorias = OpcaoAlimento.CATEGORIAS

    return render(request, 'administracao/opcoes_alimento.html', {
        'title': 'Opções de Alimentos',
        'itemselec': 'HOME',
        'opcoes': opcoes,
        'categorias': categorias,
    })


def RemoverOpcaoAlimento(request, id_opcao):
    if not request.session.get('nome') or request.session.get('usertip') not in ['admin', 'lanchonete']:
        return redirect(r('Home'))
    
    try:
        opcao = OpcaoAlimento.objects.get(pk=id_opcao)
        nome = opcao.nome
        opcao.delete()
        messages.success(request, f"Item '{nome}' removido.")
    except:
        messages.error(request, "Erro ao remover item.")
    
    return redirect(r('GerenciarOpcoesAlimento'))


def ImportarOpcoesJSON(request):
    if request.method == 'POST' and request.FILES.get('arquivo_json'):
        try:
            arquivo = request.FILES['arquivo_json']
            dados = json.load(arquivo)
            
            # Formato esperado: {"Categoria": ["Item1", "Item2"]}
            count = 0
            for cat, itens in dados.items():
                # Validar categoria
                valid_cats = [c[0] for c in OpcaoAlimento.CATEGORIAS]
                if cat not in valid_cats:
                    continue
                
                for item in itens:
                    obj, created = OpcaoAlimento.objects.get_or_create(nome=item, categoria=cat)
                    if created:
                        count += 1
            
            messages.success(request, f"Importação concluída! {count} novos itens adicionados.")
        except Exception as e:
            messages.error(request, f"Erro ao processar JSON: {str(e)}")
    
    return redirect(r('GerenciarOpcoesAlimento'))


def ExportarOpcoesJSON(request):
    if not request.session.get('nome') or request.session.get('usertip') not in ['admin', 'lanchonete']:
        return redirect(r('Home'))
    
    opcoes = OpcaoAlimento.objects.all()
    dados = {}
    
    for cat_key, cat_name in OpcaoAlimento.CATEGORIAS:
        itens = list(opcoes.filter(categoria=cat_key).values_list('nome', flat=True))
        if itens:
            dados[cat_key] = itens
            
    response_data = json.dumps(dados, indent=2, ensure_ascii=False)
    
    from django.http import HttpResponse
    response = HttpResponse(response_data, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="cardapio_modelo_{datetime.date.today()}.json"'
    
    return response