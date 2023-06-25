
import boto3
import aiohttp
import io

class FileHandler:
    def __init__(self, proxy: str | None, s3config : dict) -> None:
        self.proxy = proxy
        self.bucket_name = 'cloudfront'
        self.s3client = boto3.client(
            's3', 
            aws_access_key_id = s3config['aws_access_key_id'], 
            aws_secret_access_key = s3config['aws_secret_access_key'],
            endpoint_url=s3config['endpoint_url'],
        )
    def generate_presigned_url(self, content_type, key):

        url = self.s3client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name, 
                'Key': key,
                'ContentType': content_type,
                'ContentLength': 5242880
            }
        )
        return url
    
    async def copy_discord_img_to_bucket(self,  path: str | None, file_name: str | None,  url: str):
        _file_name = str(url.split("_")[-1]) if not file_name else file_name
        async with aiohttp.ClientSession() as session:
            # Get the image from the URL as a binary stream
            async with session.get(url , proxy= self.proxy) as response:
                # Create a file-like object from the binary stream
                in_mem_file = io.BytesIO(await response.read())
                # Upload the file-like object to S3
                self.s3client.upload_fileobj(in_mem_file, self.bucket_name , f'{path}/{_file_name}')
    async def download_img_to_cache():
        pass