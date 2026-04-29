import mercadopago
import json
from django.shortcuts import render, redirect, resolve_url as r
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decouple import config
from restaurante.administracao.models import config as config_model
from restaurante.core.models import prato, alunoscem, aluno, servidor, Adicional
from restaurante.ticket_estudante.models import TicketAluno, TicketServidor

def get_config():
    """ Busca as configurações do sistema no banco de dados """
    try:
        return config_model.objects.get(id=1)
    except config_model.DoesNotExist:
        return None

def get_sdk():
    """ Inicializa o SDK do Mercado Pago com a chave do banco ou do .env """
    conf = get_config()
    token = getattr(conf, 'mp_access_token', None) or config('MP_ACCESS_TOKEN', default='YOUR_ACCESS_TOKEN_HERE')
    return mercadopago.SDK(token)

def get_user_profile(request):
    """ Identifica se o usuário logado é Aluno ou Servidor baseado no cadastro no banco de dados """
    userl = request.session.get('userl')
    if not userl:
        return None, None, "Usuário não logado"
    
    from restaurante.core.models import servidor, aluno, pessoa
    try:
        p = pessoa.objects.get(usuario=userl)
    except pessoa.DoesNotExist:
        return None, None, "Cadastro básico não encontrado"

    usertip = request.session.get('usertip')
    access_types = request.session.get('access_types', [])

    # 1. Prioridade para Servidor
    if usertip == 'servidor' or (usertip == 'admin' and 'servidor' in access_types):
        srv, created = servidor.objects.get_or_create(id_pessoa=p, defaults={'status': True})
        if not created and not srv.status:
            srv.status = True
            srv.save()
        return srv, 'servidor', None
        
    # 2. Se a sessão diz que é aluno
    if usertip == 'aluno':
        aln, created = aluno.objects.get_or_create(id_pessoa=p)
        return aln, 'aluno', None

    # 3. Fallback: Tenta qualquer perfil disponível (priorizando servidor)
    srv = servidor.objects.filter(id_pessoa=p).first()
    if srv: 
        if not srv.status: 
            srv.status = True
            srv.save()
        return srv, 'servidor', None
    
    aln, created = aluno.objects.get_or_create(id_pessoa=p)
    return aln, 'aluno', None

def get_ticket_model(user_type):
    return TicketServidor if user_type == 'servidor' else TicketAluno

def HomeEstudante(request):
    user_obj, user_type, error = get_user_profile(request)
    if not user_obj:
        return redirect('Login')
    return redirect('Home')

def TicketsEstudante(request):
    user_obj, user_type, error = get_user_profile(request)
    if not user_obj: return redirect('Login')
    
    TicketModel = get_ticket_model(user_type)
    filter_key = 'id_servidor' if user_type == 'servidor' else 'id_aluno'
    
    from django.utils import timezone
    from datetime import timedelta
    limite_pendentes = timezone.now() - timedelta(hours=24)
    
    # Tickets Pagos
    tickets_pagos = TicketModel.objects.filter(**{filter_key: user_obj}, usado=False, pago=True).order_by('-data_compra')
    
    # Tickets Pendentes (últimas 24h)
    tickets_pendentes = TicketModel.objects.filter(
        **{filter_key: user_obj}, 
        pago=False, 
        data_compra__gte=limite_pendentes
    ).order_by('-data_compra')

    # Tickets Validados recentemente (últimos 40 minutos)
    limite_recentes = timezone.now() - timedelta(minutes=40)
    tickets_recentes = TicketModel.objects.filter(
        **{filter_key: user_obj}, 
        usado=True, 
        data_utilizacao__gte=limite_recentes
    ).order_by('-data_utilizacao')

    # Adiciona tempo de expiração para o frontend
    for t in tickets_recentes:
        t.expira_em = (t.data_utilizacao + timedelta(minutes=40)).isoformat()
    
    return render(request, 'ticket_estudante/tickets.html', {
        'title': 'Meus Tickets', 
        'itemselec': 'TICKETS', 
        'tickets': tickets_pagos,
        'pendentes': tickets_pendentes,
        'recentes': tickets_recentes
    })

