import sys
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, resolve_url as r
import json
import datetime
from functools import wraps

# Create your views here.
from restaurante.administracao.forms import AdForm, CadastroPratoForm, ConfigHorarioLimiteVendasForm, \
    CadastroAlunosBolsistasForm, CadastroAlunosColaboradoresForm, ConfigPixForm, CadastroAdicionalForm
from restaurante.administracao.models import config
from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import prato, alunoscem, pessoa, alunoscolaboradores, CardapioDia, OpcaoAlimento, Adicional
from restaurante.core.constants import FOOD_OPTIONS
from restaurante.venda.views import ExisteAlunoCadastrado, SalvaAluno

# Eu sei que tenho que trocar isso
usuario = 'winbackup'
senha = 'v4c4pr3t4'

from restaurante.acesso.utils import permissao_requerida

# --- VIEWS ---

@permissao_requerida(category='ADMINISTRAÇÃO')
def Administracao(request):
    return render(request, 'administracao/administracao.html', {
        'title': 'Administração',
        'itemselec': 'ADMINISTRAÇÃO',
    })

@permissao_requerida(item_id='config_ad')
def Dados_ad(request):
    try:
        model = (config.objects.get(id=1))
        if request.method == 'POST':
            form = AdForm(request, data=request.POST)
            if form.is_valid():
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
        messages.error(request, "Configuração inicial não encontrada.")
        return redirect(r('Administracao'))

def ConfigInicial(request):
    form = AdForm(request)
    if request.method == 'POST':
        form = AdForm(request, data=request.POST)
        if form.is_valid():
            return redirect(r('Login'))
    return render(request, 'administracao/admin_config_ad_inicial.html', {
        'title': 'Config. Inicial',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
    })

@permissao_requerida(item_id='pratos_precos')
def CadastroPrato(request):
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

@permissao_requerida(item_id='pratos_precos')
def ExcluirPratos(request):
    check = False
    pratos = prato.objects.all()
    for item in pratos:
        if request.POST.get(str(item.id)):
            check = True
            try:
                item.delete()
                messages.success(request, f'Prato {item.descricao} excluído')
            except:
                messages.error(request, f'Erro ao exluir prato {item.descricao}')
    if not check:
        messages.error(request, 'Selecione pelo menos 1 prato para excluir')
    return redirect(r('CadastroPrato'))

@permissao_requerida(item_id='pratos_precos')
def EditarPrato(request, id_prato):
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

@permissao_requerida(item_id='adicionais')
def CadastroAdicional(request):
    form = CadastroAdicionalForm()
    adicionais = Adicional.objects.all()
    if request.method == 'POST':
        form = CadastroAdicionalForm(data=request.POST)
        if form.is_valid():
            messages.success(request, 'Adicional Cadastrado Com Sucesso!!')
            return redirect(r('CadastroAdicional'))
    return render(request, 'administracao/admin_cadastro_adicional.html', {
        'title': 'Cadastro de Adicional',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
        'adicionais': adicionais,
    })

@permissao_requerida(item_id='adicionais')
def ExcluirAdicionais(request):
    check = False
    adicionais = Adicional.objects.all()
    for item in adicionais:
        if request.POST.get(str(item.id)):
            check = True
            try:
                item.delete()
                messages.success(request, f'Adicional {item.nome} excluído')
            except:
                messages.error(request, f'Erro ao excluir adicional {item.nome}')
    if not check:
        messages.error(request, 'Selecione pelo menos 1 adicional para excluir')
    return redirect(r('CadastroAdicional'))

@permissao_requerida(item_id='adicionais')
def EditarAdicional(request, id_adicional):
    adicionais = Adicional.objects.all()
    obj = adicionais.get(pk=id_adicional)
    form = CadastroAdicionalForm(initial={'nome': obj.nome, 'valor': obj.valor, 'status': obj.status, 'id': id_adicional})
    
    if request.method == 'POST':
        form = CadastroAdicionalForm(data=request.POST)
        if form.is_valid():
            messages.success(request, 'Adicional editado com sucesso!!')
            return redirect(r('CadastroAdicional'))
        else:
            messages.error(request, 'Erro ao editar adicional. Verifique os campos.')

    return render(request, 'administracao/admin_cadastro_adicional.html', {
        'title': 'Cadastro de Adicional',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
        'adicionais': adicionais,
        'id': id_adicional,
    })

