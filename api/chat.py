from http.server import BaseHTTPRequestHandler
import json
import requests
import os
import time

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Obter token das variáveis de ambiente (USE VARIÁVEL DE AMBIENTE NO VERCEL)
        API_TOKEN = os.environ.get('HUGGINGFACE_TOKEN')
        if not API_TOKEN:
            self.wfile.write(json.dumps({
                'error': 'Token não configurado no servidor'
            }).encode())
            return
        
        # Ler dados da requisição
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        user_message = data.get('message', '')
        
        # Modelo Qwen - VERIFIQUE DISPONIBILIDADE NA API
        model_name = "Qwen/Qwen3-Coder-480B-A35B-Instruct"
        API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
        
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        
        # Formato específico para o modelo Qwen
        messages = [
            {"role": "user", "content": user_message},
        ]
        
        payload = {
            "inputs": messages,
            "parameters": {
                "max_new_tokens": 100,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            # Fazer requisição com retry
            max_retries = 2
            for attempt in range(max_retries):
                response = requests.post(API_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    # Processar resposta baseado no formato do Qwen
                    if isinstance(result, list) and len(result) > 0:
                        if 'generated_text' in result[0]:
                            generated_text = result[0]['generated_text']
                        else:
                            # Tentar extrair texto de diferentes formatos de resposta
                            generated_text = str(result[0])
                    else:
                        generated_text = "Resposta em formato não esperado"
                    break
                    
                elif response.status_code == 503:
                    # Modelo carregando
                    wait_time = 10 * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                    
                else:
                    # Outro erro
                    error_msg = response.json().get('error', 'Erro desconhecido')
                    generated_text = f"Erro na API: {error_msg}"
                    break
            else:
                generated_text = "Modelo não disponível após várias tentativas"
            
            self.wfile.write(json.dumps({
                'response': generated_text
            }).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({
                'error': f"Erro interno: {str(e)}"
            }).encode())
