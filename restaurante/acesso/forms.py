from django import forms
from restaurante.administracao.models import config
from restaurante.core.libs.conexaoAD3 import conexaoAD
from django.shortcuts import resolve_url as r

class LoginForm(forms.Form):
    usuario = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Login'}))
    senha = forms.CharField(label="", widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        ou = ''
        filter = ''
        try:
            conf = config.objects.get(id=1)
            ou = conf.ou
            filter = conf.filter
        except:
            pass
        
        cleaned_data = self.cleaned_data
        usuario = cleaned_data.get("usuario")
        senha = cleaned_data.get("senha")
        
        if usuario and senha:
            c = conexaoAD(usuario, senha, ou, filter)
            result = c.Login()

            if(result == ('i')):
                raise forms.ValidationError("Usuário ou senha incorretos", code='invalid')
            elif(result == ('n')):
                raise forms.ValidationError("Servidor AD não encontrado", code='invalid')
            elif(result == ('o')):
                raise forms.ValidationError("Usuário não tem permissão para acessar essa página", code='invalid')
            else:
                result['memberOf'] = str(result['memberOf']).replace(',', '')
                ret = repr(result)
                ret = ret.replace('[', '').replace(']', '')
                MontarMenu(self.request, ret, usuario)
        return cleaned_data


def MontarMenu(request, ret, usuario):
    result = eval(ret)
    from restaurante.administracao.models import MenuPermission
    
    # 1. Identificar se é Administrador do Sistema (Acesso Total)
    is_admin = (ret.find(str('G_PSO_CGTI_SERVIDORES')) > -1)
    
    # 2. Buscar Perfis de Acesso configurados no BD para os grupos do usuário
    matching_profiles = []
    all_profiles = MenuPermission.objects.all()
    for profile in all_profiles:
        if ret.find(str(profile.ad_group)) > -1:
            matching_profiles.append(profile)
    
    # Validação de Acesso Estrito: Se não for Admin e não tiver perfil no BD, bloqueia
    if not is_admin and not matching_profiles:
        from django import forms
        raise forms.ValidationError("Seu grupo do AD não possui um perfil de acesso configurado. Contate o administrador.", code='unauthorized')

    allowed_items = []
    quick_access = []
    can_switch = False
    can_sell = False
    default_dashboard = 'usuario'
    group_label = ''
    
    # Se houver múltiplos perfis, pegamos as permissões mais amplas
    # Priorizamos perfis de tipo Admin na ordenação
    matching_profiles.sort(key=lambda p: (p.access_type == 'admin', p.access_type == 'glanchonete'), reverse=True)
    
    # Determinar Rótulo (Label) do cargo - Prioridade absoluta para perfis Admin
    # Se for Admin Global (is_admin), já começamos com "Administrador"
    if is_admin:
        group_label = 'Administrador'

    for p in matching_profiles:
        allowed_items.extend(p.get_allowed_list())
        if p.quick_access:
            quick_access.extend([x.strip() for x in p.quick_access.split(',')])
        if p.can_switch_dashboard: can_switch = True
        if p.can_sell: can_sell = True
        if p.default_dashboard == 'funcionario': default_dashboard = 'funcionario'
        
        # O rótulo é pego do perfil de maior prioridade. 
        # Se for um perfil Admin, ele sobrescreve o label genérico de is_admin ou qualquer outro.
        if p.group_label:
            if p.access_type == 'admin':
                group_label = p.group_label
            elif not group_label:
                group_label = p.group_label
    
    # Se ainda for admin e não tiver rótulo nenhum (caso raro)
    if is_admin and not group_label:
        group_label = 'Administrador'

    # Fallback/Segurança para Admins (mesmo que o DB seja limpo ou falhe)
    if is_admin:
        can_switch = True
        can_sell = True
        default_dashboard = 'funcionario'
        # Adiciona atalhos de admin se não estiverem no DB (redundância)
        admin_defaults = [
            'menu_vendas', 'menu_relatorios', 'horario_vendas', 'bolsistas', 
            'colaboradores', 'cardapio_hub', 'config_ad', 'config_pix', 
            'permissoes', 'cardapio_dia', 'pratos_precos', 'opcoes_alimento'
        ]
        allowed_items.extend(admin_defaults)
        quick_defaults = ['shortcut_vendas', 'shortcut_qr', 'shortcut_cardapio', 'shortcut_relatorios']
        quick_access.extend(quick_defaults)

    allowed_items = list(set(allowed_items))
    quick_access = list(set(quick_access))

    # 4. Salvar dados básicos na Sessão
    request.session['is_admin'] = is_admin
    request.session['userl'] = usuario
    request.session['nome'] = result['displayName'].title()
    request.session['dashboard_mode'] = default_dashboard
    request.session['can_switch'] = can_switch
    request.session['can_sell'] = can_sell
    request.session['quick_access_items'] = quick_access
    request.session['allowed_items'] = allowed_items
    request.session['group_label'] = group_label
    
    # Compatibilidade com código legado (usertip)
    if is_admin: request.session['usertip'] = 'admin'
    elif default_dashboard == 'funcionario': request.session['usertip'] = 'lanchonete'
    else: request.session['usertip'] = 'aluno'

    try:
        request.session['mail'] = result['mail']
    except KeyError:
        request.session['mail'] = 'Não informado'
    try:
        request.session['phone'] = result['telephoneNumber']
    except KeyError:
        request.session['phone'] = 'Não informado'

    RebuildMenu(request)


def RebuildMenu(request):
    dashboard_mode = request.session.get('dashboard_mode', 'usuario')
    allowed = request.session.get('allowed_items', [])
    is_admin = request.session.get('is_admin', False)

    if dashboard_mode == 'funcionario':
        menu = ['logo', 'HOME']
        urls = [r('Home'), r('Home')]
        imgs = ['if.png', 'home24.png']
        
        # VENDAS: can_sell flag ou IDs manuais
        vendas_items = ['menu_vendas', 'vendas_manual', 'leitura_qr']
        if request.session.get('can_sell') or any(item in allowed for item in vendas_items):
            menu.append('VENDAS')
            urls.append(r('Vendas'))
            imgs.append('dinheiro24b.png')
            
        # RELATÓRIOS
        rel_items = ['menu_relatorios', 'relatorio_vendas', 'custo_aluno_periodo']
        if any(item in allowed for item in rel_items):
            menu.append('RELATÓRIOS')
            urls.append(r('Relatorios'))
            imgs.append('relatorio24.png')
            
        # ADMINISTRAÇÃO: Qualquer item da categoria admin
        admin_items = ['horario_vendas', 'bolsistas', 'colaboradores', 'cardapio_hub', 'config_ad', 'config_pix', 'permissoes', 'cardapio_dia', 'pratos_precos', 'opcoes_alimento']
        if any(item in allowed for item in admin_items):
            menu.append('ADMINISTRAÇÃO')
            urls.append(r('Administracao'))
            imgs.append('admin24.png')
            
        menu.append('sair')
        urls.append('')
        imgs.append('')
        
        # Ajuste de prefixo de URL para o projeto
        urls = [u.replace('/restaurante/', 'restaurante/') if u else '' for u in urls]
        
        request.session['menu'] = menu
        request.session['url'] = urls
        request.session['img'] = imgs
    else:
        # Dashboard de Estudante
        request.session['menu'] = ['logo', 'HOME', 'TICKETS', 'COMPRAR', 'sair']
        urls = [r('Home'), r('Home'), r('TicketsEstudante'), r('ComprarTicket'), '']
        request.session['url'] = [u.replace('/restaurante/', 'restaurante/') if u else '' for u in urls]
        request.session['img'] = ['if.png', 'home24.png', 'ticket.png', 'dinheiro24b.png', '']
