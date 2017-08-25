import os
import platform
import pdfkit

from django.http import HttpResponse
from django.shortcuts import render, resolve_url as r, redirect

# Create your views here.
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt


from restaurante.core.models import aluno, venda
from restaurante.relatorios.forms import RelatorioVendasForm


def Relatorios(request):
    if dict(request.session).get('nome'):
        return render(request, 'relatorios/relatorios.html')
    return redirect(r('Login'))


@csrf_exempt
def RelatorioVendas(request):
    if dict(request.session).get('nome'):# Verificar se usuário está logado
        soma = 0
        datainicial = ''
        datafinal = ''
        vd = []

        # Pega valores da sessao para jogar no formulario
        form = RelatorioVendasForm(request, initial={
            'campo_data_inicial': request.session.get('data-inicial'),
            'campo_data_final': request.session.get('data-final'),
            'campo_aluno': request.session.get('aluno-selecionado')
        })

        if request.method == 'POST':
            form = RelatorioVendasForm(request, request.POST)
            if form.is_valid():
                # Pega valores do POST
                datainicial = request.POST['campo_data_inicial']
                datafinal = request.POST['campo_data_final']
                alunoselecionado = form.cleaned_data['campo_aluno']
                # Pega no bd os dados da vas vendas, filtrando por aluno
                if alunoselecionado == '-1':
                    vd = venda.objects.select_related().filter(
                        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59']
                    )
                else:
                    vd = venda.objects.select_related().filter(
                        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'],
                        id_aluno=alunoselecionado
                    )
                # Salva valores na sessão p preencher automaticamente posteriormente
                request.session['data-inicial'] = datainicial
                request.session['data-final'] = datafinal
                request.session['aluno-selecionado'] = alunoselecionado

        # Somar valor das vendas no periodo
        for vend in vd:
            soma = soma + vend.valor

        return render(request, 'relatorios/relatoriovendas.html', {
            'soma': soma, 'datainicial': datainicial, 'datafinal': datafinal,
            'itemselec': 'HOME', 'venda': vd, 'form': form,
        })


def PdfVendas(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    campo_aluno = request.session.get('aluno-selecionado')
    datainicial = request.session['data-inicial']
    datafinal = request.session['data-final']
    soma = 0

    if campo_aluno == '-1':
        vd = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59']
        )
        alunoobj = ''
    else:
        vd = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'],
            id_aluno=campo_aluno
        )
        alunoobj = aluno.objects.get(id=campo_aluno)

    # Somar valor das vendas no periodo
    for vend in vd:
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
    }

    html = template.render(contexto)

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
        'margin-bottom': 16,
    }

    # Use False instead of output path to save pdf to a variable
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)
    response = HttpResponse(pdf, content_type='application/pdf')

    return response