import csv
import datetime
import os
import platform
import pdfkit

from django.db.models import Sum
from django.shortcuts import render, resolve_url as r, redirect
from django.http import HttpResponse
from django.template import loader, Context
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
        somaalmoco = 0
        somajanta = 0
        somacem = 0
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

        #Fazer as somas do relatório
        for vend in vd:
            if vend.cem: #se for bolsista 100%
                contcem = contcem + 1
                somacem = somacem + vend.valor

            # Pega o horário pra definir o que é janta e o que é almoço
            now = datetime.datetime.now()
            hotariojanta = now.replace(hour=15, minute=0, second=0, microsecond=0)
            # Pega o horário da venda
            data = vend.data

            if (data.time() <= hotariojanta.time()):  # resolvido, verificando se é almoço pelo horário da venda, gratidão, dessa vez é verdade
                contalmoco = contalmoco + 1
                somaalmoco = somaalmoco + vend.valor
            else:
                contjanta = contjanta + 1
                somajanta = somajanta + vend.valor

            soma = soma + vend.valor

        return render(request, 'relatorios/relatoriovendas.html', {
            'soma': soma,
            'datainicial': datainicial,
            'datafinal': datafinal,
            'itemselec': 'RELATÓRIOS',
            'venda': vd,
            'contcem': contcem,
            'valorcem': somacem,
            'contjanta': contjanta,
            'contalmoco': contalmoco,
            'valorjanta': somajanta,
            'valoralmoco': somaalmoco,
            'form': form,
            'title': 'Relatórios',
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
    soma = 0
    somaalmoco = 0
    somajanta = 0
    somacem = 0
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

    for vend in vd:
        if vend.cem:  # se for bolsista 100%
            contcem = contcem + 1
            somacem = somacem + vend.valor

        # Pega o horário pra definir o que é janta e o que é almoço
        now = datetime.datetime.now()
        hotariojanta = now.replace(hour=15, minute=0, second=0, microsecond=0)
        # Pega o horário da venda
        data = vend.data

        if (
                data.time() <= hotariojanta.time()):  # resolvido, verificando se é almoço pelo horário da venda, gratidão, dessa vez é verdade
            contalmoco = contalmoco + 1
            somaalmoco = somaalmoco + vend.valor
        else:
            contjanta = contjanta + 1
            somajanta = somajanta + vend.valor

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
        'valorcem': somacem,
        'contalmoco': contalmoco,
        'valoralmoco': somaalmoco,
        'contjanta': contjanta,
        'valorjanta': somajanta,
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


def CsvVendas(request):
    campo_aluno = request.session.get('aluno-selecionado')
    datainicial = request.session['data-inicial']
    datafinal = request.session['data-final']
    campotipo = request.session['campo_tipo']

    # Cria o objeto HttpResponse com o cabeçalho CSV apropriado.
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="somefilename.csv"'},
    )
    writer = csv.writer(response)
    # Cria cabeçalho do arquivo, 1ª linha
    writer.writerow(["Data", "Aluno", "Matrícula", "Preço"])

    if campotipo == '-1':
        campotipo = ''

    if campo_aluno == '-1':
        vd = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo
        ).order_by('data')
    else:
        vd = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo,
            id_aluno=campo_aluno
        ).order_by('data')

    for vend in vd:
        #Adiciona linha ao arquivo
        writer.writerow([vend.data, vend.id_aluno.id_pessoa, vend.id_aluno.id_pessoa.usuario, str(vend.valor).replace('.', ',')])

    return response