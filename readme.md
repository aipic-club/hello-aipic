requirements
```
pip install fastapi
pip install "uvicorn[standard]"
pip install pillow
pip install "redis[hiredis]"
pip install pyyaml
pip install websockets
```




```
celery.exe -A bot worker -l info -c 1
celery -A bot worker -l info --pool=solo 
celery.exe flower --address=127.0.0.1 --port=5566
``` 
#### start mock server
```
    uvicorn mock-server:app --reload
```


https://beautifulsoup.readthedocs.io/zh_CN/v4.4.0/
