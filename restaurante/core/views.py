from django.shortcuts import render, redirect, resolve_url as r


# Create your views here.
from django.template import RequestContext


def Home(request):
    try:# Verificar se usuario esta logado
        if request.session['nome']:
            context = {'err': '', 'itemselec': 'HOME'}
            
            if request.session.get('usertip') == 'aluno':
                try:
                    from restaurante.core.models import aluno, pessoa, alunoscem
                    from restaurante.ticket_estudante.models import TicketAluno
                    from restaurante.venda.views import ExistePratoCadastrado

                    pessoa_obj = pessoa.objects.get(usuario=request.session['userl'])
                    aluno_obj = aluno.objects.get(id_pessoa=pessoa_obj)
                    
                    # Prato Ativo Atualmente
                    prato_obj_ativo = ExistePratoCadastrado(request.session['userl'])
                    if prato_obj_ativo:
                        context['prato_info'] = {
                            'status': True,
                            'descricao': prato_obj_ativo.descricao,
                            'preco': prato_obj_ativo.preco_aluno
                        }
                    else:
                        context['prato_info'] = {
                            'status': False,
                            'erro': 'Atendimento encerrado ou sem pratos cadastrados para este horário.'
                        }
                    
                    # Contagem de Tickets Não Utilizados (Apenas os Pagos)
                    tickets_ativos_qs = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=False, pago=True).order_by('-data_compra')
                    context['tickets_ativos'] = tickets_ativos_qs.count()
                    if context['tickets_ativos'] > 0:
                        context['primeiro_ticket_uuid'] = tickets_ativos_qs.first().uuid
                    
                    # Histórico Recente de Tickets Usados (usa data_utilizacao se houver, senao data_compra)
                    historico = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=True).order_by('-data_utilizacao', '-data_compra')[:3]
                    context['historico'] = historico
                    
                    # Categoria / Bolsista
                    from restaurante.core.models import alunoscolaboradores
                    is_cem = alunoscem.objects.filter(id_pessoa=pessoa_obj).exists()
                    is_colab = alunoscolaboradores.objects.filter(id_pessoa=pessoa_obj).exists()
                    
                    if is_cem: context['categoria'] = 'Bolsista CEM (Gratuidade)'
                    elif is_colab: context['categoria'] = 'Aluno Colaborador'
                    else: context['categoria'] = 'Estudante Regular'
                    
                    # --- RESUMO FINANCEIRO ---
                    from django.db.models import Sum
                    from django.utils import timezone
                    from datetime import timedelta

                    periodo = request.GET.get('periodo', '30')
                    hoje = timezone.now()
                    
                    if periodo == '60':
                        dias = 60
                        context['periodo_texto'] = '60 dias'
                    elif periodo == '365':
                        dias = 365
                        context['periodo_texto'] = '1 ano'
                    elif periodo == 'tudo':
                        dias = 9999
                        context['periodo_texto'] = 'todo o período'
                    else:
                        dias = 30
                        context['periodo_texto'] = '30 dias'
                        periodo = '30'

                    data_limite = hoje - timedelta(days=dias)
                    context['periodo_selecionado'] = periodo

                    # Query de soma
                    resumo_qs = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=True)
                    if periodo != 'tudo':
                        resumo_qs = resumo_qs.filter(data_utilizacao__gte=data_limite)

                    sum_almoco = resumo_qs.filter(tipo_refeicao__icontains='Almoço').aggregate(total=Sum('valor'))['total'] or 0.0
                    sum_janta = resumo_qs.filter(tipo_refeicao__icontains='Janta').aggregate(total=Sum('valor'))['total'] or 0.0
                    
                    # Caso a correção de nomes (acentos) não tenha pegado em registros manuais antigos:
                    if sum_almoco == 0:
                        sum_almoco = resumo_qs.filter(tipo_refeicao__icontains='Almoco').aggregate(total=Sum('valor'))['total'] or 0.0

                    context['total_almoco'] = sum_almoco
                    context['total_janta'] = sum_janta
                    # ------------------------

                except Exception as e:
                    import sys
                    print("Erro ao carregar dashboard de aluno:", e, sys.exc_info())
                    
            elif request.session.get('usertip') in ['admin', 'lanchonete', 'glanchonete']:
                try:
                    from restaurante.core.models import venda
                    from restaurante.ticket_estudante.models import TicketAluno
                    from django.utils import timezone
                    
                    hoje = timezone.now().date()
                    
                    # Vendas Diretas Hoje
                    context['vendas_hoje'] = venda.objects.filter(data__date=hoje).count()
                    
                    # Tickets Validados Hoje
                    context['validacoes_hoje'] = TicketAluno.objects.filter(usado=True, data_utilizacao__date=hoje).count()
                    
                except Exception as e:
                    print("Erro ao carregar stats de funcionário:", e)
                    
            return render(request, 'index.html', context)

    except KeyError:
        return redirect(r('Login'))