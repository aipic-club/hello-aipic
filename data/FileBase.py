from abc import abstractmethod
import copy

import boto3
import aiohttp
import io

class FileInterface:
    @abstractmethod
    def __init__(self, config : dict, proxy: str | None) -> None:
        pass

class FileBase(FileInterface):
    def __init__(self, config : dict, proxy: str | None) -> None:
        self.proxy = proxy
        self.bucket_name = None
        if 'aws_bucket_name' in config:
            self.bucket_name = config.pop('aws_bucket_name')

        self.s3client = boto3.client(
            's3', 
            **config
        )

    def file_generate_presigned_url(self, key):
 
        url = self.s3client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name, 
                'Key': key,
                'ContentType': '',
                'ContentLength': 5242880
            }
        ) 
        return url

    async def file_download_a_file(self, url: str) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            # Get the image from the URL as a binary stream
            async with session.get(url , proxy= self.proxy) as response:
                # Create a file-like object from the binary stream
                return await response.read()
                # in_mem_file = io.BytesIO(await response.read())
                # return in_mem_file

    async def upload_a_file(self, url: str, data: io.BytesIO, mime_type: str) :
        async with aiohttp.ClientSession() as session:

            async with session.put(
                url= url, 
                data= data, 
                proxy= self.proxy,
                headers= {
                    'Content-Type': mime_type
                }
            ) as response:
                return response.status




    async def file_copy_url_to_bucket(self, url: str, path: str, file_name: str ):
            # Get the image from the URL as a binary stream
            resp = await self.file_download_a_file(url)
            in_mem_file = io.BytesIO(resp)
            self.s3client.upload_fileobj(in_mem_file, self.bucket_name , f'{path}/{file_name}')
            # async with self.session.get(url , proxy= self.proxy) as response:
            #     # Create a file-like object from the binary stream
            #     in_mem_file = io.BytesIO(await response.read())
            #     # Upload the file-like object to S3
            #     self.s3client.upload_fileobj(in_mem_file, self.bucket_name , f'{path}/{file_name}')