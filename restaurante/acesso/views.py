import sys
from django.shortcuts import render, redirect, resolve_url as r
from django.core.exceptions import ObjectDoesNotExist


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
            pess = None
            try:
                pess = pessoa.objects.get(usuario=request.session['userl'])
            except ObjectDoesNotExist:
                # Pessoa não cadastrada - Fazer cadastro inicial
                pess = pessoa(nome=request.session['nome'], usuario=request.session['userl'], status=True)
                pess.save()
            
            # Uma vez que a Pessoa existe, garantimos os perfis configurados
            usertip = request.session.get('usertip')
            access_types = request.session.get('access_types', [])
            
            if usertip == 'admin' or 'admin' in access_types:
                from restaurante.core.models import administrador
                administrador.objects.get_or_create(id_pessoa=pess)
            
            if usertip == 'lanchonete' or 'lanchonete' in access_types:
                from restaurante.core.models import usuariorestaurante
                usuariorestaurante.objects.get_or_create(id_pessoa=pess)
                
            if usertip == 'servidor' or 'servidor' in access_types:
                from restaurante.core.models import servidor
                servidor.objects.get_or_create(id_pessoa=pess, defaults={'status': True})
                
            if usertip == 'aluno' or 'aluno' in access_types:
                from restaurante.core.models import aluno
                aluno.objects.get_or_create(id_pessoa=pess)
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
    request.session.flush()
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


def TrocarPerfil(request, perfil_type):
    if not request.session.get('nome'):
        return redirect(r('Login'))
        
    available_profiles = request.session.get('available_profiles', [])
    perfil_data = next((p for p in available_profiles if p['type'] == perfil_type), None)
    
    if perfil_data:
        from restaurante.administracao.models import MenuPermission
        from restaurante.core.models import pessoa, administrador, usuariorestaurante, servidor, aluno
        
        try:
            p_base = pessoa.objects.get(usuario=request.session['userl'])
            
            # Garantir que o perfil exista no banco de dados
            if perfil_type == 'admin':
                administrador.objects.get_or_create(id_pessoa=p_base)
            elif perfil_type == 'servidor':
                servidor.objects.get_or_create(id_pessoa=p_base, defaults={'status': True})
            elif perfil_type == 'aluno':
                aluno.objects.get_or_create(id_pessoa=p_base)
            elif perfil_type == 'lanchonete':
                usuariorestaurante.objects.get_or_create(id_pessoa=p_base)
        except Exception as e:
            print(f"Erro ao garantir perfil no banco: {e}")

        # 1. Atualizar Identidade Básica na Sessão
        request.session['usertip'] = perfil_data['type']
        request.session['group_label'] = perfil_data['label']
        
        # 2. Recarregar Permissões Específicas do Perfil Selecionado
        is_global_admin = request.session.get('is_admin', False)
        
        allowed_items = []
        can_switch = is_global_admin
        can_sell = is_global_admin
        
        p_obj = MenuPermission.objects.filter(access_type=perfil_type).first()
        if p_obj:
            allowed_items = p_obj.get_allowed_list()
            if p_obj.can_switch_dashboard: can_switch = True
            if p_obj.can_sell: can_sell = True
            
        if perfil_type == 'admin':
            admin_defaults = [
                'menu_vendas', 'menu_relatorios', 'horario_vendas', 'bolsistas', 
                'colaboradores', 'cardapio_hub', 'config_ad', 'config_pix', 
                'permissoes', 'cardapio_dia', 'pratos_precos', 'opcoes_alimento'
            ]
            allowed_items = list(set(allowed_items + admin_defaults))
            can_switch = True
            can_sell = True

        request.session['allowed_items'] = allowed_items
        request.session['can_switch'] = can_switch
        request.session['can_sell'] = can_sell
        
        # 3. Ajustar Modo do Dashboard
        if perfil_type in ['aluno', 'servidor']:
             request.session['dashboard_mode'] = 'usuario'
        else:
             request.session['dashboard_mode'] = 'funcionario'
             
        from restaurante.acesso.forms import RebuildMenu
        RebuildMenu(request)
        
        from django.contrib import messages
        messages.success(request, f"Perfil alterado para: {perfil_data['label']}")
        
    return redirect(r('Home'))