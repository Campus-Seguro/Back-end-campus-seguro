import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv
import uuid
from fastapi import UploadFile

# 1. Carrega as variáveis do arquivo .env para a memória do Python
load_dotenv()

# 2. Puxa as credenciais usando o os.getenv()
ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')
ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

# 3. Configura o cliente R2 com as variáveis seguras
s3_client = boto3.client(
    's3',
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

def gerar_link_seguro(caminho_arquivo: str):
    """Gera um link que se autodestrói em 1 hora"""
    url_temporaria = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': BUCKET_NAME, # Puxando do .env também
            'Key': caminho_arquivo
        },
        ExpiresIn=3600 # Tempo de vida do link em segundos (3600 = 1 hora)
    )
    print(url_temporaria)
    return url_temporaria


def deletar_arquivo_bucket(key: str):
    """Remove um arquivo do Cloudflare R2 caso o banco de dados falhe"""
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        print(f"Arquivo {key} removido do bucket após falha no banco.")
    except Exception as e:
        print(f"Erro crítico: Não foi possível remover {key} do bucket: {str(e)}")

def obter_tamanho_atual_bucket() -> int:
    """Soma o peso de todos os arquivos do bucket e retorna em bytes"""
    tamanho_total = 0
    # O Paginator lida automaticamente com buckets que têm milhares de arquivos
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for pagina in paginator.paginate(Bucket=BUCKET_NAME):
        if 'Contents' in pagina:
            for objeto in pagina['Contents']:
                tamanho_total += objeto['Size'] # Soma os bytes de cada arquivo

    print(f"Tamanho atual do bucket: {tamanho_total} bytes")                
    return tamanho_total


def fazer_upload_arquivo(arquivo: UploadFile) -> str:
    """Recebe um arquivo, checa o limite de 9GB, salva no R2 e retorna a Key"""
    
    # 1. Trava de Segurança: Calcular o tamanho atual do bucket
    LIMITE_BYTES = 9 * 1024 * 1024 * 1024 # 9 Gigabytes em Bytes
    tamanho_atual_bucket = obter_tamanho_atual_bucket()
    
    # 2. Descobrir o tamanho do arquivo que o usuário está tentando enviar
    arquivo.file.seek(0, 2) # Joga o "cursor" de leitura pro final do arquivo
    tamanho_novo_arquivo = arquivo.file.tell() # Vê em qual byte parou (peso do arquivo)
    arquivo.file.seek(0) # IMPORTANTE: Volta o cursor para o começo para o upload funcionar
    
    # 3. Verifica se a soma do que já tem + o que está chegando passa de 9GB
    if (tamanho_atual_bucket + tamanho_novo_arquivo) >= LIMITE_BYTES:
        # Se passar, nós abortamos a operação aqui mesmo, antes de gastar internet enviando
        raise ValueError("Capacidade máxima do sistema atingida (9GB). Não é possível enviar novos arquivos no momento.")

    # 4. Gerar nome seguro e fazer o upload (Seu código original continua aqui)
    extensao = arquivo.filename.split(".")[-1]
    nome_seguro = f"{uuid.uuid4()}.{extensao}" 

    s3_client.upload_fileobj(
        arquivo.file,       
        BUCKET_NAME,        
        nome_seguro,        
        ExtraArgs={
            "ContentType": arquivo.content_type 
        }
    )

    return nome_seguro