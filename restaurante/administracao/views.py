import sys
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, resolve_url as r


# Create your views here.
from restaurante.administracao.forms import AdForm, CadastroPratoForm, ConfigHorarioLimiteVendasForm
from restaurante.administracao.models import config
from restaurante.core.models import prato


def Administracao(request):
    if dict(request.session).get('nome'):
        return render(request, 'administracao/administracao.html', {
            'title': 'Administração',
            'itemselec': 'ADMINISTRAÇÃO',
        })
    return redirect(r('Login'))


def Dados_ad(request):
    if dict(request.session).get('usertip') == 'admin':
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


def ExcluirPratos(request):
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


def EditarPrato(request, id_prato):
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


def HorarioLimiteVendas(request):
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