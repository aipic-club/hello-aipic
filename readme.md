
pipreqs . --encoding UTF-8



```
pip install --no-cache-dir --upgrade -r requirements.txt
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
