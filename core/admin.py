from django.contrib import admin
from .models import ConfiguracoesSistema, Material, Orcamento, MateriaisUtilizados, Cliente, Empresa

class MateriaisUtilizadosInline(admin.TabularInline):
    model = MateriaisUtilizados
    extra = 1

@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cliente', 'quantidade', 'tempo_por_unidade']
    inlines = [MateriaisUtilizadosInline]

admin.site.register(ConfiguracoesSistema)
admin.site.register(Material)
admin.site.register(Cliente)
admin.site.register(Empresa)
