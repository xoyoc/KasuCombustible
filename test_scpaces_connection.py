import boto3
from botocore.exceptions import ClientError
            
def test_connection(self):
        """Prueba la conexión a Spaces"""
        print("\n🔍 PROBANDO CONEXIÓN...")
        print("-" * 25)
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Configurar cliente S3 para Spaces
            session = boto3.session.Session()
            client = session.client(
                's3',
                region_name=self.config['region'],
                endpoint_url=self.config['endpoint'],
                aws_access_key_id=self.config['access_key'],
                aws_secret_access_key=self.config['secret_key']
            )
            
            # Probar listado del bucket
            response = client.head_bucket(Bucket=self.config['bucket_name'])
            print("✅ Conexión exitosa al bucket")
            
            # Probar subida de archivo de prueba
            test_key = 'test_connection.txt'
            client.put_object(
                Bucket=self.config['bucket_name'],
                Key=test_key,
                Body=b'Test de conexion desde Django',
                ACL='public-read'
            )
            
            # Eliminar archivo de prueba
            client.delete_object(Bucket=self.config['bucket_name'], Key=test_key)
            print("✅ Prueba de subida/eliminación exitosa")
            
            return True
            
        except ImportError:
            print("❌ boto3 no está instalado")
            print("   Instalar con: pip install boto3")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"❌ El bucket '{self.config['bucket_name']}' no existe")
                print("   Créalo en: https://cloud.digitalocean.com/spaces")
            elif error_code == 'InvalidAccessKeyId':
                print("❌ Access Key inválido")
            elif error_code == 'SignatureDoesNotMatch':
                print("❌ Secret Key inválido")
            else:
                print(f"❌ Error de conexión: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False