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


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import sys
import io

@csrf_exempt
def executar_codigo_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            codigo = data.get('codigo', '')
            respostas = data.get('respostas', []) 
            
            iterador_respostas = iter(respostas)
            
            def input_simulado(prompt=""):
                try:
                    return next(iterador_respostas)
                except StopIteration:
                    raise EOFError("Entrada de dados não fornecida pelo usuário.")

            # Função segura para substituir o exit() e evitar travamentos
            def exit_simulado(*args, **kwargs):
                print("Sessão finalizada pelo comando exit().")
                return

            stdout_antigo = sys.stdout
            sys.stdout = buffer_saida = io.StringIO()
            
            # Monta o ambiente isolado
            ambiente_execucao = {
                '__builtins__': __builtins__.copy(),
            }
            # Sobrescreve as funções nativas de entrada e saída do console
            ambiente_execucao['__builtins__']['input'] = input_simulado
            ambiente_execucao['__builtins__']['exit'] = exit_simulado
            ambiente_execucao['__builtins__']['quit'] = exit_simulado
            
            erro = None
            try:
                exec(codigo, ambiente_execucao)
            except Exception as e:
                erro = str(e)
                
            sys.stdout = stdout_antigo
            saida_terminal = buffer_saida.getvalue()
            
            return JsonResponse({
                'saida': saida_terminal,
                'erro': erro
            })
        except Exception as e:
            return JsonResponse({'saida': '', 'erro': f'Erro interno no servidor: {str(e)}'})





import sys
import subprocess
from io import StringIO
from django.shortcuts import render

def painel_controle(request):
    # Pega o modo atual que veio do formulário. Se não vier nada, o padrão é bash
    modo = request.POST.get('modo_atual', 'bash')
    resultado = ""
    comando_anterior = ""

    if request.method == "POST":
        comando = request.POST.get("comando", "").strip()
        comando_anterior = comando

        # --- TRANSIÇÃO DE ESTADOS ---
        if modo == 'bash' and comando == 'python':
            modo = 'python'
            resultado = "Python 3.12 (Django Context)\nPressione ENTER duas vezes seguidas para rodar.\nDigite 'exit()' para voltar ao Bash."
        
        elif modo == 'python' and comando == 'exit()':
            modo = 'bash'
            resultado = "Voltou para o modo Bash Shell."
        
        # --- EXECUÇÃO ---
        else:
            if modo == 'bash':
                try:
                    execucao = subprocess.run(
                        comando, shell=True, capture_output=True, text=True, timeout=10
                    )
                    resultado = execucao.stdout + execucao.stderr
                except Exception as e:
                    resultado = f"Erro Bash: {str(e)}"
            
            elif modo == 'python':
                antigo_stdout = sys.stdout
                resultado_string = StringIO()
                sys.stdout = resultado_string
                
                try:
                    exec(comando, globals())
                    resultado = resultado_string.getvalue()
                except Exception as e:
                    resultado = f"Erro Python:\n{str(e)}"
                finally:
                    sys.stdout = antigo_stdout

    contexto = {
        "resultado": resultado,
        "comando_anterior": comando_anterior,
        "modo": modo,
    }
    return render(request, "gerenciador/painel.html", contexto)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess

@csrf_exempt
def executar_bash_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comando = data.get('comando', '')
            
            # Executa o comando no sistema operacional
            # shell=True permite comandos do bash como 'ls', 'pwd', 'echo'
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5 # Evita que comandos travados travem o servidor
            )
            
            # Se o comando falhar no bash, pegamos o stderr (erro do sistema)
            if resultado.returncode != 0:
                return JsonResponse({
                    'saida': '',
                    'erro': resultado.stderr or f"Comando falhou com código {resultado.returncode}"
                })
            
            # Se der certo, devolvemos a saída padrão (stdout)
            return JsonResponse({
                'saida': resultado.stdout,
                'erro': None
            })
            
        except subprocess.TimeoutExpired:
            return JsonResponse({'saida': '', 'erro': 'O comando demorou muito para responder (Timeout).'})
        except Exception as e:
            return JsonResponse({'saida': '', 'erro': f'Erro interno no servidor: {str(e)}'})

