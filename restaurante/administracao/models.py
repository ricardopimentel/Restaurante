from django.db import models

# Create your models here.
class config(models.Model):
    dominio = models.CharField(max_length=200)
    endservidor = models.CharField(max_length=200)
    gadmin = models.CharField(max_length=200)
    ou = models.CharField(max_length=200)
    filter = models.TextField('Filtro')
    hora_fechamento_vendas = models.TimeField('Horário do Fechamento das Vendas', default='23:59:59')
    mp_access_token = models.CharField('Mercado Pago Access Token', max_length=255, null=True, blank=True)
    webhook_url = models.CharField('Webhook URL', max_length=255, null=True, blank=True)

class MenuPermission(models.Model):
    TIPOS_ACESSO = (
        ('admin', 'Administrador'),
        ('lanchonete', 'Lanchonete'),
        ('aluno', 'Aluno'),
        ('glanchonete', 'Gerência Lanchonete'),
    )
    access_type = models.CharField('Tipo de Acesso', max_length=20, choices=TIPOS_ACESSO)
    ad_group = models.CharField('Grupo do AD', max_length=255, help_text="Nome do grupo no Active Directory")
    allowed_menus = models.TextField('Menus Permitidos', help_text="IDs dos menus permitidos separados por vírgula")
    
    # Novos campos para perfis de acesso dinâmicos
    DASHBOARD_CHOICES = (
        ('usuario', 'Dashboard Usuário (Estudante)'),
        ('funcionario', 'Dashboard Funcionário (Gestão/Vendas)'),
    )
    default_dashboard = models.CharField('Dashboard Padrão', max_length=20, choices=DASHBOARD_CHOICES, default='usuario')
    can_switch_dashboard = models.BooleanField('Pode trocar de Dashboard?', default=False)
    can_sell = models.BooleanField('Pode realizar venda?', default=False)
    group_label = models.CharField('Rótulo do Grupo', max_length=50, blank=True, help_text="Ex: Administrador, Vendedor, Coordenador")
    quick_access = models.TextField('Atalhos de Acesso Rápido', blank=True, help_text="IDs dos atalhos separados por vírgula (ex: vendas_manual, validacao_qr, cardapio_dia, relatorios)")

    class Meta:
        verbose_name = 'Permissão de Menu'
        verbose_name_plural = 'Permissões de Menu'
        unique_together = ('access_type', 'ad_group')

    def __str__(self):
        return f"{self.get_access_type_display()} - {self.ad_group}"

    def get_allowed_list(self):
        return [x.strip() for x in self.allowed_menus.split(',') if x.strip()]

    def get_quick_list(self):
        if not self.quick_access: return []
        return [x.strip() for x in self.quick_access.split(',') if x.strip()]