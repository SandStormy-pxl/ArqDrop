from django.db import models
from django.contrib.auth.models import User

class Arquivo(models.Model):
    # Vincula o arquivo diretamente a um usuário do Django
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arquivos')
    nome_do_arquivo = models.CharField(max_length=255)
    conteudo_do_arquivo = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_do_arquivo} | {self.autor.username}"
