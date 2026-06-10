from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Rotas de Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='gerenciador/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    
    # Rotas do CRUD
    path('', views.lista_arquivos, name='lista_arquivos'),
    path('editar/<int:arquivo_id>/', views.lista_arquivos, name='abrir_editor'),
    path('criar/', views.criar_arquivo, name='criar_arquivo'),
    path('salvar/<int:arquivo_id>/', views.salvar_arquivo, name='salvar_arquivo'),
    path('deletar/<int:arquivo_id>/', views.deletar_arquivo, name='deletar_arquivo'),
    path('upload/', views.upload_arquivo, name='upload_arquivo'),
    path('preview/<int:arquivo_id>/', views.visualizar_html, name='visualizar_html'),
    path('executar-codigo/', views.executar_codigo_view, name='executar_codigo'),


]
