import sys
from django.shortcuts import render, redirect, resolve_url as r


# Create your views here.
from restaurante.acesso.forms import LoginForm
from restaurante.administracao.models import config
from restaurante.core.models import pessoa, administrador


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
                return redirect(r('Home'))
        else:  # Se os dados não são válidos, mostra tela de login com os erros destacados
            return render('login.html', {'form': form, 'err': '', 'itemselec': 'HOME', }, request)
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

    except KeyError:
        print(sys.exc_info())
    return redirect(r("Login"))