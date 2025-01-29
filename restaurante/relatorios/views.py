import os
import platform
from datetime import datetime

import pdfkit

from django import forms
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, resolve_url as r, redirect

# Create your views here.
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt


from restaurante.core.models import venda, aluno, prato
from restaurante.relatorios.forms import RelatorioVendasForm


def Relatorios(request):
    if dict(request.session).get('nome'):
        return render(request, 'relatorios/relatorios.html', {
            'title': 'Relatórios',
            'itemselec': 'RELATÓRIOS',
        })
    return redirect(r('Login'))


@csrf_exempt
def RelatorioVendas(request):
    if dict(request.session).get('nome'):# Verificar se usuário está logado
        soma = 0
        contcem = 0
        contalmoco = 0
        contjanta = 0
        datainicial = ''
        datafinal = ''
        vd = []

        CHOICES = [(-1, 'Todos')]
        alunoobj = aluno.objects.all()
        for al in alunoobj:
            CHOICES.append((al.id, str(al.id_pessoa.usuario).title()))

        # Pega valores da sessao para jogar no formulario
        form = RelatorioVendasForm(request, CHOICES, initial={
            'campo_data_inicial': request.session.get('data-inicial'),
            'campo_data_final': request.session.get('data-final'),
            'campo_aluno': request.session.get('aluno-selecionado'),
            'campotipo': request.session.get('campo_tipo')
        })

        if request.method == 'POST':
            form = RelatorioVendasForm(request, CHOICES, request.POST)
            if form.is_valid():
                # Pega valores do POST
                datainicial = request.POST['campo_data_inicial']
                datafinal = request.POST['campo_data_final']
                alunoselecionado = form.cleaned_data['campo_aluno']
                campotipo = form.cleaned_data['campo_tipo']

                if campotipo == '-1':
                    campotipo = ''


                # Pega no bd os dados da vas vendas, filtrando por aluno
                if alunoselecionado == '-1':
                    vd = venda.objects.select_related().filter(
                        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo
                    ).order_by('data')
                else:
                    vd = venda.objects.select_related().filter(
                        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo,
                        id_aluno=alunoselecionado
                    ).order_by('data')
                # Salva valores na sessão p preencher automaticamente posteriormente
                request.session['data-inicial'] = datainicial
                request.session['data-final'] = datafinal
                request.session['aluno-selecionado'] = alunoselecionado
                request.session['campo_tipo'] = campotipo

        # Somar valor das vendas no periodo
        almoco = prato.objects.get(descricao='Almoço')
        janta = prato.objects.get(descricao='Janta')
        cem = prato.objects.get(descricao='Cem')
        for vend in vd:
            if vend.cem: #se for bolsista 100%
                contcem = contcem + 1
            else:
                if (vend.id_prato == almoco):  # resolvido, verificando se é almoço pelo horário da venda, gratidão
                    contalmoco = contalmoco + 1
                else:
                    contjanta = contjanta + 1
            soma = soma + vend.valor

        return render(request, 'relatorios/relatoriovendas.html', {
            'soma': soma, 'datainicial': datainicial, 'datafinal': datafinal,
            'itemselec': 'RELATÓRIOS', 'venda': vd, 'contcem': contcem, 'valorcem': (contcem*(cem.preco)), 'contjanta': contjanta, 'contalmoco': contalmoco, 'valorjanta': (contjanta*janta.preco), 'valoralmoco': (contalmoco*almoco.preco), 'form': form, 'title': 'Relatórios',
        })


@csrf_exempt
def RelatorioCustoAlunoPeriodo(request):
    if dict(request.session).get('nome'):# Verificar se usuário está logado
        soma = 0
        datainicial = ''
        datafinal = ''
        vd = []

        CHOICES = [(-1, 'Todos')]
        alunoobj = aluno.objects.all()
        for al in alunoobj:
            CHOICES.append((al.id, str(al.id_pessoa.usuario).title()))

        # Pega valores da sessao para jogar no formulario
        form = RelatorioVendasForm(request, CHOICES, initial={
            'campo_data_inicial': request.session.get('data-inicial'),
            'campo_data_final': request.session.get('data-final'),
            'campo_aluno': request.session.get('aluno-selecionado'),
        })

        if request.method == 'POST':
            form = RelatorioVendasForm(request, CHOICES, request.POST)
            if form.is_valid():
                # Pega valores do POST
                datainicial = request.POST['campo_data_inicial']
                datafinal = request.POST['campo_data_final']
                alunoselecionado = form.cleaned_data['campo_aluno']
                # Pega no bd os dados da vas vendas, filtrando por aluno
                #objects.values('host').annotate(soma=Sum('pages')).order_by('-soma')
                if alunoselecionado == '-1':
                    vd = venda.objects.select_related().values('id_aluno__id_pessoa__nome', 'id_aluno__id_pessoa__usuario').annotate(soma=Sum('valor')).filter(
                        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59']
                    )
                else:
                    vd = venda.objects.select_related().values('id_aluno__id_pessoa__nome', 'id_aluno__id_pessoa__usuario').annotate(soma=Sum('valor')).filter(
                        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'],
                        id_aluno=alunoselecionado
                    )
                # Salva valores na sessão p preencher automaticamente posteriormente
                request.session['data-inicial'] = datainicial
                request.session['data-final'] = datafinal
                request.session['aluno-selecionado'] = alunoselecionado

        # Somar valor das vendas no periodo
        for vend in vd:
            soma = soma + vend['soma']

        return render(request, 'relatorios/relatorio_custo_aluno_periodo.html', {
            'soma': soma, 'datainicial': datainicial, 'datafinal': datafinal,
            'itemselec': 'RELATÓRIOS', 'venda': vd, 'form': form, 'title': 'Relatórios',
        })



