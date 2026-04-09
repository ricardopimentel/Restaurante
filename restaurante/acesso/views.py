import sys
from django.shortcuts import render, redirect, resolve_url as r


# Create your views here.
from restaurante.acesso.forms import LoginForm
from restaurante.administracao.models import config
from restaurante.core.models import pessoa, administrador, usuariorestaurante, aluno


def Login(request):
    try:
        conf = config.objects.get(id=1)
        dominio = conf.dominio
    except:
        return redirect(r('ConfigInicial'))

    # Se vier algo pelo post significa que houve requisição
    if request.method == 'POST':
        # Cria uma instancia do formulario com os dados vindos do request POST:
        form = LoginForm(request, data=request.POST)
        # Checa se os dados são válidos:
        if form.is_valid():
            # Logou no ad, verificar se está salvo no banco de dados
            try:
                pess = pessoa.objects.get(usuario=request.session['userl'])
                if pess:  # Pessoa Cadastrada
                    # Pessoa cadastrada, abrir página inicial
                    return redirect(r('Home'))
            except:
                # Pessoa não cadastrada - Fazer cadastro
                pessoaobj = pessoa(nome=request.session['nome'], usuario=request.session['userl'], status=True)
                pessoaobj.save()
                # Verificar tipo de usuário
                if (request.session['usertip'] == 'admin'):  # Cadastrar Admin
                    adminobj = administrador(id_pessoa=pessoaobj)
                    adminobj.save()
                elif (request.session['usertip'] == 'lanchonete'):  # Usuário da lanchonete
                    lanchoneteobj = usuariorestaurante(id_pessoa=pessoaobj)
                    lanchoneteobj.save()
                elif (request.session['usertip'] == 'aluno'):  # Estudante
                    from restaurante.core.models import aluno
                    alunoobj = aluno(id_pessoa=pessoaobj)
                    alunoobj.save()
                return redirect(r('Home'))
        else:
            # Capturar erros de validação (como senha incorreta ou usuário fora do escopo)
            error_message = ""
            if form.errors:
                # Pega o primeiro erro encontrado (geralmente non_field_errors do clean)
                error_list = form.non_field_errors()
                if error_list:
                    error_message = error_list[0]
                else:
                    # Se não houver non_field_errors, tenta listar o primeiro erro de algum campo
                    for field, errors in form.errors.items():
                        error_message = f"{field.capitalize()}: {errors[0]}"
                        break
            
            return render(request, 'acesso/login.html', {
                'form': form, 
                'err': error_message, 
                'itemselec': 'HOME', 
            })
    else:  # se não veio nada no post cria uma instancia vazia
        # Criar instancia vazia do formulario de login
        request.session['menu'] = ['HOME']
        request.session['url'] = ['restaurante/']
        request.session['img'] = ['home24.png']
        form = LoginForm(request)
        return render(request, 'acesso/login.html', {
            'title': 'Home',
            'itemselec': 'HOME',
            'form': form,
        })


def Logout(request):
    try:
        del request.session['nome']
        del request.session['mail']
        del request.session['curso']
        del request.session['userl']
        del request.session['menu']
        del request.session['url']
        del request.session['phone']

    except KeyError:
        print(sys.exc_info())
    return redirect(r("Login"))


def TrocarDashboard(request):
    if not request.session.get('nome'):
        return redirect(r('Login'))
    
    is_admin = request.session.get('is_admin', False)
    can_switch = request.session.get('can_switch', False)
    
    if is_admin or can_switch:
        current_mode = request.session.get('dashboard_mode', 'usuario')
        new_mode = 'funcionario' if current_mode == 'usuario' else 'usuario'
        request.session['dashboard_mode'] = new_mode
        
        # Reconstruir o menu para o novo modo
        from restaurante.acesso.forms import RebuildMenu
        RebuildMenu(request)
        
        from django.contrib import messages
        messages.success(request, f"Dashboard alterado para visão de {new_mode.capitalize()}.")
        
    return redirect(r('Home'))