@permissao_requerida(item_id='horario_vendas')
def HorarioLimiteVendas(request):
    configobj = config.objects.get(id=1)
    form = ConfigHorarioLimiteVendasForm(initial={'hora_fechamento_vendas': configobj.hora_fechamento_vendas})
    if request.method == 'POST':
        form = ConfigHorarioLimiteVendasForm(data=request.POST)
        if form.is_valid():
            try:
                configobj.hora_fechamento_vendas = form.cleaned_data['hora_fechamento_vendas']
                configobj.save()
                messages.success(request, 'Horário salvo com sucesso!')
            except:
                messages.error(request, 'Erro ao atualizar o horario de fechamento das vendas.')
            return redirect(r('HorarioLimiteVendas'))
    return render(request, 'administracao/admin_config_horario_limite_vendas.html', {
        'title': 'Configuração de Vendas',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
    })

def Tutoriais(request, action):
    # Tutorial view seems to redirect back to CadastroPrato or be placeholder
    return redirect(r('CadastroPrato'))

@permissao_requerida(item_id='bolsistas')
def CadastroBolsistas(request):
    ListaErros = []
    ListaAcertos = []
    form = CadastroAlunosBolsistasForm()
    if request.method == 'POST':
        ListaAlunosAD = GetListaEstudantesAD()
        form = CadastroAlunosBolsistasForm(data=request.POST)
        if form.is_valid():
            if ListaAlunosAD is False:
                messages.error(request, "Falha ao conectar ao servidor AD. Verifique as configurações.")
            else:
                usuarios = form.cleaned_data['usuarios']
                ListaCPFsDigitados = list(map(str, usuarios.split('\n'))) 
                for cpf in ListaCPFsDigitados:
                    cpf = str(cpf.replace('\r', '').strip())
                    if not cpf: continue
                    if (cpf in ListaAlunosAD):
                        try:
                            alunoobj = ExisteAlunoCadastrado(cpf)
                            if alunoobj:
                                pessoaobj = pessoa.objects.get(usuario=cpf)
                            else:
                                retorno = SalvaAluno(cpf)
                                pessoaobj = retorno['pessoa']
                            
                            cem, created = alunoscem.objects.get_or_create(id_pessoa=pessoaobj)
                            if created:
                                ListaAcertos.append({'nome': pessoaobj.nome, 'matricula': cpf})
                            else:
                                ListaErros.append({'nome': pessoaobj.nome, 'matricula': cpf, 'erro': 'Já é bolsista.'})
                        except:
                            ListaErros.append({'matricula': cpf, 'erro': f'Erro ao processar (verifique se o aluno existe).'})
                    else:
                        ListaErros.append({'matricula': cpf, 'erro': 'Não é um aluno do IFTO.'})
            
    return render(request, 'administracao/admin_cadastro_bolsistas.html', {
        'title': 'Cadastro de Bolsistas',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
        'ListaErros': ListaErros,
        'ListaAcertos': ListaAcertos,
    })

@permissao_requerida(item_id='bolsistas')
def ExcluirBolsistas(request):
    bolsistas = alunoscem.objects.select_related('id_pessoa').all()
    if request.method == 'POST':
        check = False
        for aluno in bolsistas:
            if request.POST.get(str(aluno.id)):
                check = True
                try:
                    nome = aluno.id_pessoa.nome
                    aluno.delete()
                    messages.success(request, f'Bolsista {nome} excluído')
                except:
                    messages.error(request, f'Erro ao exluir bolsista {aluno.id_pessoa.nome}')
        if not check:
            messages.error(request, 'Selecione pelo menos 1 aluno para excluir')
        return redirect(r('ExcluirBolsistas'))
    return render(request, 'administracao/admin_conferir_cadastro_bolsistas.html', {
        'title': 'Lista de Bolsistas 100%',
        'itemselec': 'ADMINISTRAÇÃO',
        'bolsistas': bolsistas,
    })

