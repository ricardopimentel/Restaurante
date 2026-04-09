from functools import wraps
from django.shortcuts import redirect, resolve_url as r
from django.contrib import messages

def permissao_requerida(item_id=None, category=None):
    """
    Decorator para verificar se o usuário tem permissão para acessar um item de menu específico
    ou qualquer item de uma categoria.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.session.get('nome'):
                return redirect(r('Login'))
            
            # Admins sempre têm acesso a tudo
            if request.session.get('is_admin'):
                return view_func(request, *args, **kwargs)
            
            allowed = request.session.get('allowed_items', [])
            
            # Se for especificado um ID de item
            if item_id and item_id in allowed:
                return view_func(request, *args, **kwargs)
                
            # Se categoria for especificada, verifica se tem acesso a QUALQUER item da categoria
            if category:
                if category == 'ADMINISTRAÇÃO':
                    admin_items = ['horario_vendas', 'bolsistas', 'colaboradores', 'cardapio_hub', 'config_ad', 'config_pix', 'permissoes', 'cardapio_dia', 'pratos_precos', 'opcoes_alimento', 'menu_relatorios']
                    if any(item in allowed for item in admin_items):
                        return view_func(request, *args, **kwargs)
                elif category == 'RELATÓRIOS':
                    if 'menu_relatorios' in allowed:
                        return view_func(request, *args, **kwargs)

            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect(r('Home'))
        return _wrapped_view
    return decorator