def ComprarTicket(request):
    user_obj, user_type, error = get_user_profile(request)
    if not user_obj: return redirect('Login')
    
    from restaurante.venda.views import ExistePratoCadastrado
    prato_ativo = ExistePratoCadastrado(user_obj.id_pessoa.usuario)
    
    if not prato_ativo:
        return render(request, 'ticket_estudante/comprar.html', {
            'erro': 'Nenhum prato disponível ou atendimento encerrado.',
            'itemselec': 'COMPRAR'
        })
    
    is_cem = False
    if user_type == 'aluno':
        from restaurante.core.models import alunoscem
        is_cem = alunoscem.objects.filter(id_pessoa=user_obj.id_pessoa).exists()
    
    # Define o preço base de acordo com o tipo de usuário e o prato ativo
    if user_type == 'servidor':
        preco_base = prato_ativo.preco_servidor
    else:
        preco_base = 0.0 if is_cem else prato_ativo.preco_aluno

    # Para compatibilidade com o template que espera almoco/janta:
    # Se o nome não ajudar, assumimos Almoço se for antes das 15h, senão Janta
    hora = timezone.now().hour
    is_almoco_time = 'Almoço' in prato_ativo.descricao or ('Janta' not in prato_ativo.descricao and hora <= 14)
    
    context = {
        'title': 'Comprar Ticket',
        'itemselec': 'COMPRAR',
        'prato': prato_ativo,
        'almoco': prato_ativo if is_almoco_time else None,
        'janta': prato_ativo if not is_almoco_time else None,
        'is_cem': is_cem,
        'user_type': user_type,
        'adicionais': Adicional.objects.filter(status=True),
        'pix_fee': getattr(get_config(), 'pix_fee', 0.0),
        'pix_test_mode': getattr(get_config(), 'pix_test_mode', False),
        'preco_almoco': preco_base if is_almoco_time else 0.0,
        'preco_janta': preco_base if not is_almoco_time else 0.0,
        'preco_base': preco_base,
    }

    return render(request, 'ticket_estudante/comprar.html', context)