@permissao_requerida(item_id='colaboradores')
def CadastroColaboradores(request):
    ListaErros = []
    ListaAcertos = []
    form = CadastroAlunosColaboradoresForm()
    if request.method == 'POST':
        ListaAlunosAD = GetListaEstudantesAD()
        form = CadastroAlunosColaboradoresForm(data=request.POST)
        if form.is_valid():
            if ListaAlunosAD is False:
                messages.error(request, "Falha ao conectar ao servidor AD. Verifique as configurações.")
            else:
                usuarios = form.cleaned_data['usuarios']
                ListaCPFsDigitados = list(map(str, usuarios.split('\n'))) 
                for cpf in ListaCPFsDigitados:
                    cpf = str(cpf.replace('\r', '').strip())
                    if not cpf: continue
                    if (cpf in ListaAlunosAD):
                        try:
                            alunoobj = ExisteAlunoCadastrado(cpf)
                            if alunoobj:
                                pessoaobj = pessoa.objects.get(usuario=cpf)
                            else:
                                retorno = SalvaAluno(cpf)
                                pessoaobj = retorno['pessoa']
                            
                            colab, created = alunoscolaboradores.objects.get_or_create(id_pessoa=pessoaobj)
                            if created:
                                ListaAcertos.append({'nome': pessoaobj.nome, 'matricula': cpf})
                            else:
                                ListaErros.append({'nome': pessoaobj.nome, 'matricula': cpf, 'erro': 'Já é colaborador.'})
                        except:
                            ListaErros.append({'matricula': cpf, 'erro': f'Erro ao processar (verifique se o aluno existe).'})
                    else:
                        ListaErros.append({'matricula': cpf, 'erro': 'Não é um aluno do IFTO.'})
                    
    return render(request, 'administracao/admin_cadastro_colaboradores.html', {
        'title': 'Cadastro de Colaboradores',
        'itemselec': 'ADMINISTRAÇÃO',
        'form': form,
        'ListaErros': ListaErros,
        'ListaAcertos': ListaAcertos,
    })

@permissao_requerida(item_id='colaboradores')
def ExcluirColaboradores(request):
    colaboradores = alunoscolaboradores.objects.select_related('id_pessoa').all()
    if request.method == 'POST':
        check = False
        for aluno in colaboradores:
            if request.POST.get(str(aluno.id)):
                check = True
                try:
                    nome = aluno.id_pessoa.nome
                    aluno.delete()
                    messages.success(request, f'Colaborador {nome} excluído')
                except:
                    messages.error(request, f'Erro ao exluir colaborador {aluno.id_pessoa.nome}')
        if not check:
            messages.error(request, 'Selecione pelo menos 1 aluno para excluir')
        return redirect(r('ExcluirColaboradores'))
    return render(request, 'administracao/admin_conferir_cadastro_colaboradores.html', {
        'title': 'Lista de Alunos Colaboradores',
        'itemselec': 'ADMINISTRAÇÃO',
        'colaboradores': colaboradores,
    })

def GetListaEstudantesAD():
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

    if retorno is None or isinstance(retorno, str):
        return False
    else:
        for lista in retorno:
            try:
                if lista.get('raw_attributes'):
                    ListaAlunos.append((lista['raw_attributes']['sAMAccountName'][0]).decode('UTF-8'))
            except:
                pass
        return ListaAlunos

@permissao_requerida(item_id='config_pix')
def ConfigPix(request):
    try:
        configobj = config.objects.get(id=1)
    except config.DoesNotExist:
        configobj = config.objects.create(id=1)

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

@permissao_requerida(item_id='cardapio_hub')
def MenuGestaoCardapio(request):
    return render(request, 'administracao/menu_cardapio.html', {
        'title': 'Gestão de Cardápios',
        'itemselec': 'ADMINISTRAÇÃO',
    })

@permissao_requerida(item_id='cardapio_dia')
def GerenciarCardapio(request):
    hoje = datetime.date.today()
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        itens_selecionados = request.POST.getlist('itens')
        if not itens_selecionados:
            messages.warning(request, "Selecione ao menos um item.")
        else:
            itens_str = ", ".join(itens_selecionados)
            CardapioDia.objects.update_or_create(data=hoje, tipo=tipo, defaults={'itens': itens_str})
            tipo_label = "do Almoço" if tipo == 'ALMOCO' else "da Janta"
            messages.success(request, f"Cardápio {tipo_label} salvo!")
            return redirect(r('GerenciarCardapio'))

    cardapios_hoje = CardapioDia.objects.filter(data=hoje)
    cardapio_dict = {c.tipo: c.itens.split(", ") for c in cardapios_hoje}
    food_options = {}
    for cat_key, cat_name in OpcaoAlimento.CATEGORIAS:
        food_options[cat_name] = OpcaoAlimento.objects.filter(categoria=cat_key).values_list('nome', flat=True)

    return render(request, 'administracao/gerenciar_cardapio.html', {
        'title': 'Gerenciar Cardápio',
        'itemselec': 'ADMINISTRAÇÃO',
        'food_options': food_options,
        'cardapio_hoje': cardapio_dict,
        'hoje': hoje,
    })

