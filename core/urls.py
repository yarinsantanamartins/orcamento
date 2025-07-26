from django.urls import path
from . import views

from django.conf import settings          # <--- IMPORTAR settings aqui
from django.conf.urls.static import static

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('parametros/', views.parametros_sistema, name='parametros_sistema'),
    path('parametros-sistema/', views.parametros_sistema, name='parametros_sistema'),
    path('orcamentos/novo/', views.novo_orcamento, name='novo_orcamento'),
    path('resultado/<int:pk>/', views.resultado_orcamento, name='resultado_orcamento'),
    path('orcamentos/', views.lista_orcamentos, name='lista_orcamentos'),
    path('orcamento/<int:pk>/gerar/', views.gerar_orcamento_html, name='gerar_orcamento_html'),
    path('clientes/novo/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('produtos/cadastrar/', views.cadastrar_produto, name='cadastrar_produto'),
    path('orcamento/<int:pk>/editar/', views.editar_orcamento, name='editar_orcamento'),
    path('orcamento/<int:pk>/excluir/', views.excluir_orcamento, name='excluir_orcamento'),
    path('orcamento/<int:pk>/detalhes-preco/', views.detalhes_preco, name='detalhes_preco'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
