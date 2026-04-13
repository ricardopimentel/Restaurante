import mercadopago
import json
from django.shortcuts import render, redirect, resolve_url as r
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decouple import config
from restaurante.administracao.models import config as config_model
from restaurante.core.models import prato, alunoscem, aluno
from restaurante.ticket_estudante.models import TicketAluno

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

def get_aluno(request):
    """ Busca o objeto Aluno baseado na sessão atual com log de debug """
    userl = request.session.get('userl')
    
    # Log temporário para debug de sessão
    try:
        with open('debug_session.log', 'a') as f:
            f.write(f"\n--- DEBUG {json.dumps(dict(request.session))} ---\n")
            f.write(f"Userl na sessão: {userl}\n")
    except:
        pass

    if not userl:
        return None, "Sessão expirada ou chave 'userl' não encontrada no request.session"
    
    try:
        aluno_inst = aluno.objects.get(id_pessoa__usuario=userl)
        return aluno_inst, None
    except aluno.DoesNotExist:
        return None, f"Aluno não encontrado no banco para o usuário: {userl}"
    except Exception as e:
        return None, f"Erro inesperado ao buscar aluno: {str(e)}"

def HomeEstudante(request):
    aluno_obj, error = get_aluno(request)
    if not aluno_obj:
        return redirect('Login')
    return redirect('Home')