@permissao_requerida(item_id='opcoes_alimento')
def GerenciarOpcoesAlimento(request):
    if not OpcaoAlimento.objects.exists():
        for cat, itens in FOOD_OPTIONS.items():
            for item in itens:
                OpcaoAlimento.objects.get_or_create(nome=item, categoria=cat)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        if nome and categoria:
            OpcaoAlimento.objects.get_or_create(nome=nome, categoria=categoria)
            messages.success(request, f"Item '{nome}' adicionado.")
        return redirect(r('GerenciarOpcoesAlimento'))

    opcoes = OpcaoAlimento.objects.all()
    categorias = OpcaoAlimento.CATEGORIAS
    return render(request, 'administracao/opcoes_alimento.html', {
        'title': 'Opções de Alimentos',
        'itemselec': 'ADMINISTRAÇÃO',
        'opcoes': opcoes,
        'categorias': categorias,
    })

@permissao_requerida(item_id='opcoes_alimento')
def RemoverOpcaoAlimento(request, id_opcao):
    OpcaoAlimento.objects.filter(pk=id_opcao).delete()
    messages.success(request, "Item removido.")
    return redirect(r('GerenciarOpcoesAlimento'))

@permissao_requerida(item_id='opcoes_alimento')
def ImportarOpcoesJSON(request):
    if request.method == 'POST' and request.FILES.get('arquivo_json'):
        from django.db import transaction
        try:
            dados = json.load(request.FILES['arquivo_json'])
            valid_cats = [c[0] for c in OpcaoAlimento.CATEGORIAS]
            
            with transaction.atomic():
                # Limpar biblioteca atual antes de importar
                OpcaoAlimento.objects.all().delete()
                
                for cat, itens in dados.items():
                    if cat in valid_cats:
                        for item in itens:
                            OpcaoAlimento.objects.create(nome=item, categoria=cat)
            
            messages.success(request, "Biblioteca substituída com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao importar JSON: {str(e)}")
    return redirect(r('GerenciarOpcoesAlimento'))

