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
                    # Tenta buscar aluno, se não existir, cria ou ignora gracefuly
                    aluno_obj = aluno.objects.filter(id_pessoa=pessoa_obj).first()
                    
                    if aluno_obj:
                        # --- 1. PRATO ATIVO ---
                        try:
                            from restaurante.venda.views import ExistePratoCadastrado
                            prato_obj_ativo = ExistePratoCadastrado(request.session['userl'])
                            if prato_obj_ativo:
                                context['prato_info'] = {'status': True, 'descricao': prato_obj_ativo.descricao, 'preco': prato_obj_ativo.preco_aluno}
                            else:
                                context['prato_info'] = {'status': False, 'erro': 'Atendimento encerrado ou sem pratos cadastrados para este horário.'}
                        except Exception as e:
                            context['prato_info'] = {'status': False, 'erro': 'Não foi possível consultar as refeições agora.'}

                        # --- 2. CARTEIRA (TICKETS) ---
                        try:
                            tickets_ativos_qs = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=False, pago=True).order_by('-data_compra')
                            context['tickets_ativos'] = tickets_ativos_qs.count()
                            if context['tickets_ativos'] > 0:
                                context['primeiro_ticket_uuid'] = tickets_ativos_qs.first().uuid
                        except:
                            context['tickets_ativos'] = 0

                        # --- 3. HISTÓRICO RECENTE ---
                        try:
                            from restaurante.ticket_estudante.models import TicketAluno
                            historico = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=True).order_by('-data_utilizacao', '-data_compra')[:3]
                            context['historico'] = historico
                        except:
                            context['historico'] = []

                        # --- 4. CATEGORIA ---
                        try:
                            from restaurante.core.models import alunoscem, alunoscolaboradores
                            is_cem = alunoscem.objects.filter(id_pessoa=pessoa_obj).exists()
                            is_colab = alunoscolaboradores.objects.filter(id_pessoa=pessoa_obj).exists()
                            if is_cem: context['categoria'] = 'Bolsista CEM (Gratuidade)'
                            elif is_colab: context['categoria'] = 'Aluno Colaborador'
                            else: context['categoria'] = 'Estudante Regular'
                            context['is_cem'] = is_cem
                        except:
                            context['categoria'] = 'Estudante Regular'

                        # --- 5. RESUMO FINANCEIRO ---
                        try:
                            from django.db.models import Sum
                            from django.utils import timezone
                            from datetime import timedelta

                            periodo = request.GET.get('periodo', '30')
                            hoje = timezone.now()
                            
                            if periodo == '60': dias = 60; context['periodo_texto'] = '60 dias'
                            elif periodo == '365': dias = 365; context['periodo_texto'] = '1 ano'
                            elif periodo == 'tudo': dias = 9999; context['periodo_texto'] = 'todo o período'
                            else: dias = 30; context['periodo_texto'] = '30 dias'; periodo = '30'

                            data_limite = hoje - timedelta(days=dias)
                            context['periodo_selecionado'] = periodo

                            # Filtra por tickets USADOS (consumo) no período
                            resumo_qs = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=True)
                            if periodo != 'tudo':
                                # Fallback para data_compra caso data_utilizacao seja nula (registros antigos)
                                from django.db.models import Q
                                resumo_qs = resumo_qs.filter(
                                    Q(data_utilizacao__gte=data_limite) | 
                                    Q(data_utilizacao__isnull=True, data_compra__gte=data_limite)
                                )

                            sum_almoco = resumo_qs.filter(tipo_refeicao__icontains='Almoço').aggregate(total=Sum('valor'))['total'] or 0.0
                            sum_janta = resumo_qs.filter(tipo_refeicao__icontains='Janta').aggregate(total=Sum('valor'))['total'] or 0.0
                            
                            if sum_almoco == 0:
                                sum_almoco = resumo_qs.filter(tipo_refeicao__icontains='Almoco').aggregate(total=Sum('valor'))['total'] or 0.0

                            context['total_almoco'] = sum_almoco
                            context['total_janta'] = sum_janta
                        except:
                            context['total_almoco'] = 0.0
                            context['total_janta'] = 0.0
                            context['periodo_texto'] = 'indisponível'
                    
                except Exception as e:
                    import sys
                    print("Erro crítico no dashboard de aluno:", e, sys.exc_info())
                    
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
            
            # --- CARDÁPIO DO DIA (PARA TODOS) ---
            try:
                from restaurante.core.models import CardapioDia
                import datetime
                agora = datetime.datetime.now()
                hoje = agora.date()
                hora = agora.hour
                
                # Se for antes das 14h, foca no Almoço, senão na Janta
                tipo_atual = 'ALMOCO' if hora < 14 else 'JANTA'
                
                cardapio_obj = CardapioDia.objects.filter(data=hoje, tipo=tipo_atual).first()
                if not cardapio_obj:
                    # Se não achou o do momento, tenta o outro (ex: as 15h se não tiver janta, mostra o almoço que teve)
                    cardapio_obj = CardapioDia.objects.filter(data=hoje).order_by('-tipo').first()
                
                if cardapio_obj:
                    context['cardapio_dia'] = {
                        'tipo': cardapio_obj.get_tipo_display(),
                        'itens': cardapio_obj.itens.split(", "),
                        'hora_ref': tipo_atual
                    }
            except:
                pass
            # -------------------------------------

            return render(request, 'index.html', context)

    except KeyError:
        return redirect(r('Login'))