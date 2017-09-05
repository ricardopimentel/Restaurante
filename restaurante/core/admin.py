from django.contrib import admin

# Register your models here.
from restaurante.core.models import prato, usuariorestaurante, aluno, administrador

admin.site.register(prato)
admin.site.register(usuariorestaurante)
admin.site.register(aluno)
admin.site.register(administrador)