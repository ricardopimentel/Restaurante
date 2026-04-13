import sys
from django.contrib import messages
from django.shortcuts import render, redirect, resolve_url as r
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from restaurante.administracao.models import config
from restaurante.core.libs.calendario import calendario
from restaurante.core.libs.conexaoAD3 import conexaoAD
from restaurante.core.models import pessoa, aluno, prato, usuariorestaurante, venda, alunoscem, alunoscolaboradores
import datetime
from django.utils import timezone
from restaurante.ticket_estudante.models import TicketAluno

from restaurante.venda.forms import ConfirmacaoVendaForm

# Eu sei que tenho que trocar isso
usuario = 'winbackup'
senha = 'v4c4pr3t4'

from restaurante.acesso.utils import permissao_requerida

# Views
@permissao_requerida(item_id='menu_vendas')
def Vendas(request):
    return render(request, 'venda/vendas.html', {
        'title': 'Vendas',
        'itemselec': 'VENDAS',
    })

@permissao_requerida(item_id='leitura_qr')
def ValidacaoQRCode(request):
    return render(request, 'venda/validar_qrcode.html', {
        'title': 'Validar QR Code',
        'itemselec': 'VENDAS',
    })

@permissao_requerida(item_id='vendas_manual')
def Venda(request):
    # Controle de Limpeza de Cache (Forçar Sincronização)
    if 'refresh' in request.GET:
        cache.delete('venda_lista_alunos_ad')
        messages.success(request, 'A lista de alunos foi sincronizada com o Active Directory.')
        return redirect('Venda')

    # Tenta buscar no cache
    ListaAlunos = cache.get('venda_lista_alunos_ad')
    
    if ListaAlunos is None:
        # tenta conectar ao banco de dados para pegar parametros do ldap
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

        if str(retorno) == 'i':
            messages.error(request, 'Falha ao realizar a consulta verifique o usuário "'+ usuario+'"')
        else:
            for lista in retorno:
                try:
                    if lista.get('raw_attributes'):
                        ListaAlunos.append({
                            'nome': (lista['raw_attributes']['displayName'][0]).decode('UTF-8'),
                            'cpf': (lista['raw_attributes']['sAMAccountName'][0]).decode('UTF-8'),
                        })
                except:
                    messages.error(request, str(sys.exc_info()[1]))
            
            # Só atualiza a memória se achou registros válidos, armazena por 1 Hora (3600 sec)
            if ListaAlunos:
                cache.set('venda_lista_alunos_ad', ListaAlunos, timeout=3600)

    return render(request, 'venda/venda.html', {
        'title': 'Venda',
        'itemselec': 'VENDAS',
        'step': 'pri',
        'alunos': ListaAlunos,
    })

@permissao_requerida(item_id='vendas_manual')
def VendaLotes(request):
    ListaAlunos = []
    con = conexaoAD(usuario, senha)
    if str(con.ListaAlunos()) == 'i':
        messages.error(request, 'Falha ao realizar a consulta verifique o usuário "' + usuario + '"')
    else:
        for lista in con.ListaAlunos():
            try:
                if lista.get('raw_attributes'):
                    ListaAlunos.append({
                        'nome': lista['raw_attributes']['displayName'][0],
                        'cpf': lista['raw_attributes']['sAMAccountName'][0],
                    })
            except:
                messages.error(request, str(sys.exc_info()[1]))

    return render(request, 'venda/venda_em_lotes.html', {
        'title': 'Venda',
        'itemselec': 'VENDAS',
        'step': 'pri',
        'alunos': ListaAlunos,
    })


@permissao_requerida(item_id='vendas_manual')
def VenderLotes(request, id_pessoa):
    if request.method == 'POST':
        messages.success(request, "Você quer vender")
    calendarobj = calendario()

    # Pega od dados necessarios para montar visão do calendario
    dadospagina = calendarobj.getCalendario()
    dadospagina['title'] = 'Venda'
    dadospagina['itemselec'] = 'VENDAS'
    dadospagina['step'] = 'seg'
    return render(request, 'venda/venda_em_lotes.html', dadospagina)


