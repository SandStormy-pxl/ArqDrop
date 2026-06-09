from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Painel de administração padrão do Django
    path('admin/', admin.site.config if hasattr(admin.site, 'config') else admin.site.urls),
    
    # Inclui todas as rotas de autenticação e CRUD do nosso app
    path('', include('gerenciador.urls')),
]