def PdfCustoAlunoPeriodo(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    campo_aluno = request.session.get('aluno-selecionado')
    datainicial = request.session['data-inicial']
    datafinal = request.session['data-final']
    soma = 0

    if campo_aluno == '-1':
        vd = venda.objects.select_related().values('id_aluno__id_pessoa__nome', 'id_aluno__id_pessoa__usuario').annotate(soma=Sum('valor')).filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59']
        )
        alunoobj = ''
    else:
        vd = venda.objects.select_related().values('id_aluno__id_pessoa__nome', 'id_aluno__id_pessoa__usuario').annotate(soma=Sum('valor')).filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'],
            id_aluno=campo_aluno
        )
        alunoobj = aluno.objects.get(id=campo_aluno)

    # Somar valor das vendas no periodo
    for vend in vd:
        soma = soma + vend['soma']

    # Template
    template = get_template('relatorios/pdfcusto_aluno_periodo.html')

    # Contexto
    contexto = {
        'title': 'Relatório PDF',
        'pagesize': 'A4',
        'venda': vd,
        'soma': soma,
        'datainicial': datainicial,
        'datafinal': datafinal,
        'aluno': alunoobj,
        'base_dir': BASE_DIR,
    }

    html = template.render(contexto)

    # Verificar se o sistema é windows
    if platform.system() == 'Windows':
        path_wkthmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    else:
        path_wkthmltopdf = '/app/storage/wkhtmltopdf/wkhtmltopdf'

    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)

    options = {
        'encoding': 'utf-8',
        'footer-left': 'IFTO - Campus de Paraiso do Tocantins [date]',
        'footer-right': 'Pag. [page] de [topage]',
        'margin-bottom': 16,
    }

    # Use False instead of output path to save pdf to a variable
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)
    response = HttpResponse(pdf, content_type='application/pdf')

    return response


def PdfVendas(request):
    contcem = 0
    contalmoco = 0
    contjanta = 0
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    campo_aluno = request.session.get('aluno-selecionado')
    datainicial = request.session['data-inicial']
    datafinal = request.session['data-final']
    campotipo = request.session['campo_tipo']

    if campotipo == '-1':
        campotipo = ''

    soma = 0

    if campo_aluno == '-1':
        vd = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo
        ).order_by('data')
        alunoobj = ''
    else:
        vd = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo,
            id_aluno=campo_aluno
        ).order_by('data')
        alunoobj = aluno.objects.get(id=campo_aluno)

    # Somar valor das vendas no periodo
    almoco = prato.objects.get(descricao='Almoço')
    janta = prato.objects.get(descricao='Janta')
    cem = prato.objects.get(descricao='Cem')
    for vend in vd:
        if vend.cem:  # se for bolsista 100%
            contcem = contcem + 1
        else:
            if (vend.id_prato == almoco):  # resolvido, verificando se é almoço pelo tipo de prato, gratidão
                contalmoco = contalmoco + 1
            else:
                contjanta = contjanta + 1
        soma = soma + vend.valor

    # Template
    template = get_template('relatorios/pdfvendas.html')

    # Contexto
    contexto = {
        'title': 'Relatório PDF',
        'pagesize': 'A4',
        'venda': vd,
        'soma': soma,
        'datainicial': datainicial,
        'datafinal': datafinal,
        'aluno': alunoobj,
        'base_dir': BASE_DIR,
        'contcem': contcem,
        'valorcem': (contcem * cem.preco),
        'contalmoco': contalmoco,
        'valoralmoco': (contalmoco * almoco.preco),
        'contjanta': contjanta,
        'valorjanta': (contjanta * janta.preco),
    }

    html = template.render(contexto)

    # Verificar se o sistema é windows
    if platform.system() == 'Windows':
        path_wkthmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    else:
        path_wkthmltopdf = '/app/storage/wkhtmltopdf/wkhtmltopdf'

    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)

    options = {
        'encoding': 'utf-8',
        'footer-left': 'IFTO - Campus de Paraiso do Tocantins [date]',
        'footer-right': 'Pag. [page] de [topage]',
        'margin-bottom': 16,
    }

    # Use False instead of output path to save pdf to a variable
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)
    response = HttpResponse(pdf, content_type='application/pdf')

    return response