@csrf_exempt
@permissao_requerida(item_id='vendas_manual')
def Vender(request, id_pessoa):
    form = ConfirmacaoVendaForm(request, id_pessoa)
    if request.method == 'POST':
        form = ConfirmacaoVendaForm(request, id_pessoa, data=request.POST)
        if form.is_valid():
            id_aluno = request.POST['id_aluno']
            id_prato = ExistePratoCadastrado(id_pessoa).id
            restricoes = Restricoes(id_aluno, id_prato)
            if not restricoes['status']:
                vendaobj = SalvarVenda(request, id_aluno, id_prato, id_pessoa)
                if vendaobj:
                    messages.success(request, "Venda realizada com sucesso")
                return redirect(r('Venda'))
            else:
                messages.error(request, restricoes['erro'])
                return redirect(r('Venda'))

    data = datetime.datetime.now()
    pratoobj = ExistePratoCadastrado(id_pessoa)
    if pratoobj:
        aluno = ExisteAlunoCadastrado(id_pessoa)
        cem = VerificarUsuarioCem(id_pessoa)
        if not aluno:
            aluno = SalvaAluno(id_pessoa)

        return render(request, 'venda/venda.html', {
            'title': 'Venda',
            'itemselec': 'VENDAS',
            'step': 'fim',
            'dados': aluno,
            'data': data,
            'prato': pratoobj,
            'formulario': form,
            'cem': cem,
        })
    else:
        return render(request, 'venda/venda.html', {
            'title': 'Venda',
            'itemselec': 'VENDA',
            'step': 'notprato',
        })

# Métodos aplicados nas views
def SalvaAluno(cpf):
    # tenta conectar ao banco de dados para pegar parametros do ldap
    ou = ''
    filter = ''
    try:
        conf = config.objects.get(id=1)
        ou = conf.ou
        filter = conf.filter
    except:
        pass

    # Inicializa váriaveis
    con = conexaoAD(usuario, senha, ou, filter)
    nomealuno = (con.DadosAluno(cpf)[0]['raw_attributes']['displayName'][0]).decode('UTF-8')

    pessoaobj = pessoa(nome=nomealuno, usuario=cpf, status=True)
    pessoaobj.save()

    alunoobj = aluno(id_pessoa=pessoaobj)
    alunoobj.save()

    return {'pessoa': pessoaobj, 'aluno': alunoobj}


def ExistePratoCadastrado(id_pessoa):
    hora = datetime.datetime.now().hour
    id = False
    if VerificarUsuarioCem(id_pessoa):
        id = "Cem"
    else:
        if hora <= 14:
            id = "Almoço"
        else:
            id = "Janta"
    try:
        return prato.objects.get(descricao=id)
    except:
        return False


def ExisteAlunoCadastrado(id_pessoa):
    try:
        dados = aluno.objects.select_related('id_pessoa').get(id_pessoa__usuario=id_pessoa)
        return {'pessoa': dados.id_pessoa, 'aluno': dados}
    except:
        return False


def SalvarVenda(request, id_aluno, id_prato, id_pessoa):
    try:
        data = datetime.datetime.now()

        pratoobj = prato.objects.get(id=id_prato)
        usuariorestauranteobj = usuariorestaurante.objects.select_related('id_pessoa').get(id_pessoa__usuario=str(request.session['userl']))
        alunoobj = aluno.objects.get(id=id_aluno)

        cem = VerificarUsuarioCem(id_pessoa) #verifica se a bolsa é 100%
        #criar objeto da venda
        
        # Para alunos normais, registra o subsídio padrão. Se for CEM, soma o subsídio + a parte isentada do aluno
        valor_final = (pratoobj.preco + pratoobj.preco_aluno) if cem else pratoobj.preco

        if cem: #verifica se a bolsa é 100%
            vendaobj = venda(data=data, valor=valor_final, id_aluno=alunoobj, id_prato=pratoobj, id_usuario_restaurante=usuariorestauranteobj, cem=True)
        else:
            vendaobj = venda(data=data, valor=valor_final, id_aluno=alunoobj, id_prato=pratoobj, id_usuario_restaurante=usuariorestauranteobj)
        vendaobj.save()#salva venda

        return True
    except:
        messages.error(request, 'O usuário não tem permissão para realizar a venda. '+ str(sys.exc_info()[1]))
        return False


def VerificarUsuarioCem(id_pessoa):
    # Verificar se a bolsa é 100%
    try:
        cem = alunoscem.objects.select_related('id_pessoa').get(id_pessoa__usuario=id_pessoa)
        return True
    except:
        return False