@csrf_exempt
def SimularPagamento(request):
    """
    Agora renomeado logicamente para ProcessarPagamento. 
    Lida com a criação do PIX real via Mercado Pago.
    """
    user_obj, user_type, error = get_user_profile(request)
    if not user_obj: 
        return JsonResponse({'error': 'Não autorizado', 'detail': error}, status=401)
    
    TicketModel = get_ticket_model(user_type)
    filter_key = 'id_servidor' if user_type == 'servidor' else 'id_aluno'

    if request.method == 'POST':
        tipo = request.POST.get('tipo_refeicao', 'Almoço')
        prato_selecionado = prato.objects.filter(descricao=tipo).first()
        
        try:
            quantidade = int(request.POST.get('quantidade', 1))
        except ValueError:
            quantidade = 1
        if quantidade < 1: quantidade = 1
        if quantidade > 20: quantidade = 20

        if not prato_selecionado:
            return JsonResponse({'error': 'Prato não encontrado'}, status=404)

        is_cem = False
        if user_type == 'aluno':
            is_cem = alunoscem.objects.filter(id_pessoa=user_obj.id_pessoa).exists()
            valor = 0.0 if is_cem else prato_selecionado.preco_aluno
        else:
            valor = prato_selecionado.preco_servidor
        
        # Processar Adicionais (Apenas Servidores podem comprar adicionais)
        adicionais_post = request.POST.get('adicionais_json', '[]')
        if user_type != 'servidor':
            adicionais_post = '[]'
        
        adicionais_lista = json.loads(adicionais_post)
        valor_unitario_adicionais = 0.0
        for item in adicionais_lista:
            try:
                obj = Adicional.objects.get(id=item['id'])
                valor_unitario_adicionais += float(obj.valor) * int(item['qtd'])
            except: pass

        # BUSCA TAXA PIX (%)
        conf = get_config()
        pix_fee_percent = float(getattr(conf, 'pix_fee', 0.0))
        
        # Valor total = (Prato + Adicionais) * Quantidade
        valor_total_sem_taxa = (valor + valor_unitario_adicionais) * quantidade
        valor_total_taxa = float(valor_total_sem_taxa) * (pix_fee_percent / 100) if valor_total_sem_taxa > 0 else 0.0
        valor_com_taxa = valor_total_sem_taxa + valor_total_taxa
        valor_unitario_taxa = valor_total_taxa / quantidade

        # SE FOR CEM, CRIA OS N TICKETS JÁ PAGOS E RETORNA SUCESSO DIRETO
        if is_cem or valor_total_sem_taxa <= 0:
            for _ in range(quantidade):
                TicketModel.objects.create(
                    **{filter_key: user_obj}, 
                    valor=0.0, 
                    valor_adicionais=0.0,
                    tipo_refeicao=tipo,
                    pago=True,
                    data_pagamento=timezone.now()
                )
            return JsonResponse({'status': 'approved', 'redirect': r('TicketsEstudante')})

        # MODO TESTE PIX
        pix_test_mode = getattr(conf, 'pix_test_mode', False)
        if pix_test_mode and not (is_cem or valor_total_sem_taxa <= 0):
            import uuid
            test_id = 'TESTE_' + str(uuid.uuid4())
            tickets_criados = []
            for i in range(quantidade):
                t = TicketModel.objects.create(
                    **{filter_key: user_obj}, 
                    valor=valor, 
                    valor_adicionais=valor_unitario_adicionais,
                    valor_taxa=valor_unitario_taxa,
                    detalhe_adicionais=adicionais_post,
                    tipo_refeicao=tipo,
                    pago=False,
                    data_pagamento=None,
                    id_pagamento_externo=test_id,
                    pix_copia_e_cola=f"00020101021226580014br.gov.bcb.pix0136{test_id}52040000530398654041.005802BR5915TESTE6009SAO PAULO62070503***63041234",
                    pix_qr_code_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
                )
                tickets_criados.append(t)
            
            primeiro_uuid = tickets_criados[0].uuid

            return JsonResponse({
                'status': 'pending',
                'ticket_uuid': str(primeiro_uuid),
                'pix_code': tickets_criados[0].pix_copia_e_cola,
                'pix_qr': tickets_criados[0].pix_qr_code_base64
            })

        # INTEGRAÇÃO REAL MERCADO PAGO
        try:
            mp_sdk = get_sdk()
            
            webhook_url = getattr(conf, 'webhook_url', None) or config('WEBHOOK_URL', default='')
            
            payment_data = {
                "transaction_amount": float(valor_com_taxa),
                "description": f"{quantidade}x Ticket {tipo} - Cantina IFTO",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"{user_obj.id_pessoa.usuario}@ifto.edu.br",
                    "first_name": user_obj.id_pessoa.nome.split()[0],
                    "last_name": user_obj.id_pessoa.nome.split()[-1] if len(user_obj.id_pessoa.nome.split()) > 1 else (user_type.capitalize()),
                }
            }
            
            if webhook_url.startswith('http'):
                payment_data["notification_url"] = webhook_url

            payment_response = mp_sdk.payment().create(payment_data)
            
            if payment_response.get("status") not in [200, 201]:
                return JsonResponse({
                    'error': 'Erro na API do Mercado Pago', 
                    'status_code': payment_response.get("status"),
                    'detail': payment_response.get("response")
                }, status=400)

            payment = payment_response["response"]

            if payment.get('status') == 'pending' or payment.get('status') == 'approved':
                tickets_criados = []
                for i in range(quantidade):
                    t = TicketModel.objects.create(
                        **{filter_key: user_obj}, 
                        valor=valor, 
                        valor_adicionais=valor_unitario_adicionais,
                        valor_taxa=valor_unitario_taxa,
                        detalhe_adicionais=adicionais_post,
                        tipo_refeicao=tipo,
                        pago=(payment.get('status') == 'approved'),
                        data_pagamento=timezone.now() if payment.get('status') == 'approved' else None,
                        id_pagamento_externo=str(payment.get('id')),
                        pix_copia_e_cola=payment['point_of_interaction']['transaction_data']['qr_code'],
                        pix_qr_code_base64=payment['point_of_interaction']['transaction_data']['qr_code_base64']
                    )
                    tickets_criados.append(t)
                
                primeiro_uuid = tickets_criados[0].uuid

                return JsonResponse({
                    'status': payment.get('status'),
                    'ticket_uuid': str(primeiro_uuid),
                    'pix_code': payment['point_of_interaction']['transaction_data']['qr_code'],
                    'pix_qr': payment['point_of_interaction']['transaction_data']['qr_code_base64']
                })
            else:
                return JsonResponse({'error': 'Status de pagamento inesperado', 'detail': payment}, status=400)
                
        except Exception as e:
            import traceback
            return JsonResponse({
                'error': 'Exceção interna ao processar pagamento',
                'exception': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    return redirect('ComprarTicket')

def StatusTicket(request, uuid):
    """ 
    Polling inteligente: verifica no banco local e, caso pendente, 
    faz uma consulta ativa na API do Mercado Pago (Plano B).
    """
    user_obj, user_type, error = get_user_profile(request)
    TicketModel = get_ticket_model(user_type)
    filter_key = 'id_servidor' if user_type == 'servidor' else 'id_aluno'
    ticket = TicketModel.objects.filter(uuid=uuid, **{filter_key: user_obj}).first()
    
    if not ticket:
        return JsonResponse({'error': 'Ticket não encontrado'}, status=404)
    
    # Se ainda estiver pendente no banco local, tentamos uma consulta ativa na API do MP
    if not ticket.pago and ticket.id_pagamento_externo:
        # CHECK MODO TESTE
        if ticket.id_pagamento_externo.startswith('TESTE_'):
            time_diff = (timezone.now() - ticket.data_compra).total_seconds()
            if time_diff >= 3:
                TicketModel.objects.filter(id_pagamento_externo=ticket.id_pagamento_externo).update(
                    pago=True,
                    data_pagamento=timezone.now()
                )
                ticket.pago = True
            return JsonResponse({'status': 'approved' if ticket.pago else 'pending'})

        try:
            mp_sdk = get_sdk()
            payment_info = mp_sdk.payment().get(ticket.id_pagamento_externo)
            
            if payment_info["status"] in [200, 201]:
                mp_status = payment_info["response"].get("status")
                if mp_status == 'approved':
                    TicketModel.objects.filter(id_pagamento_externo=ticket.id_pagamento_externo).update(
                        pago=True,
                        data_pagamento=timezone.now()
                    )
                    ticket.pago = True
        except Exception as e:
            # Se a consulta ativa falhar (ex: rede), apenas ignoramos e retornamos o status local
            pass
            
    return JsonResponse({
        'pago': ticket.pago,
        'usado': ticket.usado,
        'status_mp': 'approved' if ticket.pago else 'pending'
    })

@csrf_exempt
def WebhookPix(request):
    """ Callback do Mercado Pago para atualizar status do pagamento """
    mp_sdk = get_sdk()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get('type') == 'payment':
                id_pagamento = data.get('data', {}).get('id')
                
                payment_info = mp_sdk.payment().get(id_pagamento)
                status = payment_info["response"].get("status")
                
                if status == 'approved':
                    # Como o Webhook não tem sessão, tentamos atualizar em AMBAS as tabelas pelo ID externo
                    TicketAluno.objects.filter(id_pagamento_externo=id_pagamento).update(
                        pago=True,
                        data_pagamento=timezone.now()
                    )
                    TicketServidor.objects.filter(id_pagamento_externo=id_pagamento).update(
                        pago=True,
                        data_pagamento=timezone.now()
                    )
        except:
            pass
                    
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'method not allowed'}, status=405)