def TicketsEstudante(request):
    aluno_obj, error = get_aluno(request)
    if not aluno_obj: return redirect('Login')
    
    from django.utils import timezone
    from datetime import timedelta
    limite_pendentes = timezone.now() - timedelta(hours=24)
    
    # Tickets Pagos
    tickets_pagos = TicketAluno.objects.filter(id_aluno=aluno_obj, usado=False, pago=True).order_by('-data_compra')
    
    # Tickets Pendentes (últimas 24h)
    tickets_pendentes = TicketAluno.objects.filter(
        id_aluno=aluno_obj, 
        pago=False, 
        data_compra__gte=limite_pendentes
    ).order_by('-data_compra')

    # Tickets Validados recentemente (últimos 40 minutos)
    limite_recentes = timezone.now() - timedelta(minutes=40)
    tickets_recentes = TicketAluno.objects.filter(
        id_aluno=aluno_obj, 
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
    aluno_obj, error = get_aluno(request)
    if not aluno_obj: return redirect('Login')
    
    almoco = prato.objects.filter(descricao="Almoço").first()
    janta = prato.objects.filter(descricao="Janta").first()
    
    if not almoco and not janta:
        return render(request, 'ticket_estudante/comprar.html', {
            'erro': 'Nenhum prato disponível no momento.',
            'itemselec': 'COMPRAR'
        })
    
    is_cem = alunoscem.objects.filter(id_pessoa=aluno_obj.id_pessoa).exists()
    
    context = {
        'title': 'Comprar Ticket',
        'itemselec': 'COMPRAR',
        'almoco': almoco,
        'janta': janta,
        'is_cem': is_cem,
        'pix_fee': getattr(get_config(), 'pix_fee', 0.0),
        'preco_almoco': 0.0 if is_cem else (almoco.preco_aluno if almoco else 0.0),
        'preco_janta': 0.0 if is_cem else (janta.preco_aluno if janta else 0.0),
    }
    return render(request, 'ticket_estudante/comprar.html', context)

@csrf_exempt
def SimularPagamento(request):
    """
    Agora renomeado logicamente para ProcessarPagamento. 
    Lida com a criação do PIX real via Mercado Pago.
    """
    aluno_obj, error = get_aluno(request)
    if not aluno_obj: 
        return JsonResponse({'error': 'Não autorizado', 'detail': error}, status=401)
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo_refeicao', 'Almoço')
        prato_selecionado = prato.objects.filter(descricao=tipo).first()
        
        if not prato_selecionado:
            return JsonResponse({'error': 'Prato não encontrado'}, status=404)

        is_cem = alunoscem.objects.filter(id_pessoa=aluno_obj.id_pessoa).exists()
        valor = 0.0 if is_cem else prato_selecionado.preco_aluno
        
        # BUSCA TAXA PIX (%)
        conf = get_config()
        pix_fee_percent = float(getattr(conf, 'pix_fee', 0.0))
        valor_com_taxa = float(valor) * (1 + (pix_fee_percent / 100)) if valor > 0 else 0.0

        # SE FOR CEM, CRIA O TICKET JÁ PAGO E RETORNA SUCESSO DIRETO
        if is_cem or valor <= 0:
            ticket = TicketAluno.objects.create(
                id_aluno=aluno_obj, 
                valor=0.0, 
                tipo_refeicao=tipo,
                pago=True,
                data_pagamento=timezone.now()
            )
            return JsonResponse({'status': 'approved', 'redirect': r('TicketsEstudante')})

        # INTEGRAÇÃO REAL MERCADO PAGO
        try:
            mp_sdk = get_sdk()
            
            webhook_url = getattr(conf, 'webhook_url', None) or config('WEBHOOK_URL', default='')
            
            payment_data = {
                "transaction_amount": float(valor_com_taxa),
                "description": f"Ticket {tipo} (+ Taxa PIX) - Cantina IFTO",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"{aluno_obj.id_pessoa.usuario}@ifto.edu.br",
                    "first_name": aluno_obj.id_pessoa.nome.split()[0],
                    "last_name": aluno_obj.id_pessoa.nome.split()[-1] if len(aluno_obj.id_pessoa.nome.split()) > 1 else "Aluno",
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
                ticket = TicketAluno.objects.create(
                    id_aluno=aluno_obj, 
                    valor=valor, 
                    tipo_refeicao=tipo,
                    pago=(payment.get('status') == 'approved'),
                    data_pagamento=timezone.now() if payment.get('status') == 'approved' else None,
                    id_pagamento_externo=str(payment.get('id')),
                    pix_copia_e_cola=payment['point_of_interaction']['transaction_data']['qr_code'],
                    pix_qr_code_base64=payment['point_of_interaction']['transaction_data']['qr_code_base64']
                )
                
                return JsonResponse({
                    'status': payment.get('status'),
                    'ticket_uuid': str(ticket.uuid),
                    'pix_code': ticket.pix_copia_e_cola,
                    'pix_qr': ticket.pix_qr_code_base64
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
    aluno_obj, error = get_aluno(request)
    ticket = TicketAluno.objects.filter(uuid=uuid, id_aluno=aluno_obj).first()
    
    if not ticket:
        return JsonResponse({'error': 'Ticket não encontrado'}, status=404)
    
    # Se ainda estiver pendente no banco local, tentamos uma consulta ativa na API do MP
    if not ticket.pago and ticket.id_pagamento_externo:
        try:
            mp_sdk = get_sdk()
            payment_info = mp_sdk.payment().get(ticket.id_pagamento_externo)
            
            if payment_info["status"] in [200, 201]:
                mp_status = payment_info["response"].get("status")
                if mp_status == 'approved':
                    ticket.pago = True
                    ticket.data_pagamento = timezone.now()
                    ticket.save()
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
                    ticket = TicketAluno.objects.filter(id_pagamento_externo=id_pagamento).first()
                    if ticket:
                        ticket.pago = True
                        ticket.data_pagamento = timezone.now()
                        ticket.save()
        except:
            pass
                    
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'method not allowed'}, status=405)

def VisualizarTicket(request, uuid):
    aluno_obj, error = get_aluno(request)
    ticket = TicketAluno.objects.filter(uuid=uuid, id_aluno=aluno_obj).first()
    
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
        
    return render(request, 'ticket_estudante/ver_ticket.html', {
        'title': 'Meu Ticket', 
        'itemselec': 'TICKETS', 
        'ticket': ticket
    })

def RevisarPagamento(request, uuid):
    """ Tela para retomar o pagamento de um ticket pendente """
    aluno_obj, error = get_aluno(request)
    ticket = TicketAluno.objects.filter(uuid=uuid, id_aluno=aluno_obj).first()
    
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