def Restricoes(id_aluno, id_prato):#tem que trazer a instacia nova da venda e comparar com a instancia antiga, pra saber se foi o mesmo prato
    try:
        horafechamento = config.objects.get(id=1).hora_fechamento_vendas
        hoje = datetime.datetime.today()
        if hoje.time() < horafechamento:#verifica a hora do fechamento das vendas
            try:
                vendaobj = venda.objects.get(data__year=hoje.year, data__month=hoje.month, data__day=hoje.day, id_aluno=id_aluno)#tenta encontrar uma venda para o aluno especifico na data de hoje
            except venda.DoesNotExist:
                vendaobj = venda.objects.filter(data__year=hoje.year, data__month=hoje.month, data__day=hoje.day, id_aluno=id_aluno)#quando é a primeira venda do dia para esse aluno
            except:
                return {'status': True, 'erro': "Já existem duas vendas para esse aluno hoje"}
            if vendaobj:#verifica se a venda existe
                #verifica se o aluno é bolsista
                try:
                    alunoobj = aluno.objects.get(id=id_aluno)
                    alunocem = alunoscem.objects.get(id_pessoa=alunoobj.id_pessoa)
                except:
                    alunocem = False
                if alunocem:
                    return {'status': True, 'erro': "O aluno é bolsista e já realizou a compra hoje"}
                else:
                    #verifica se o aluno é colaborador
                    try:
                        alunoobj = aluno.objects.get(id=id_aluno)
                        alunocolaborador = alunoscolaboradores.objects.get(id_pessoa=alunoobj.id_pessoa)
                    except Exception as e:
                        alunocolaborador = False
                    if alunocolaborador:#valida se o aluno é colaborador
                        #verifica o prato
                        if vendaobj.id_prato == prato.objects.get(id=id_prato):# se o aluno é colaborador e a ultima venda realizada tem o mesmo prato do horário atual
                            return {'status': True, 'erro': "Aluno já realizou compra desse mesmo prato hoje"}
                    else:#se não é colaborador não pode repetir a venda
                        return {'status': True, 'erro': "Aluno já realizou compra hoje"}
            return {'status': False, 'erro': "Não há restrições"}
        else:
            return {'status': True, 'erro': "O horário das vendas está encerrado"}
    except Exception as e:
        return {'status': True, 'erro': "Falha ao verificar o horário de fechamento"}

@csrf_exempt
@permissao_requerida(item_id='leitura_qr')
def ValidarTicket(request):
    if request.method == 'POST':
        uuid_str = request.POST.get('uuid')
        ticket = TicketAluno.objects.filter(uuid=uuid_str).first()
        if not ticket:
            messages.error(request, "Ticket inválido ou não encontrado.")
            return redirect('ValidacaoQRCode')
        
        if ticket.usado:
            messages.error(request, "Ticket já foi utilizado!")
            return redirect('ValidacaoQRCode')
            
        prato_ativo = ExistePratoCadastrado(ticket.id_aluno.id_pessoa.usuario)
        if not prato_ativo:
            messages.error(request, "Não há prato ativo ou o horário não permite validar a venda.")
            return redirect('ValidacaoQRCode')
            
        # Validação de Tipo de Refeição e Valor
        # Se o tipo do ticket for diferente do prato atual E os valores forem diferentes, bloqueia
        if ticket.tipo_refeicao and ticket.tipo_refeicao != prato_ativo.descricao:
            if ticket.valor != prato_ativo.preco_aluno:
                messages.error(request, f"O ticket de {ticket.tipo_refeicao} (R$ {ticket.valor:.2f}) não pode ser usado nessa refeição de {prato_ativo.descricao} (R$ {prato_ativo.preco_aluno:.2f}).")
                return redirect('ValidacaoQRCode')
            
        restricoes = Restricoes(ticket.id_aluno.id, prato_ativo.id)
        if restricoes['status']:
            messages.error(request, restricoes['erro'])
            return redirect('ValidacaoQRCode')
            
        try:
            sucesso = SalvarVenda(request, ticket.id_aluno.id, prato_ativo.id, ticket.id_aluno.id_pessoa.usuario)
            if sucesso:
                ticket.usado = True
                ticket.data_utilizacao = timezone.now()
                ticket.tipo_refeicao = prato_ativo.descricao
                ticket.save()
                messages.success(request, f"Ticket de {ticket.id_aluno.id_pessoa.nome} validado com sucesso!")
            else:
                pass # SalvarVenda should have already added messages.error
        except Exception as e:
            messages.error(request, f"Falha ao validar: {str(e)}")
            
        return redirect('ValidacaoQRCode')
        
    return redirect('ValidacaoQRCode')