def VisualizarTicket(request, uuid):
    user_obj, user_type, error = get_user_profile(request)
    TicketModel = get_ticket_model(user_type)
    filter_key = 'id_servidor' if user_type == 'servidor' else 'id_aluno'
    ticket = TicketModel.objects.filter(uuid=uuid, **{filter_key: user_obj}).first()
    
    if not ticket or not ticket.pago:
        return redirect('TicketsEstudante')
    
    # Se já foi usado, verificar se ainda está no prazo dos 40 minutos
    if ticket.usado:
        from django.utils import timezone
        from datetime import timedelta
        limite = timezone.now() - timedelta(minutes=40)
        if ticket.data_utilizacao < limite:
            # Se passou de 40 minutos, não pode mais ver o ticket usado
            return redirect('TicketsEstudante')
        
        # Adiciona flag e tempo de expiração para o comprovante
        ticket.expira_em = (ticket.data_utilizacao + timedelta(minutes=40)).isoformat()

    # Processar adicionais para exibição
    adicionais_list = []
    if ticket.detalhe_adicionais:
        try:
            items = json.loads(ticket.detalhe_adicionais)
            for item in items:
                adicional_obj = Adicional.objects.filter(id=item['id']).first()
                if adicional_obj:
                    adicionais_list.append({
                        'nome': adicional_obj.nome,
                        'qtd': item['qtd'],
                        'valor_unit': adicional_obj.valor,
                        'total': float(adicional_obj.valor) * int(item['qtd'])
                    })
        except:
            pass
        
    ticket.valor_total_pago = float(ticket.valor) + float(ticket.valor_adicionais) + float(ticket.valor_taxa)
    
    return render(request, 'ticket_estudante/ver_ticket.html', {
        'title': 'Meu Ticket', 
        'itemselec': 'TICKETS', 
        'ticket': ticket,
        'adicionais_comprados': adicionais_list
    })

def RevisarPagamento(request, uuid):
    """ Tela para retomar o pagamento de um ticket pendente """
    user_obj, user_type, error = get_user_profile(request)
    TicketModel = get_ticket_model(user_type)
    filter_key = 'id_servidor' if user_type == 'servidor' else 'id_aluno'
    ticket = TicketModel.objects.filter(uuid=uuid, **{filter_key: user_obj}).first()
    
    if not ticket:
        return redirect('TicketsEstudante')
    
    # Se já foi pago, redireciona para ver o ticket
    if ticket.pago:
        return redirect('VisualizarTicket', uuid=ticket.uuid)
        
    return render(request, 'ticket_estudante/pagar_pendente.html', {
        'title': 'Concluir Pagamento',
        'itemselec': 'TICKETS',
        'ticket': ticket
    })
