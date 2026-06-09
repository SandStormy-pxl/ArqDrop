from django.contrib import admin
from django.urls import path, include
# Certifique-se de que o import está exatamente assim no topo do core/urls.py:
from gerenciador.views import painel_controle

urlpatterns = [
    # Painel de administração padrão do Django
    path('admin/', admin.site.config if hasattr(admin.site, 'config') else admin.site.urls),
    
    # Inclui todas as rotas de autenticação e CRUD do nosso app
    path('', include('gerenciador.urls')),
    path('painel/', painel_controle, name='painel_controle'), # Acesse via seudominio.com/painel/

]
