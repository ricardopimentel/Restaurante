import csv
import datetime
import os
import platform
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template

from django.db.models import Sum, Count, Q
from django.shortcuts import render, resolve_url as r, redirect
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from restaurante.core.models import venda, VendaServidor, aluno, servidor, prato
from restaurante.relatorios.forms import RelatorioVendasForm, RelatorioCustoAlunoForm, RelatorioVendasServidorForm
from django.core.cache import cache


from restaurante.acesso.utils import permissao_requerida

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources (like images)
    """
    from django.conf import settings
    import os
    
    # use short variable names
    static_url = settings.STATIC_URL
    static_root = settings.STATIC_ROOT
    media_url = settings.MEDIA_URL
    media_root = settings.MEDIA_ROOT

    # convert URIs to absolute system paths
    if uri.startswith(media_url):
        path = os.path.join(media_root, uri.replace(media_url, ""))
    elif uri.startswith(static_url):
        path = os.path.join(static_root, uri.replace(static_url, ""))
    else:
        return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (static_url, media_url)
        )
    return path

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    # Para o xhtml2pdf encontrar imagens estáticas, passamos o link_callback
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@permissao_requerida(category='RELATÓRIOS')
def Relatorios(request):
    return render(request, 'relatorios/relatorios.html', {
        'title': 'Relatórios',
        'itemselec': 'RELATÓRIOS',
    })


@csrf_exempt
@permissao_requerida(item_id='relatorio_vendas')
def RelatorioVendas(request):
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

    CHOICES = cache.get('lista_alunos_choices')
    if not CHOICES:
        CHOICES = [(-1, 'Todos')]
        alunoobj = aluno.objects.select_related('id_pessoa').all()
        for al in alunoobj:
            CHOICES.append((al.id, str(al.id_pessoa.usuario).title()))
        cache.set('lista_alunos_choices', CHOICES, 3600)  # Cache por 1 hora

    # Pega valores da sessao para jogar no formulario
    form = RelatorioVendasForm(request, CHOICES, initial={
        'campo_data_inicial': request.session.get('data-inicial'),
        'campo_data_final': request.session.get('data-final'),
        'campo_aluno': request.session.get('aluno-selecionado'),
        'campo_tipo': request.session.get('campo_tipo'),
        'agrupar_por_dia': request.session.get('agrupar_por_dia', False)
    })

    if request.method == 'POST':
        form = RelatorioVendasForm(request, CHOICES, request.POST)
        if form.is_valid():
            # Pega valores do POST
            datainicial = request.POST['campo_data_inicial']
            datafinal = request.POST['campo_data_final']
            alunoselecionado = form.cleaned_data['campo_aluno']
            campotipo = form.cleaned_data['campo_tipo']
            agrupar_por_dia = form.cleaned_data['agrupar_por_dia']

            if campotipo == '-1':
                campotipo = ''

            # Pega no bd os dados da vas vendas, filtrando por aluno
            queryset = venda.objects.select_related().filter(
                data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo
            )
            
            if alunoselecionado != '-1':
                queryset = queryset.filter(id_aluno=alunoselecionado)

            if agrupar_por_dia:
                vd = queryset.values('data__date').annotate(
                    dia_soma=Sum('valor'), 
                    dia_qtd=Count('id'),
                    qtd_manual=Count('id', filter=Q(origem='MANUAL')),
                    qtd_ticket=Count('id', filter=Q(origem='TICKET')),
                    qtd_cem=Count('id', filter=Q(cem=True)),
                    v_cem=Sum('valor', filter=Q(cem=True)),
                    qtd_almoco=Count('id', filter=Q(id_prato__descricao='Almoço')),
                    v_almoco=Sum('valor', filter=Q(id_prato__descricao='Almoço')),
                    qtd_janta=Count('id', filter=Q(id_prato__descricao='Janta')),
                    v_janta=Sum('valor', filter=Q(id_prato__descricao='Janta')),
                    # Origem por tipo
                    manual_cem=Count('id', filter=Q(origem='MANUAL', cem=True)),
                    ticket_cem=Count('id', filter=Q(origem='TICKET', cem=True)),
                    manual_almoco=Count('id', filter=Q(origem='MANUAL', id_prato__descricao='Almoço')),
                    ticket_almoco=Count('id', filter=Q(origem='TICKET', id_prato__descricao='Almoço')),
                    manual_janta=Count('id', filter=Q(origem='MANUAL', id_prato__descricao='Janta')),
                    ticket_janta=Count('id', filter=Q(origem='TICKET', id_prato__descricao='Janta'))
                ).order_by('data__date')
            else:
                vd = queryset.order_by('data')

            # Salva valores na sessão p preencher automaticamente posteriormente
            request.session['data-inicial'] = datainicial
            request.session['data-final'] = datafinal
            request.session['aluno-selecionado'] = alunoselecionado
            request.session['campo_tipo'] = campotipo
            request.session['agrupar_por_dia'] = agrupar_por_dia

    cont_manual = 0
    cont_ticket = 0
    m_cem = 0; t_cem = 0
    m_almoco = 0; t_almoco = 0
    m_janta = 0; t_janta = 0
    
    # Fazer as somas do relatório
    if request.session.get('agrupar_por_dia'):
        # Quando agrupado, somamos as agregações diárias para manter os KPIs corretos
        for item in vd:
            soma = soma + (item['dia_soma'] or 0)
            cont_manual = cont_manual + (item['qtd_manual'] or 0)
            cont_ticket = cont_ticket + (item['qtd_ticket'] or 0)
            contcem = contcem + (item['qtd_cem'] or 0)
            somacem = somacem + (item['v_cem'] or 0)
            contalmoco = contalmoco + (item['qtd_almoco'] or 0)
            somaalmoco = somaalmoco + (item['v_almoco'] or 0)
            contjanta = contjanta + (item['qtd_janta'] or 0)
            somajanta = somajanta + (item['v_janta'] or 0)
            # Breakdown origem
            m_cem += (item['manual_cem'] or 0); t_cem += (item['ticket_cem'] or 0)
            m_almoco += (item['manual_almoco'] or 0); t_almoco += (item['ticket_almoco'] or 0)
            m_janta += (item['manual_janta'] or 0); t_janta += (item['ticket_janta'] or 0)
    else:
        for vend in vd:
            is_ticket = (vend.origem == 'TICKET')
            if is_ticket:
                cont_ticket += 1
            else:
                cont_manual += 1

            if vend.cem: #se for bolsista 100%
                contcem += 1
                somacem += vend.valor
                if is_ticket: t_cem += 1
                else: m_cem += 1

            # Contabilizar por tipo de prato (Almoço ou Janta) usando o registro oficial do prato
            desc = vend.id_prato.descricao
            if desc == "Almoço":
                contalmoco += 1
                somaalmoco += vend.valor
                if is_ticket: t_almoco += 1
                else: m_almoco += 1
            elif desc == "Janta":
                contjanta += 1
                somajanta += vend.valor
                if is_ticket: t_janta += 1
                else: m_janta += 1

            soma = soma + vend.valor

    return render(request, 'relatorios/relatoriovendas.html', {
        'soma': soma,
        'cont_manual': cont_manual,
        'cont_ticket': cont_ticket,
        'm_cem': m_cem, 't_cem': t_cem,
        'm_almoco': m_almoco, 't_almoco': t_almoco,
        'm_janta': m_janta, 't_janta': t_janta,
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
@permissao_requerida(item_id='custo_aluno_periodo')
def RelatorioCustoAlunoPeriodo(request):
    soma = 0
    datainicial = ''
    datafinal = ''
    vd = []

    CHOICES = cache.get('lista_alunos_choices')
    if not CHOICES:
        CHOICES = [(-1, 'Todos')]
        alunoobj = aluno.objects.select_related('id_pessoa').all()
        for al in alunoobj:
            CHOICES.append((al.id, str(al.id_pessoa.usuario).title()))
        cache.set('lista_alunos_choices', CHOICES, 3600)

    # Pega valores da sessao para jogar no formulario
    form = RelatorioCustoAlunoForm(request, CHOICES, initial={
        'campo_data_inicial': request.session.get('data-inicial'),
        'campo_data_final': request.session.get('data-final'),
        'campo_aluno': request.session.get('aluno-selecionado'),
    })

    if request.method == 'POST':
        form = RelatorioCustoAlunoForm(request, CHOICES, request.POST)
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



@permissao_requerida(item_id='custo_aluno_periodo')
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

    return render_to_pdf('relatorios/pdfcusto_aluno_periodo.html', contexto)


@permissao_requerida(item_id='relatorio_vendas')
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

    request.session['data-inicial'] = datainicial
    request.session['data-final'] = datafinal
    request.session['campo_tipo'] = campotipo
    request.session['aluno-selecionado'] = campo_aluno
    request.session['agrupar_por_dia'] = request.session.get('agrupar_por_dia', False)

    if campo_aluno == '-1':
        queryset = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo
        )
        alunoobj = ''
    else:
        queryset = venda.objects.select_related().filter(
            data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59'], cem__contains=campotipo,
            id_aluno=campo_aluno
        )
        alunoobj = aluno.objects.get(id=campo_aluno)

    if request.session.get('agrupar_por_dia'):
        vd = queryset.values('data__date').annotate(
            dia_soma=Sum('valor'), 
            dia_qtd=Count('id'),
            qtd_manual=Count('id', filter=Q(origem='MANUAL')),
            qtd_ticket=Count('id', filter=Q(origem='TICKET')),
            qtd_cem=Count('id', filter=Q(cem=True)),
            v_cem=Sum('valor', filter=Q(cem=True)),
            qtd_almoco=Count('id', filter=Q(id_prato__descricao='Almoço')),
            v_almoco=Sum('valor', filter=Q(id_prato__descricao='Almoço')),
            qtd_janta=Count('id', filter=Q(id_prato__descricao='Janta')),
            v_janta=Sum('valor', filter=Q(id_prato__descricao='Janta')),
            manual_cem=Count('id', filter=Q(origem='MANUAL', cem=True)),
            ticket_cem=Count('id', filter=Q(origem='TICKET', cem=True)),
            manual_almoco=Count('id', filter=Q(origem='MANUAL', id_prato__descricao='Almoço')),
            ticket_almoco=Count('id', filter=Q(origem='TICKET', id_prato__descricao='Almoço')),
            manual_janta=Count('id', filter=Q(origem='MANUAL', id_prato__descricao='Janta')),
            ticket_janta=Count('id', filter=Q(origem='TICKET', id_prato__descricao='Janta'))
        ).order_by('data__date')
    else:
        vd = queryset.order_by('data')

    cont_manual = 0
    cont_ticket = 0
    m_cem = 0; t_cem = 0
    m_almoco = 0; t_almoco = 0
    m_janta = 0; t_janta = 0
    
    soma = 0
    for item in vd:
        if request.session.get('agrupar_por_dia'):
            soma = soma + (item['dia_soma'] or 0)
            cont_manual = cont_manual + (item['qtd_manual'] or 0)
            cont_ticket = cont_ticket + (item['qtd_ticket'] or 0)
            contcem = contcem + (item['qtd_cem'] or 0)
            somacem = somacem + (item['v_cem'] or 0)
            contalmoco = contalmoco + (item['qtd_almoco'] or 0)
            somaalmoco = somaalmoco + (item['v_almoco'] or 0)
            contjanta = contjanta + (item['qtd_janta'] or 0)
            somajanta = somajanta + (item['v_janta'] or 0)
            # Origin Breakdown
            m_cem += (item['manual_cem'] or 0); t_cem += (item['ticket_cem'] or 0)
            m_almoco += (item['manual_almoco'] or 0); t_almoco += (item['ticket_almoco'] or 0)
            m_janta += (item['manual_janta'] or 0); t_janta += (item['ticket_janta'] or 0)
        else:
            is_ticket = (item.origem == 'TICKET')
            if is_ticket:
                cont_ticket += 1
            else:
                cont_manual += 1

            if item.cem:  # se for bolsista 100%
                contcem += 1
                somacem += item.valor
                if is_ticket: t_cem += 1
                else: m_cem += 1

            # Contabilizar por tipo de prato (Almoço ou Janta) usando o registro oficial do prato
            desc = item.id_prato.descricao
            if desc == "Almoço":
                contalmoco += 1
                somaalmoco += item.valor
                if is_ticket: t_almoco += 1
                else: m_almoco += 1
            elif desc == "Janta":
                contjanta += 1
                somajanta += item.valor
                if is_ticket: t_janta += 1
                else: m_janta += 1

            soma = soma + item.valor

    # Contexto
    contexto = {
        'title': 'Relatório PDF',
        'pagesize': 'A4',
        'venda': vd,
        'grouped': request.session.get('agrupar_por_dia'),
        'soma': soma,
        'cont_manual': cont_manual,
        'cont_ticket': cont_ticket,
        'm_cem': m_cem, 't_cem': t_cem,
        'm_almoco': m_almoco, 't_almoco': t_almoco,
        'm_janta': m_janta, 't_janta': t_janta,
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

    return render_to_pdf('relatorios/pdfvendas.html', contexto)


@permissao_requerida(item_id='relatorio_vendas')
def CsvVendas(request):
    campo_aluno = request.session.get('aluno-selecionado')
    datainicial = request.session['data-inicial']
    datafinal = request.session['data-final']
    campotipo = request.session['campo_tipo']

    # Cria o objeto HttpResponse com o cabeçalho CSV apropriado.
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="vendas_relatorio.csv"'},
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

@csrf_exempt
@permissao_requerida(item_id='relatorio_servidores')
def RelatorioVendasServidor(request):
    soma = 0
    datainicial = ''
    datafinal = ''
    vd = []

    CHOICES = cache.get('lista_servidores_choices')
    if not CHOICES:
        CHOICES = [(-1, 'Todos')]
        servidor_objs = servidor.objects.select_related('id_pessoa').all()
        for s in servidor_objs:
            CHOICES.append((s.id, str(s.id_pessoa.usuario).title()))
        cache.set('lista_servidores_choices', CHOICES, 3600)

    form = RelatorioVendasServidorForm(request, CHOICES, initial={
        'campo_data_inicial': request.session.get('srv-data-inicial'),
        'campo_data_final': request.session.get('srv-data-final'),
        'campo_servidor': request.session.get('srv-selecionado'),
    })

    if request.method == 'POST':
        form = RelatorioVendasServidorForm(request, CHOICES, request.POST)
        if form.is_valid():
            datainicial = request.POST['campo_data_inicial']
            datafinal = request.POST['campo_data_final']
            servidor_selecionado = form.cleaned_data['campo_servidor']

            queryset = VendaServidor.objects.select_related().filter(
                data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59']
            )
            
            if servidor_selecionado != '-1':
                queryset = queryset.filter(id_servidor=servidor_selecionado)

            vd = queryset.order_by('data')

            request.session['srv-data-inicial'] = datainicial
            request.session['srv-data-final'] = datafinal
            request.session['srv-selecionado'] = servidor_selecionado

    for vend in vd:
        soma += vend.valor_pago

    return render(request, 'relatorios/relatorio_vendas_servidor.html', {
        'soma': soma,
        'datainicial': datainicial,
        'datafinal': datafinal,
        'itemselec': 'RELATÓRIOS',
        'venda': vd,
        'form': form,
        'title': 'Relatórios Servidores',
    })

@permissao_requerida(item_id='relatorio_servidores')
def PdfVendasServidor(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    servidor_id = request.session.get('srv-selecionado')
    datainicial = request.session.get('srv-data-inicial')
    datafinal = request.session.get('srv-data-final')
    soma = 0

    queryset = VendaServidor.objects.select_related().filter(
        data__range=[datainicial + ' 00:00:00', datafinal + ' 23:59:59']
    )
    
    servidor_obj = None
    if servidor_id and servidor_id != '-1':
        queryset = queryset.filter(id_servidor=servidor_id)
        servidor_obj = servidor.objects.get(id=servidor_id)

    vd = queryset.order_by('data')
    for item in vd:
        soma += item.valor_pago

    contexto = {
        'title': 'Relatório Servidores PDF',
        'pagesize': 'A4',
        'venda': vd,
        'soma': soma,
        'datainicial': datainicial,
        'datafinal': datafinal,
        'servidor': servidor_obj,
        'base_dir': BASE_DIR,
    }

    return render_to_pdf('relatorios/pdf_vendas_servidor.html', contexto)


    return response