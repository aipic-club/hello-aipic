from abc import abstractmethod

import boto3
import aiohttp
import io

class FileInterface:
    @abstractmethod
    def __init__(self, config : dict, proxy: str | None) -> None:
        pass
    @abstractmethod
    def generate_presigned_url(self, content_type, key):
        pass

class FileBase(FileInterface):
    def __init__(self, config : dict, proxy: str | None) -> None:
        self.proxy = proxy
        self.bucket_name = 'cloudfront'
        self.s3client = boto3.client(
            's3', 
            **config
        )
    def file_generate_presigned_url(self, content_type, key):
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
    async def file_copy_url_to_bucket(self, url: str, path: str, file_name: str ):
        async with aiohttp.ClientSession() as session:
            # Get the image from the URL as a binary stream
            async with session.get(url , proxy= self.proxy) as response:
                # Create a file-like object from the binary stream
                in_mem_file = io.BytesIO(await response.read())
                # Upload the file-like object to S3
                self.s3client.upload_fileobj(in_mem_file, self.bucket_name , f'{path}/{file_name}')