@permissao_requerida(item_id='opcoes_alimento')
def ExportarOpcoesJSON(request):
    opcoes = OpcaoAlimento.objects.all()
    dados = {}
    for cat_key, cat_name in OpcaoAlimento.CATEGORIAS:
        itens = list(opcoes.filter(categoria=cat_key).values_list('nome', flat=True))
        if itens: dados[cat_key] = itens
    
    from django.http import HttpResponse
    response = HttpResponse(json.dumps(dados, indent=2, ensure_ascii=False), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="opcoes_alimento_{datetime.date.today()}.json"'
    return response

@permissao_requerida(item_id='permissoes')
def GerenciarPermissoes(request):
    from restaurante.administracao.models import MenuPermission
    from restaurante.administracao.forms import MenuPermissionForm
    
    ADMIN_GROUP = 'G_PSO_CGTI_SERVIDORES'
    
    ALL_MENU_ITEMS = [
        {'id': 'menu_home', 'label': 'Home / Início', 'category': 'Principal', 'parent': None},
        {'id': 'user_info', 'label': 'Informações Pessoais (Nome, Foto, Cargo)', 'category': 'Home', 'parent': 'menu_home', 'required': True},
        {'id': 'shortcut_vendas', 'label': 'Atalho: Venda Manual', 'category': 'Home', 'parent': 'menu_home', 'is_shortcut': True},
        {'id': 'shortcut_qr', 'label': 'Atalho: Leitura de QR Code', 'category': 'Home', 'parent': 'menu_home', 'is_shortcut': True},
        {'id': 'shortcut_cardapio', 'label': 'Atalho: Cardápio', 'category': 'Home', 'parent': 'menu_home', 'is_shortcut': True},
        {'id': 'shortcut_relatorios', 'label': 'Atalho: Relatórios', 'category': 'Home', 'parent': 'menu_home', 'is_shortcut': True},

        {'id': 'menu_vendas', 'label': 'Módulo de Vendas', 'category': 'Principal', 'parent': None},
        {'id': 'vendas_manual', 'label': 'Acesso: Venda Manual', 'category': 'Vendas', 'parent': 'menu_vendas'},
        {'id': 'leitura_qr', 'label': 'Acesso: Leitura de QR Code', 'category': 'Vendas', 'parent': 'menu_vendas'},

        {'id': 'menu_relatorios', 'label': 'Módulo de Relatórios', 'category': 'Principal', 'parent': None},
        {'id': 'relatorio_vendas', 'label': 'Relatório de Vendas (Geral)', 'category': 'Relatórios', 'parent': 'menu_relatorios'},
        {'id': 'relatorio_servidores', 'label': 'Relatório de Vendas (Servidores)', 'category': 'Relatórios', 'parent': 'menu_relatorios'},
        {'id': 'custo_aluno_periodo', 'label': 'Custo do Aluno no Período', 'category': 'Relatórios', 'parent': 'menu_relatorios'},

        {'id': 'menu_admin', 'label': 'Módulo de Administração', 'category': 'Principal', 'parent': None},
        {'id': 'horario_vendas', 'label': 'Horário Limite das Vendas', 'category': 'Administração', 'parent': 'menu_admin'},
        {'id': 'bolsistas', 'label': 'Gestão de Bolsistas', 'category': 'Administração', 'parent': 'menu_admin'},
        {'id': 'colaboradores', 'label': 'Gestão de Colaboradores', 'category': 'Administração', 'parent': 'menu_admin'},
        {'id': 'cardapio_hub', 'label': 'Gerenciamento de Cardápios (Hub)', 'category': 'Administração', 'parent': 'menu_admin'},
        
        {'id': 'cardapio_dia', 'label': 'Cardápio do Dia', 'category': 'Cardápio', 'parent': 'cardapio_hub'},
        {'id': 'pratos_precos', 'label': 'Pratos & Preços', 'category': 'Cardápio', 'parent': 'cardapio_hub'},
        {'id': 'adicionais', 'label': 'Adicionais', 'category': 'Cardápio', 'parent': 'cardapio_hub'},
        {'id': 'opcoes_alimento', 'label': 'Opções de Alimentos', 'category': 'Cardápio', 'parent': 'cardapio_hub'},
        
        {'id': 'config_ad', 'label': 'Configuração do AD/LDAP', 'category': 'Administração', 'parent': 'menu_admin'},
        {'id': 'config_pix', 'label': 'Configuração de Pagamento (PIX)', 'category': 'Administração', 'parent': 'menu_admin'},
        {'id': 'permissoes', 'label': 'Gerenciar Permissões', 'category': 'Administração', 'parent': 'menu_admin'},
    ]

    # For legacy references or icons in dashboard
    QUICK_ACCESS_ITEMS = [
        {'id': 'shortcut_vendas', 'label': 'Vendas', 'icon': 'fa-store', 'url_name': 'Venda', 'color': '#065f46'},
        {'id': 'shortcut_qr', 'label': 'QR Code', 'icon': 'fa-qrcode', 'url_name': 'ValidacaoQRCode', 'color': '#6366f1'},
        {'id': 'shortcut_cardapio', 'label': 'Cardápio', 'icon': 'fa-utensils', 'url_name': 'GerenciarCardapio', 'color': '#f59e0b'},
        {'id': 'shortcut_relatorios', 'label': 'Relatórios', 'icon': 'fa-chart-pie', 'url_name': 'Relatorios', 'color': '#6d28d9'},
    ]

    admin_perm, created = MenuPermission.objects.get_or_create(
        ad_group=ADMIN_GROUP,
        defaults={
            'access_type': 'admin',
            'allowed_menus': ','.join([i['id'] for i in ALL_MENU_ITEMS]),
            'quick_access': ','.join([i['id'] for i in QUICK_ACCESS_ITEMS]),
            'default_dashboard': 'funcionario',
            'can_switch_dashboard': True,
            'can_sell': True
        }
    )
    if not created:
        admin_perm.allowed_menus = ','.join([i['id'] for i in ALL_MENU_ITEMS])
        admin_perm.quick_access = ','.join([i['id'] for i in QUICK_ACCESS_ITEMS])
        admin_perm.save()

    permissoes = MenuPermission.objects.all().order_by('access_type')
    form = MenuPermissionForm()
    
    if request.method == 'POST':
        id_perm = request.POST.get('id')
        if 'excluir' in request.POST:
            if id_perm:
                perm_obj = MenuPermission.objects.filter(id=id_perm).first()
                if perm_obj and perm_obj.ad_group == ADMIN_GROUP:
                    messages.error(request, "O grupo de Administradores não pode ser removido.")
                    return redirect(r('GerenciarPermissoes'))
                MenuPermission.objects.filter(id=id_perm).delete()
                messages.success(request, "Permissão removida.")
            return redirect(r('GerenciarPermissoes'))
            
        instance = MenuPermission.objects.filter(id=id_perm).first() if id_perm else None
        
        form = MenuPermissionForm(data=request.POST, instance=instance)
        if form.is_valid():
            new_instance = form.save(commit=False)
            
            # Proteção especial para o grupo de Administradores
            if instance and instance.ad_group == ADMIN_GROUP:
                # Garante que não se pode remover permissões, apenas adicionar
                old_allowed = set(instance.get_allowed_list())
                new_allowed = set(new_instance.allowed_menus.split(','))
                final_allowed = old_allowed.union(new_allowed)
                new_instance.allowed_menus = ','.join(filter(None, final_allowed))
                
                old_quick = set(instance.get_quick_list())
                new_quick = set(new_instance.quick_access.split(','))
                final_quick = old_quick.union(new_quick)
                new_instance.quick_access = ','.join(filter(None, final_quick))

            new_instance.save()
            messages.success(request, "Salvo com sucesso!")
            return redirect(r('GerenciarPermissoes'))

    return render(request, 'administracao/admin_gerenciar_permissoes.html', {
        'title': 'Gerenciar Permissões',
        'itemselec': 'ADMINISTRAÇÃO',
        'permissoes': permissoes,
        'all_menu_items': ALL_MENU_ITEMS,
        'quick_access_items': QUICK_ACCESS_ITEMS,
        'form': form,
        'admin_group_name': ADMIN_GROUP
    })

@permissao_requerida(item_id='permissoes')
def ExportarPermissoesJSON(request):
    from restaurante.administracao.models import MenuPermission
    permissoes = MenuPermission.objects.all()
    dados = []
    
    for p in permissoes:
        dados.append({
            'ad_group': p.ad_group,
            'access_type': p.access_type,
            'allowed_menus': p.allowed_menus,
            'quick_access': p.quick_access,
            'default_dashboard': p.default_dashboard,
            'can_switch_dashboard': p.can_switch_dashboard,
            'can_sell': p.can_sell,
            'group_label': p.group_label,
        })
    
    import json
    from django.http import HttpResponse
    import datetime
    
    response = HttpResponse(json.dumps(dados, indent=2, ensure_ascii=False), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="permissoes_restaurante_{datetime.date.today()}.json"'
    return response

@permissao_requerida(item_id='permissoes')
def ImportarPermissoesJSON(request):
    if request.method == 'POST' and request.FILES.get('arquivo_json'):
        from restaurante.administracao.models import MenuPermission
        import json
        try:
            dados = json.load(request.FILES['arquivo_json'])
            count = 0
            for item in dados:
                MenuPermission.objects.update_or_create(
                    ad_group=item['ad_group'],
                    defaults={
                        'access_type': item['access_type'],
                        'allowed_menus': item['allowed_menus'],
                        'quick_access': item['quick_access'],
                        'default_dashboard': item.get('default_dashboard', 'usuario'),
                        'can_switch_dashboard': item.get('can_switch_dashboard', False),
                        'can_sell': item.get('can_sell', False),
                        'group_label': item.get('group_label', ''),
                    }
                )
                count += 1
            messages.success(request, f"Importação concluída! {count} perfis atualizados.")
        except Exception as e:
            messages.error(request, f"Erro ao importar JSON: {str(e)}")
    return redirect(r('GerenciarPermissoes'))