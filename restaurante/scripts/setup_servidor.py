import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante.settings')
django.setup()

from restaurante.administracao.models import MenuPermission

def create_server_group():
    group, created = MenuPermission.objects.get_or_create(
        ad_group='G_PSO_CGTI_SERVIDORES',
        defaults={
            'access_type': 'aluno', # Usando aluno como base de dashboard de usuário
            'allowed_menus': 'menu_home, user_info',
            'default_dashboard': 'usuario',
            'can_switch_dashboard': False,
            'can_sell': False,
            'group_label': 'Servidor'
        }
    )
    if created:
        print("Grupo Servidor criado com sucesso!")
    else:
        print("Grupo Servidor já existia.")

if __name__ == "__main__":
    create_server_group()
