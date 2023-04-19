requirements
```
pip install fastapi
pip install "uvicorn[standard]"
pip install pillow
pip install "redis[hiredis]"
pip install pyyaml
pip install websocket-client
pip install websocket-client[optional]
pip install mysql-connector-python
pip install boto3
```




```
celery.exe -A bot-main worker -l info -c 1
celery -A bot-main worker -l info --pool=solo 
celery.exe flower --address=127.0.0.1 --port=5566
``` 
#### start mock server
```
    uvicorn mock-server:app --host 0.0.0.0 --reload
```


https://beautifulsoup.readthedocs.io/zh_CN/v4.4.0/
