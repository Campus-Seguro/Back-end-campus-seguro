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

def fazer_upload_arquivo(arquivo: UploadFile) -> str:
    """Recebe um arquivo do FastAPI, salva no R2 e retorna a Key"""
    
    # 1. Gerar um nome único e seguro para o arquivo
    # Pegamos a extensão original (ex: .mp4, .jpg)
    extensao = arquivo.filename.split(".")[-1]
    
    # Criamos um nome com UUID para evitar que um arquivo sobrescreva outro com o mesmo nome
    nome_seguro = f"{uuid.uuid4()}.{extensao}" 

    # 2. Fazer o upload para o Cloudflare R2
    s3_client.upload_fileobj(
        arquivo.file,       # Os dados do arquivo em si
        BUCKET_NAME,        # O nome do bucket (puxado do .env)
        nome_seguro,        # O novo nome que criamos
        ExtraArgs={
            # Diz para o navegador que tipo de arquivo é (importante para vídeos tocarem)
            "ContentType": arquivo.content_type 
        }
    )

    # 3. Retornar a Key gerada para o FastAPI poder salvar no banco de dados
    return nome_seguro