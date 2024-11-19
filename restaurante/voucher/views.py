from django.shortcuts import render, redirect, resolve_url as r
from django.contrib import messages
from restaurante.voucher.forms import GeraLiberacaoForm, CadastroVouchersForm
from restaurante.voucher.models import voucher


# Create your views here.
def GeraLiberacao(request):
    #Tenta pegar o primeiro voucher encontrado
    voucher_obj = voucher.objects.filter(usado=False).first()
    #Verifica se ele não é vazio
    if voucher_obj == None:
        messages.error(request, "Não Existe Voucher Cadastrado")
        # Caso não encontre um voucher, redireciona para o cadastro
        return redirect(r('CadastroVouchers'))
    else:
        #Se encontrar o voucher, passa ele como escolhido no formulário
        form = GeraLiberacaoForm(initial={'id_voucher': voucher_obj})
    #Testa forulario
    if request.method == 'POST':
        form = GeraLiberacaoForm(data=request.POST)
        if form.is_valid():
            #Altera o voucher para usado
            voucher_obj.usado = True
            voucher_obj.save()
            #salva formulário se os dados forem válidos
            form.save()
            #http://40.0.0.1:8002/index.php?zone=wifi&auth_voucher=+voucher_obj.codigo
            return redirect('http://40.0.0.1:8002/index.php?zone=wifi&auth_voucher='+voucher_obj.codigo)
    return render(request, 'voucher/voucher_cadastro_liberacao.html', {
        'title': 'Voucher',
        'form': form,
    })


def CadastroVouchers(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'): # Verifica permissão de gerente ou admin
            menu = 'CONFIGURAÇÃO'
            if (dict(request.session).get('usertip') == 'admin'):
                menu = 'ADMINISTRAÇÃO'
            ListaErros = []
            ListaAcertos = []
            form = CadastroVouchersForm()
            if request.method == 'POST':#se vier pelo post
                form = CadastroVouchersForm(data=request.POST)
                if form.is_valid():#se o formulário foi válido, ou seja todos os campos obrigatórios preecnhidos
                    vouchers = form.cleaned_data['vouchers']
                    ListaVouchersDigitados = list(map(str, vouchers.split('\n'))) #Transforma todos os cpfs digitados no campo usuários em uma lista
                    # Percorre a lista de vouchers
                    for voucher_code in ListaVouchersDigitados:
                        try:
                            voucher_obj = voucher(codigo=voucher_code)
                            voucher_obj.save()
                            ListaAcertos.append("O Voucher: " + voucher_code + " Foi adicionado com sucesso!")
                        except:
                            ListaErros.append("O Voucher: " + voucher_code + " Não foi adicionado")

                    return render(request, 'voucher/voucher_cadastro_vouchers.html', {
                        'title': 'Cadastro de Vouchers',
                        'ListaErros': ListaErros,
                        'ListaAcertos': ListaAcertos,
                        'itemselec': menu,
                        'form': CadastroVouchersForm(),
                    })
            return render(request, 'voucher/voucher_cadastro_vouchers.html', {
                'title': 'Cadastro de Vouchers',
                'itemselec': menu,
                'form': form,
            })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))


def ExcluirVouchers(request):
    if dict(request.session).get('nome'):# verifica se o usurário está logado
        if (dict(request.session).get('usertip') == 'glanchonete')or(dict(request.session).get('usertip') == 'admin'):  # Verifica permissão de gerente ou admin
            menu = 'CONFIGURAÇÃO'
            if (dict(request.session).get('usertip') == 'admin'):
                menu = 'ADMINISTRAÇÃO'
            vouchers_objs = voucher.objects.filter(usado=False)
            if request.method == 'POST':
                check = False
                for voucher_obj in vouchers_objs:
                    if request.POST.get(str(voucher_obj.codigo)):
                        check = True
                        try:
                            voucher_obj.delete()
                            messages.success(request, 'Voucher '+ str(voucher_obj.codigo)+ ' excluído')
                        except:
                            messages.error(request, 'Erro ao exluir voucher '+ str(voucher_obj.codigo))
                if not check:
                    messages.error(request, 'Selecione pelo menos 1 voucher para excluir')
                return redirect(r('ExcluirVouchers'))
            else:
                return render(request, 'voucher/voucher_conferir_cadastro_vouchers.html', {
                    'title': 'Lista Vouchers',
                    'itemselec': menu,
                    'vouchers': vouchers_objs,
                })
        else:
            messages.error(request, "Você não tem permissão para acessar esta página, redirecionando para HOME")
            return redirect(r('Home'))
    else:
        return redirect(r('Login'))