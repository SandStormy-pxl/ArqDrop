from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Arquivo

@login_required
def lista_arquivos(request, arquivo_id=None):
    arquivos = Arquivo.objects.filter(autor=request.user).order_by('-id')
    arquivo_editando = None
    if arquivo_id:
        arquivo_editando = get_object_or_404(Arquivo, id=arquivo_id, autor=request.user)
        
    return render(request, 'gerenciador/index.html', {
        'arquivos': arquivos,
        'arquivo_editando': arquivo_editando
    })

@login_required
def criar_arquivo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_do_arquivo', '').strip()
        if nome:
            extensoes_validas = ('.txt', '.py', '.html', '.json')
            if not nome.lower().endswith(extensoes_validas):
                nome += '.txt'
                
            Arquivo.objects.create(
                autor=request.user,
                nome_do_arquivo=nome,
                conteudo_do_arquivo="Escreva o conteúdo aqui..."
            )
    return redirect('lista_arquivos')

@login_required
def salvar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(Arquivo, id=arquivo_id, autor=request.user)
    if request.method == 'POST':
        arquivo.conteudo_do_arquivo = request.POST.get('conteudo_do_arquivo')
        arquivo.save()
    return redirect('lista_arquivos')

@login_required
def deletar_arquivo(request, arquivo_id):
    arquivo = get_object_or_404(Arquivo, id=arquivo_id, autor=request.user)
    arquivo.delete()
    return redirect('lista_arquivos')

@login_required
def upload_arquivo(request):
    if request.method == 'POST' and request.FILES.get('arquivo_fisico'):
        arquivo_enviado = request.FILES['arquivo_fisico']
        nome = arquivo_enviado.name
        
        extensoes_validas = ('.txt', '.py', '.html', '.json')
        if not nome.lower().endswith(extensoes_validas):
            messages.error(request, 'Formato não suportado! Use .txt, .py, .html ou .json.')
            return redirect('lista_arquivos')
            
        try:
            conteudo = arquivo_enviado.read().decode('utf-8')
        except UnicodeDecodeError:
            messages.error(request, 'Erro ao ler o arquivo. Certifique-se de que é texto puro.')
            return redirect('lista_arquivos')

        Arquivo.objects.create(
            autor=request.user,
            nome_do_arquivo=nome,
            conteudo_do_arquivo=conteudo
        )
        messages.success(request, f'"{nome}" carregado com sucesso!')
        
    return redirect('lista_arquivos')

def cadastro(request):
    if request.user.is_authenticated:
        return redirect('lista_arquivos')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
        
    return render(request, 'gerenciador/cadastro.html', {'form': form})



from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Arquivo

def visualizar_html(request, arquivo_id):
    # Busca o arquivo pelo ID de forma pública (sem filtrar por usuário)
    arquivo = get_object_or_404(Arquivo, id=arquivo_id)
    
    # Retorna o conteúdo informando ao navegador que é um HTML real
    return HttpResponse(arquivo.conteudo_do_arquivo, content_type="text/html")


import sys
import subprocess
from io import StringIO
from django.shortcuts import render

def painel_controle(request):
    resultado = ""
    comando_anterior = ""
    tipo_anterior = ""

    if request.method == "POST":
        # Verifica qual formulário foi enviado
        if "comando_bash" in request.POST:
            comando = request.POST.get("comando_bash", "")
            comando_anterior = comando
            tipo_anterior = "Bash"
            try:
                # Executa o comando Bash no ambiente Linux da Vercel
                execucao = subprocess.run(
                    comando, shell=True, capture_output=True, text=True, timeout=10
                )
                resultado = execucao.stdout + execucao.stderr
            except Exception as e:
                resultado = f"Erro ao executar Bash: {str(e)}"

        elif "codigo_python" in request.POST:
            codigo = request.POST.get("codigo_python", "")
            comando_anterior = codigo
            tipo_anterior = "Python"
            
            # Redireciona a saída do print() para uma variável
            antigo_stdout = sys.stdout
            resultado_string = StringIO()
            sys.stdout = resultado_string
            
            try:
                # Executa o código Python no contexto do Django
                exec(codigo, globals())
                resultado = resultado_string.getvalue()
            except Exception as e:
                resultado = f"Erro no script Python:\n{str(e)}"
            finally:
                # Restaura a saída padrão do sistema
                sys.stdout = antigo_stdout

    contexto = {
        "resultado": resultado,
        "comando_anterior": comando_anterior,
        "tipo_anterior": tipo_anterior,
    }
    return render(request, "gerenciador/painel.html", contexto)
